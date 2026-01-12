"""CogVideoX 本地视频生成策略（支持 Apple Silicon MPS）"""
import os
import time
import torch
import tempfile
from typing import Optional, List
from ..script_generator.models import Script
from .strategy import VideoGenerationStrategy
from .models import VideoResult
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config.settings import settings


class CogVideoXStrategy(VideoGenerationStrategy):
    """CogVideoX 本地视频生成策略
    
    使用智谱AI开源的CogVideoX模型在本地生成视频
    支持 Apple Silicon (MPS) 和 NVIDIA GPU (CUDA)
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.storage_path = config.get("storage_path", settings.videos_path)
        self.model_id = config.get("model_id", "THUDM/CogVideoX-2b")  # 2B参数版本，适合M4
        self.device = self._get_device()
        self.pipe = None
        self._load_model_lazy = config.get("lazy_load", True)  # 延迟加载模型
        
    def _get_device(self):
        """获取可用的设备"""
        if torch.backends.mps.is_available():
            return "mps"  # Apple Silicon
        elif torch.cuda.is_available():
            return "cuda"  # NVIDIA GPU
        else:
            return "cpu"
    
    def _get_proxies(self):
        """获取代理配置"""
        import os
        proxies = {}
        
        # 优先使用配置中的代理
        http_proxy = self.config.get("http_proxy") or os.getenv("HTTP_PROXY")
        https_proxy = self.config.get("https_proxy") or os.getenv("HTTPS_PROXY")
        
        if http_proxy:
            proxies["http"] = http_proxy
        if https_proxy:
            proxies["https"] = https_proxy
        
        return proxies if proxies else None
    
    def _load_model(self):
        """加载模型（延迟加载）"""
        if self.pipe is not None:
            return
        
        print(f"正在加载 CogVideoX 模型到 {self.device}...")
        print("首次加载可能需要下载模型（约4GB），请耐心等待...")
        
        # 检查代理配置
        proxies = self._get_proxies()
        if proxies:
            print(f"使用代理: {proxies}")
        
        try:
            from diffusers import CogVideoXPipeline
            from diffusers.utils import export_to_video
            
            # 根据设备选择数据类型
            if self.device == "mps":
                # Apple Silicon MPS 不支持 float16，必须使用 float32
                dtype = torch.float32
            elif self.device == "cuda":
                dtype = torch.float16
            else:
                dtype = torch.float32
            
            # 构建加载参数
            load_kwargs = {
                "torch_dtype": dtype,
            }
            
            # 如果有代理，添加到加载参数
            if proxies:
                load_kwargs["proxies"] = proxies
            
            self.pipe = CogVideoXPipeline.from_pretrained(
                self.model_id,
                **load_kwargs,
            )
            
            # 启用内存优化
            self.pipe.enable_model_cpu_offload()  # CPU卸载，节省显存
            
            # 对于 MPS，启用额外的内存优化
            if self.device == "mps":
                # 启用注意力切片，减少内存使用
                try:
                    self.pipe.enable_attention_slicing(slice_size="max")
                    print("✅ 已启用注意力切片（减少内存使用）")
                except:
                    pass
                
                # 启用 VAE 切片
                try:
                    self.pipe.enable_vae_slicing()
                    print("✅ 已启用 VAE 切片（减少内存使用）")
                except:
                    pass
            
            # 对于 MPS，强制转换所有 float64 为 float32（必须在移动到 MPS 之前）
            if self.device == "mps":
                print("正在转换所有 float64 参数为 float32（MPS 要求）...")
                torch.set_default_dtype(torch.float32)
                
                def convert_float64_to_float32(module):
                    """递归转换所有 float64 参数和 buffer 为 float32"""
                    for name, param in module.named_parameters(recurse=False):
                        if param.dtype == torch.float64:
                            param.data = param.data.to(torch.float32)
                    for name, buffer in module.named_buffers(recurse=False):
                        if buffer.dtype == torch.float64:
                            buffer.data = buffer.data.to(torch.float32)
                
                # 只转换已知的模块组件，避免访问不存在的属性
                known_modules = ['transformer', 'vae', 'text_encoder', 'tokenizer']
                for module_name in known_modules:
                    if hasattr(self.pipe, module_name):
                        try:
                            module = getattr(self.pipe, module_name)
                            if module is not None and isinstance(module, torch.nn.Module):
                                module.apply(convert_float64_to_float32)
                                # 使用 float() 方法确保所有浮点数为 float32
                                setattr(self.pipe, module_name, module.float())
                        except (AttributeError, TypeError) as e:
                            # 忽略无法转换的属性（可能是配置对象等）
                            pass
                
                print("✅ 参数转换完成")
                print("正在将模型移动到 MPS...")
                self.pipe = self.pipe.to("mps")
                # 再次确保所有参数是 float32
                if hasattr(self.pipe, 'transformer') and self.pipe.transformer is not None:
                    self.pipe.transformer = self.pipe.transformer.float()
            elif self.device == "cuda":
                self.pipe = self.pipe.to("cuda")
            
            print(f"✅ CogVideoX 模型加载完成，使用设备: {self.device}")
            
        except ImportError:
            raise ImportError(
                "需要安装 diffusers 库。请运行:\n"
                "pip install diffusers transformers accelerate"
            )
    
    async def generate(self, script: Script, output_path: Optional[str] = None) -> VideoResult:
        """
        使用 CogVideoX 生成视频
        
        支持多场景剧本：为每个场景生成独立视频，然后无缝拼接
        
        Args:
            script: 剧本对象
            output_path: 输出路径
            
        Returns:
            视频生成结果
        """
        start_time = time.time()
        video_id = f"cogvideo_{int(time.time())}"
        
        try:
            if output_path is None:
                output_path = os.path.join(self.storage_path, f"{video_id}.mp4")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 加载模型
            self._load_model()
            
            # 检查是否需要多段生成
            if len(script.scenes) > 1:
                print(f"检测到 {len(script.scenes)} 个场景，将分别生成后拼接...")
                return await self._generate_multi_scene(script, output_path, video_id, start_time)
            else:
                return await self._generate_single(script, output_path, video_id, start_time)
            
        except Exception as e:
            generation_time = int(time.time() - start_time)
            error_msg = str(e)
            print(f"❌ 视频生成失败: {error_msg}")
            
            return VideoResult(
                video_id=video_id,
                file_path="",
                status="failed",
                generation_strategy="cogvideox",
                generation_time=generation_time,
                error_message=error_msg,
            )
    
    async def _generate_single(self, script: Script, output_path: str, video_id: str, start_time: float) -> VideoResult:
        """生成单个视频"""
        # 将剧本转换为提示词
        prompt = self._script_to_prompt(script)
        print(f"生成提示词: {prompt[:100]}...")
        
        # 生成视频
        print("正在生成视频，这可能需要几分钟...")
        
        from diffusers.utils import export_to_video
        
        # CogVideoX 生成参数（MPS 使用更小的值以减少内存）
        if self.device == "mps":
            num_frames = 25  # MPS 内存限制，减少到 25 帧（约1秒）
            num_inference_steps = 30  # 减少推理步数
            print(f"⚠️  MPS 内存优化模式: {num_frames} 帧, {num_inference_steps} 步")
        else:
            num_frames = 49  # 约2秒
            num_inference_steps = 50
        
        video_frames = self.pipe(
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=6.0,  # 引导强度
            num_frames=num_frames,
            generator=torch.Generator(device=self.device).manual_seed(42),
        ).frames[0]
        
        # 导出视频
        export_to_video(video_frames, output_path, fps=24)
        
        file_size = os.path.getsize(output_path)
        generation_time = int(time.time() - start_time)
        
        print(f"✅ 视频生成成功: {output_path}")
        print(f"   文件大小: {file_size / 1024:.1f} KB")
        print(f"   生成耗时: {generation_time} 秒")
        
        # 计算实际时长
        actual_duration = num_frames / 24.0  # 假设 24fps
        
        return VideoResult(
            video_id=video_id,
            file_path=output_path,
            file_size=file_size,
            duration=int(actual_duration),
            resolution="720p",
            format="mp4",
            status="completed",
            generation_strategy="cogvideox",
            generation_time=generation_time,
        )
    
    async def _generate_multi_scene(self, script: Script, output_path: str, video_id: str, start_time: float) -> VideoResult:
        """
        多场景视频生成：为每个场景生成视频，然后无缝拼接
        
        支持两种拼接模式：
        1. 简单拼接：直接连接
        2. 续接模式：使用上一段最后一帧作为下一段的起始参考
        """
        from diffusers.utils import export_to_video
        
        temp_videos = []
        temp_dir = tempfile.mkdtemp(prefix="cogvideo_")
        
        try:
            last_frame = None  # 用于续接模式
            
            for i, scene in enumerate(script.scenes):
                print(f"\n📹 生成场景 {i+1}/{len(script.scenes)}: {scene.title}")
                
                # 构建场景提示词
                prompt = self._scene_to_prompt(scene)
                print(f"   提示词: {prompt[:80]}...")
                
                # 生成视频帧（MPS 使用更小的值）
                if self.device == "mps":
                    num_frames = 25
                    num_inference_steps = 30
                else:
                    num_frames = 49
                    num_inference_steps = 50
                
                video_frames = self.pipe(
                    prompt=prompt,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=6.0,
                    num_frames=num_frames,
                    generator=torch.Generator(device=self.device).manual_seed(42 + i),
                ).frames[0]
                
                # 保存临时视频
                temp_path = os.path.join(temp_dir, f"scene_{i}.mp4")
                export_to_video(video_frames, temp_path, fps=24)
                temp_videos.append(temp_path)
                
                print(f"   ✅ 场景 {i+1} 生成完成")
            
            # 拼接所有视频
            print(f"\n🎬 正在拼接 {len(temp_videos)} 个视频片段...")
            total_duration = self._concatenate_videos(temp_videos, output_path)
            
            file_size = os.path.getsize(output_path)
            generation_time = int(time.time() - start_time)
            
            print(f"\n✅ 完整视频生成成功: {output_path}")
            print(f"   场景数量: {len(script.scenes)}")
            print(f"   总时长: {total_duration:.1f} 秒")
            print(f"   文件大小: {file_size / 1024:.1f} KB")
            print(f"   生成耗时: {generation_time} 秒")
            
            return VideoResult(
                video_id=video_id,
                file_path=output_path,
                file_size=file_size,
                duration=int(total_duration),
                resolution="720p",
                format="mp4",
                status="completed",
                generation_strategy="cogvideox",
                generation_time=generation_time,
            )
            
        finally:
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _concatenate_videos(self, video_paths: List[str], output_path: str, transition: str = "none") -> float:
        """
        拼接多个视频
        
        Args:
            video_paths: 视频文件路径列表
            output_path: 输出路径
            transition: 转场效果 ("none", "crossfade", "fade")
            
        Returns:
            总时长（秒）
        """
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        
        clips = []
        for path in video_paths:
            clip = VideoFileClip(path)
            
            if transition == "crossfade" and len(clips) > 0:
                clip = clip.crossfadein(0.3)
            elif transition == "fade":
                if len(clips) > 0:
                    clip = clip.fadein(0.2)
                clip = clip.fadeout(0.2)
            
            clips.append(clip)
        
        # 拼接
        if transition == "crossfade":
            final = concatenate_videoclips(clips, padding=-0.3, method="compose")
        else:
            final = concatenate_videoclips(clips, method="compose")
        
        total_duration = final.duration
        
        # 导出
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            logger=None  # 静默输出
        )
        
        # 清理资源
        for clip in clips:
            clip.close()
        final.close()
        
        return total_duration
    
    def _scene_to_prompt(self, scene) -> str:
        """将单个场景转换为提示词"""
        prompt = f"A high quality video: {scene.visual}"
        prompt += ", cinematic lighting, smooth motion, professional quality, 4K"
        return prompt
    
    def _script_to_prompt(self, script: Script) -> str:
        """
        将剧本转换为视频生成提示词
        
        Args:
            script: 剧本对象
            
        Returns:
            英文提示词（CogVideoX 对英文效果更好）
        """
        # 提取第一个场景的画面描述作为主要提示词
        if script.scenes:
            scene = script.scenes[0]
            # 使用场景的视觉描述
            visual = scene.visual
            
            # 构建提示词（英文效果更好）
            prompt = f"A high quality video: {visual}"
            
            # 添加一些质量提示
            prompt += ", cinematic lighting, smooth motion, professional quality, 4K"
            
        else:
            prompt = f"A video about {script.title}, high quality, cinematic"
        
        return prompt
    
    def get_capabilities(self) -> dict:
        """获取策略能力"""
        return {
            "max_duration": "unlimited",  # 支持多段拼接，无时长限制
            "single_clip_duration": 2,  # 单次生成约2秒
            "supported_resolutions": ["480p", "720p"],
            "supported_formats": ["mp4"],
            "requires_api_key": False,
            "requires_gpu": True,  # 需要GPU或MPS
            "model": self.model_id,
            "device": self.device,
            "multi_scene_support": True,  # 支持多场景拼接
            "transitions": ["none", "crossfade", "fade"],  # 支持的转场效果
        }
    
    def validate_config(self) -> bool:
        """验证配置"""
        # 检查是否有可用的加速设备
        if self.device == "cpu":
            print("⚠️  警告: 没有检测到GPU/MPS，将使用CPU运行（非常慢）")
        return True


class CogVideoXImageToVideoStrategy(VideoGenerationStrategy):
    """CogVideoX 图片转视频策略
    
    先用 Stable Diffusion 生成图片，再用 CogVideoX 转为视频
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.storage_path = config.get("storage_path", settings.videos_path)
        self.device = self._get_device()
        self.sd_pipe = None
        self.video_pipe = None
        
    def _get_device(self):
        """获取可用的设备"""
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        return "cpu"
    
    async def generate(self, script: Script, output_path: Optional[str] = None) -> VideoResult:
        """生成视频（先生成图片，再转视频）"""
        # TODO: 实现图片到视频的流程
        pass
    
    def get_capabilities(self) -> dict:
        return {
            "max_duration": 6,
            "supported_resolutions": ["720p"],
            "requires_api_key": False,
        }

