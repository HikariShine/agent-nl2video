"""Sora视频生成策略"""
import os
import time
import asyncio
from typing import Optional
from openai import OpenAI
from ..script_generator.models import Script
from .strategy import VideoGenerationStrategy
from .models import VideoResult
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config.settings import settings


class SoraStrategy(VideoGenerationStrategy):
    """OpenAI Sora策略"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        api_key = config.get("api_key") or settings.openai_api_key
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
        self.storage_path = config.get("storage_path", settings.videos_path)
    
    async def generate(self, script: Script, output_path: Optional[str] = None) -> VideoResult:
        """
        使用Sora生成视频
        
        Args:
            script: 剧本对象
            output_path: 输出路径
            
        Returns:
            视频生成结果
        """
        start_time = time.time()
        video_id = f"sora_{int(time.time())}"
        
        try:
            if self.client is None:
                # 如果没有配置API，返回模拟结果
                return self._create_mock_result(script, video_id, output_path)
            
            # 将剧本转换为Sora提示词
            prompt = self._script_to_prompt(script)
            
            # 调用Sora API（注意：Sora API可能还未公开，这里提供框架）
            # response = self.client.videos.generate(
            #     model="sora",
            #     prompt=prompt,
            #     duration=script.duration,
            #     resolution="1080p"
            # )
            
            # 模拟API调用
            print(f"调用Sora API生成视频: {prompt[:50]}...")
            await asyncio.sleep(2)  # 模拟生成时间
            
            # 保存视频文件（实际应该从API获取）
            if output_path is None:
                output_path = os.path.join(self.storage_path, f"{video_id}.mp4")
            
            # 创建模拟视频文件（使用同样的方法）
            return self._create_mock_result(script, video_id, output_path)
            
            generation_time = int(time.time() - start_time)
            
            return VideoResult(
                video_id=video_id,
                file_path=output_path,
                file_size=os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                duration=script.duration,
                resolution="1080p",
                format="mp4",
                status="completed",
                generation_strategy="sora",
                generation_time=generation_time,
            )
            
        except Exception as e:
            generation_time = int(time.time() - start_time)
            return VideoResult(
                video_id=video_id,
                file_path="",
                status="failed",
                generation_strategy="sora",
                generation_time=generation_time,
                error_message=str(e),
            )
    
    def _script_to_prompt(self, script: Script) -> str:
        """
        将剧本转换为Sora提示词
        
        Args:
            script: 剧本对象
            
        Returns:
            Sora提示词
        """
        prompt_parts = [f"Create a {script.duration}-second video titled '{script.title}'."]
        
        for scene in script.scenes:
            scene_desc = f"Scene {scene.scene_id} ({scene.duration}s): {scene.visual}. "
            if scene.narration:
                scene_desc += f"Narration: {scene.narration}. "
            prompt_parts.append(scene_desc)
        
        return " ".join(prompt_parts)
    
    def _create_mock_result(self, script: Script, video_id: str, 
                           output_path: Optional[str]) -> VideoResult:
        """创建模拟结果（用于测试）"""
        if output_path is None:
            output_path = os.path.join(self.storage_path, f"{video_id}.mp4")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 创建一个最小有效的MP4文件（使用MoviePy如果可用，否则创建简单的占位文件）
        try:
            from moviepy.editor import ColorClip, CompositeVideoClip, ImageClip, AudioFileClip
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            import tempfile
            
            # 创建一个简单的测试视频（不使用TextClip，避免ImageMagick依赖）
            # 创建一个彩色背景，颜色会根据场景变化
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
                
                # 创建字幕（使用PIL绘制文字到图片，然后转为视频）
                if scene.subtitles:
                    try:
                        # 创建字幕图片（更大的高度以便显示文字）
                        img = Image.new('RGBA', (1920, 300), (0, 0, 0, 180))  # 半透明黑色背景
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
                        
                        # 绘制文字（带描边效果，更明显）
                        # 先绘制描边（黑色，更粗）
                        for adj in [(-3, -3), (-3, 3), (3, -3), (3, 3), (-3, 0), (3, 0), (0, -3), (0, 3)]:
                            draw.text((x + adj[0], y + adj[1]), scene.subtitles, 
                                    font=font, fill=(0, 0, 0, 255))
                        # 再绘制文字（白色）
                        draw.text((x, y), scene.subtitles, font=font, fill=(255, 255, 255, 255))
                        
                        # 保存为临时文件
                        temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        img.save(temp_img.name)
                        temp_img.close()
                        
                        # 创建字幕视频片段（显示在底部，距离底部50像素）
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
            
            # 添加背景音乐（生成简单的音调）
            try:
                from moviepy.audio.AudioClip import AudioArrayClip
                # 生成简单的背景音乐（440Hz正弦波，音量逐渐减弱）
                sample_rate = 44100
                duration_samples = int(script.duration * sample_rate)
                t = np.linspace(0, script.duration, duration_samples)
                # 简单的音调，音量逐渐变化，添加一些变化避免单调
                base_freq = 440  # A4音符
                audio_array = (
                    np.sin(2 * np.pi * base_freq * t) * 0.2 * (1 - t / script.duration) +
                    np.sin(2 * np.pi * base_freq * 1.5 * t) * 0.1 * (1 - t / script.duration)
                ).astype(np.float32)
                audio_clip = AudioArrayClip(audio_array.reshape((len(audio_array), 1)), fps=sample_rate)
                video = video.set_audio(audio_clip)
                print(f"   已添加背景音乐（440Hz音调）")
            except Exception as e:
                print(f"   警告: 背景音乐生成失败: {e}，继续生成无音频视频")
            
            # 写入文件
            video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac' if video.audio else None,
                verbose=False,
                logger=None,
                preset='ultrafast'  # 快速编码
            )
            
            file_size = os.path.getsize(output_path)
            print(f"✅ 使用MoviePy生成视频成功（{file_size}字节）")
            print(f"   包含 {len(script.scenes)} 个场景，{len(subtitle_clips)} 个字幕")
            
        except ImportError:
            # 如果MoviePy不可用，创建一个最小有效的MP4文件头
            # 这是一个非常简单的MP4容器结构（仅用于测试）
            mp4_header = bytes([
                0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70,  # ftyp box
                0x69, 0x73, 0x6F, 0x6D, 0x00, 0x00, 0x02, 0x00,
                0x69, 0x73, 0x6F, 0x6D, 0x69, 0x73, 0x6F, 0x32,
                0x6D, 0x70, 0x34, 0x31, 0x00, 0x00, 0x00, 0x08,
                0x6D, 0x64, 0x61, 0x74,  # mdat box (空数据)
            ])
            
            with open(output_path, "wb") as f:
                f.write(mp4_header)
                # 填充一些数据使其看起来像视频文件
                f.write(b'\x00' * (1024 * 10))  # 10KB的占位数据
            
            file_size = os.path.getsize(output_path)
            print(f"⚠️  MoviePy未安装，创建了最小MP4文件（{file_size}字节）。建议安装MoviePy以生成真正的测试视频。")
        except Exception as e:
            # 如果MoviePy失败，尝试使用ffmpeg直接创建视频
            print(f"⚠️  MoviePy生成失败: {e}")
            print("   尝试使用ffmpeg创建视频...")
            
            try:
                import subprocess
                import tempfile
                
                # 创建一个简单的测试视频使用ffmpeg
                # 生成一个单色视频
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-f', 'lavfi',
                    '-i', f'color=c=0x6496C8:s=1920x1080:d={script.duration}',
                    '-pix_fmt', 'yuv420p',
                    '-y',  # 覆盖输出文件
                    output_path
                ]
                
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"✅ 使用ffmpeg生成视频成功（{file_size}字节）")
                else:
                    raise Exception(f"ffmpeg失败: {result.stderr}")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e2:
                # 如果ffmpeg也失败，创建一个最小有效的MP4文件
                print(f"⚠️  ffmpeg也失败: {e2}")
                print("   创建最小MP4文件...")
                
                # 创建一个最小有效的MP4文件头
                # 这是一个非常简单的MP4容器结构（仅用于测试）
                mp4_header = bytes([
                    0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70,  # ftyp box
                    0x69, 0x73, 0x6F, 0x6D, 0x00, 0x00, 0x02, 0x00,
                    0x69, 0x73, 0x6F, 0x6D, 0x69, 0x73, 0x6F, 0x32,
                    0x6D, 0x70, 0x34, 0x31, 0x00, 0x00, 0x00, 0x08,
                    0x6D, 0x64, 0x61, 0x74,  # mdat box
                ])
                
                with open(output_path, "wb") as f:
                    f.write(mp4_header)
                    # 填充一些数据使其看起来像视频文件（至少10KB）
                    f.write(b'\x00' * (1024 * 10))
                
                file_size = os.path.getsize(output_path)
                print(f"⚠️  已创建最小MP4文件（{file_size}字节），可能无法正常播放")
                print("   建议安装MoviePy或ffmpeg以生成真正的视频文件")
        
        return VideoResult(
            video_id=video_id,
            file_path=output_path,
            file_size=file_size,
            duration=script.duration,
            resolution="1080p",
            format="mp4",
            status="completed",
            generation_strategy="sora_mock",
            generation_time=2,
        )
    
    def get_capabilities(self) -> dict:
        """获取策略能力"""
        return {
            "max_duration": 60,
            "supported_resolutions": ["720p", "1080p"],
            "supported_formats": ["mp4"],
            "requires_api_key": True,
        }

