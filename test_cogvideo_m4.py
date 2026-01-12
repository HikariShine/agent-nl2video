"""CogVideoX 多场景视频生成器 - 子进程模式"""
import os
import sys
import time
import json
import subprocess
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Scene:
    """视频场景"""
    prompt: str
    duration: float = 1.1  # 秒
    seed: int = 42


@dataclass  
class VideoConfig:
    """视频配置"""
    frames: int = 9          # 帧数 (4k+1: 9,13,17...)
    steps: int = 12          # 推理步数
    guidance: float = 6.0    # 引导强度
    fps: int = 8             # 帧率
    output_dir: str = "./storage/videos"


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ==================== 场景配置 ====================
SCENES = [
    Scene("A glowing AI robot awakens in a dark laboratory, blue neon lights flashing, eyes lighting up, cinematic", seed=42),
    Scene("Futuristic city at night, flying cars zooming past skyscrapers, holographic ads, cyberpunk, camera moving", seed=123),
    Scene("Humanoid robot walking through futuristic corridor, blue orange lights on metal, dynamic camera, cinematic", seed=456),
]

CONFIG = VideoConfig()


# ==================== 核心函数 ====================
def generate_segment(scene: Scene, index: int, config: VideoConfig) -> str:
    """生成单个场景视频（在子进程中调用）"""
    import torch
    import gc
    from diffusers import CogVideoXPipeline
    from diffusers.utils import export_to_video
    
    log(f"场景 {index + 1}: {scene.prompt[:50]}...")
    
    # 加载模型
    torch.set_default_dtype(torch.float32)
    pipe = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-2b", torch_dtype=torch.float32)
    
    for name in ['transformer', 'vae', 'text_encoder']:
        if hasattr(pipe, name) and getattr(pipe, name) is not None:
            setattr(pipe, name, getattr(pipe, name).float())
    
    pipe.enable_model_cpu_offload(device="mps")
    pipe.enable_attention_slicing(slice_size=1)
    
    # 生成
    generator = torch.Generator(device="cpu").manual_seed(scene.seed)
    
    with torch.no_grad():
        frames = pipe(
            prompt=scene.prompt,
            num_inference_steps=config.steps,
            guidance_scale=config.guidance,
            num_frames=config.frames,
            generator=generator,
        ).frames[0]
    
    # 保存
    path = os.path.join(config.output_dir, f"segment_{index + 1}.mp4")
    export_to_video(frames, path, fps=config.fps)
    log(f"✅ 已保存: {path}")
    
    del frames, pipe
    gc.collect()
    torch.mps.empty_cache()
    
    return path


def run_in_subprocess(scene: Scene, index: int) -> bool:
    """在独立子进程中生成场景"""
    script = f'''
import sys; sys.path.insert(0, {repr(os.getcwd())})
from test_cogvideo_m4 import generate_segment, Scene, VideoConfig
generate_segment(
    Scene({repr(scene.prompt)}, seed={scene.seed}),
    {index},
    VideoConfig()
)
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=os.getcwd())
    return result.returncode == 0


def concatenate(paths: List[str], output: str, fps: int) -> bool:
    """拼接视频片段"""
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        clips = [VideoFileClip(p) for p in paths]
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(output, fps=fps, codec="libx264", audio=False, logger=None)
        for c in clips: c.close()
        final.close()
        return True
    except Exception as e:
        log(f"拼接失败: {e}")
        return False


# ==================== 主程序 ====================
def main():
    log("=" * 50)
    log("CogVideoX 多场景视频生成")
    log("=" * 50)
    
    os.makedirs(CONFIG.output_dir, exist_ok=True)
    
    log(f"场景数: {len(SCENES)}, 每段: {CONFIG.frames}帧/{CONFIG.frames/CONFIG.fps:.1f}秒")
    
    # 生成各场景
    paths = []
    for i, scene in enumerate(SCENES):
        log(f"\n{'='*50}\n生成场景 {i+1}/{len(SCENES)}（子进程）\n{'='*50}")
        
        path = os.path.join(CONFIG.output_dir, f"segment_{i + 1}.mp4")
        if run_in_subprocess(scene, i) and os.path.exists(path):
            paths.append(path)
            log("✅ 子进程完成，内存已释放")
        else:
            log(f"❌ 场景 {i+1} 失败")
            break
    
    # 拼接
    if len(paths) == len(SCENES):
        log(f"\n{'='*50}\n拼接视频\n{'='*50}")
        output = os.path.join(CONFIG.output_dir, "final.mp4")
        
        if concatenate(paths, output, CONFIG.fps):
            size = os.path.getsize(output) / 1024
            duration = len(SCENES) * CONFIG.frames / CONFIG.fps
            log(f"\n✅ 完成! {duration:.1f}秒, {size:.1f}KB\n   {output}")
            log(f"片段保留: {paths}")


if __name__ == "__main__":
    main()
