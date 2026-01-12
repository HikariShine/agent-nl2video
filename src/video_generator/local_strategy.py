"""本地视频生成策略（使用轻量级模型）"""
import os
import time
from typing import Optional
from ..script_generator.models import Script
from .strategy import VideoGenerationStrategy
from .models import VideoResult
import sys
import os as os_module
sys.path.insert(0, os_module.path.join(os_module.path.dirname(__file__), '../..'))
from config.settings import settings


class LocalVideoStrategy(VideoGenerationStrategy):
    """本地视频生成策略（使用MoviePy + 图片生成）"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.storage_path = config.get("storage_path", settings.videos_path)
        self.use_ai_images = config.get("use_ai_images", False)  # 是否使用AI生成图片
    
    async def generate(self, script: Script, output_path: Optional[str] = None) -> VideoResult:
        """
        使用本地方法生成视频
        
        Args:
            script: 剧本对象
            output_path: 输出路径
            
        Returns:
            视频生成结果
        """
        start_time = time.time()
        video_id = f"local_{int(time.time())}"
        
        try:
            if output_path is None:
                output_path = os.path.join(self.storage_path, f"{video_id}.mp4")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 使用MoviePy生成视频（与Sora策略类似，但不依赖API）
            video_result = await self._generate_with_moviepy(script, output_path, video_id)
            
            generation_time = int(time.time() - start_time)
            video_result.generation_time = generation_time
            video_result.generation_strategy = "local_moviepy"
            
            return video_result
            
        except Exception as e:
            generation_time = int(time.time() - start_time)
            return VideoResult(
                video_id=video_id,
                file_path="",
                status="failed",
                generation_strategy="local",
                generation_time=generation_time,
                error_message=str(e),
            )
    
    async def _generate_with_moviepy(self, script: Script, output_path: str, video_id: str) -> VideoResult:
        """使用MoviePy生成视频"""
        try:
            from moviepy.editor import ColorClip, CompositeVideoClip, ImageClip
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            import tempfile
            
            # 创建视频片段
            colors = [
                (100, 150, 200),  # 蓝色
                (150, 100, 200),  # 紫色
                (200, 150, 100),  # 橙色
                (100, 200, 150),  # 绿色
                (200, 100, 150),  # 粉色
                (150, 200, 100),  # 黄绿色
            ]
            
            video_clips = []
            subtitle_clips = []
            current_time = 0
            
            # 为每个场景创建视频片段和字幕
            for i, scene in enumerate(script.scenes):
                color = colors[i % len(colors)]
                
                # 创建背景视频片段
                bg_clip = ColorClip(
                    size=(1920, 1080),
                    color=color,
                    duration=scene.duration
                )
                video_clips.append(bg_clip.set_start(current_time))
                
                # 创建字幕
                if scene.subtitles:
                    try:
                        # 创建字幕图片
                        img = Image.new('RGBA', (1920, 300), (0, 0, 0, 180))
                        draw = ImageDraw.Draw(img)
                        
                        # 使用中文字体（按优先级尝试）
                        font_size = 60
                        font = None
                        chinese_fonts = [
                            "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
                            "/System/Library/Fonts/STHeiti Light.ttc",  # macOS 黑体
                            "/System/Library/Fonts/Hiragino Sans GB.ttc",  # macOS 冬青黑体
                            "/Library/Fonts/Arial Unicode.ttf",  # Arial Unicode
                            "/System/Library/Fonts/Supplemental/Songti.ttc",  # 宋体
                            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
                            "C:/Windows/Fonts/msyh.ttc",  # Windows 微软雅黑
                            "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
                        ]
                        
                        for font_path in chinese_fonts:
                            try:
                                font = ImageFont.truetype(font_path, font_size)
                                break
                            except:
                                continue
                        
                        if font is None:
                            font = ImageFont.load_default()
                        
                        # 计算文字位置（居中）
                        bbox = draw.textbbox((0, 0), scene.subtitles, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        x = (1920 - text_width) // 2
                        y = (300 - text_height) // 2
                        
                        # 绘制文字（带描边效果）
                        for adj in [(-3, -3), (-3, 3), (3, -3), (3, 3), (-3, 0), (3, 0), (0, -3), (0, 3)]:
                            draw.text((x + adj[0], y + adj[1]), scene.subtitles, 
                                    font=font, fill=(0, 0, 0, 255))
                        draw.text((x, y), scene.subtitles, font=font, fill=(255, 255, 255, 255))
                        
                        # 保存为临时文件
                        temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        img.save(temp_img.name)
                        temp_img.close()
                        
                        # 创建字幕视频片段
                        subtitle_img = ImageClip(temp_img.name, duration=scene.duration)
                        subtitle_img = subtitle_img.set_position(('center', 1080 - 300 - 50)).set_start(current_time)
                        subtitle_clips.append(subtitle_img)
                        
                        # 清理临时文件
                        os.unlink(temp_img.name)
                    except Exception as e:
                        print(f"   警告: 场景 {i+1} 字幕生成失败: {e}")
                
                current_time += scene.duration
            
            # 合成视频
            if len(video_clips) > 1:
                video = CompositeVideoClip(video_clips + subtitle_clips, size=(1920, 1080))
            else:
                video = CompositeVideoClip(
                    (video_clips[0] if video_clips else ColorClip(size=(1920, 1080), color=(100, 100, 200), duration=script.duration),) + tuple(subtitle_clips),
                    size=(1920, 1080)
                )
            
            # 添加背景音乐
            try:
                from moviepy.audio.AudioClip import AudioArrayClip
                sample_rate = 44100
                duration_samples = int(script.duration * sample_rate)
                t = np.linspace(0, script.duration, duration_samples)
                audio_array = (
                    np.sin(2 * np.pi * 440 * t) * 0.2 * (1 - t / script.duration) +
                    np.sin(2 * np.pi * 440 * 1.5 * t) * 0.1 * (1 - t / script.duration)
                ).astype(np.float32)
                audio_clip = AudioArrayClip(audio_array.reshape((len(audio_array), 1)), fps=sample_rate)
                video = video.set_audio(audio_clip)
                print(f"   已添加背景音乐")
            except Exception as e:
                print(f"   警告: 背景音乐生成失败: {e}")
            
            # 写入文件
            video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac' if video.audio else None,
                verbose=False,
                logger=None,
                preset='ultrafast'
            )
            
            file_size = os.path.getsize(output_path)
            print(f"✅ 本地视频生成成功（{file_size}字节）")
            
            return VideoResult(
                video_id=video_id,
                file_path=output_path,
                file_size=file_size,
                duration=script.duration,
                resolution="1080p",
                format="mp4",
                status="completed",
            )
            
        except ImportError:
            raise Exception("MoviePy未安装，请运行: pip install moviepy")
        except Exception as e:
            raise Exception(f"视频生成失败: {e}")
    
    def get_capabilities(self) -> dict:
        """获取策略能力"""
        return {
            "max_duration": 300,  # 5分钟
            "supported_resolutions": ["720p", "1080p"],
            "supported_formats": ["mp4"],
            "requires_api_key": False,  # 不需要API密钥
            "requires_gpu": False,  # 不需要GPU
        }
    
    def validate_config(self) -> bool:
        """验证配置"""
        # 本地策略总是可用（只要MoviePy安装）
        try:
            import moviepy
            return True
        except ImportError:
            return False

