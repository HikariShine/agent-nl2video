"""端到端测试"""
import asyncio
from src.trending_tracker.manager import TrendingTrackerManager
from src.script_generator.generator import ScriptGenerator
from src.video_generator.generator import VideoGenerator
from config.settings import settings


# 配置
TRENDING_CONFIG = {
    "trending_sources": [
        {
            "name": "douyin_hot",
            "type": "scraper",
            "enabled": True,
        }
    ]
}

SCRIPT_CONFIG = {
    "strategy": "qwen",
    "strategy_config": {
        "model": "qwen-max",
        "api_key": settings.qwen_api_key,
    },
    "temperature": 0.7,
    "max_tokens": 2000,
}

VIDEO_CONFIG = {
    "strategy": "cogvideox",  # 使用 CogVideoX 本地 AI 视频生成
    "strategy_config": {
        "storage_path": settings.videos_path,
        "model_id": "THUDM/CogVideoX-2b",  # 2B版本，适合M4
        "lazy_load": True,
    },
    "post_process": {
        "add_subtitles": False,  # CogVideoX生成的视频不需要额外添加字幕
        "add_music": False,
    },
}


async def test_full_workflow():
    """测试完整工作流"""
    print("=" * 50)
    print("开始端到端测试")
    print("=" * 50)
    
    # 1. 获取热点
    print("\n[1/3] 获取热点数据...")
    trending_manager = TrendingTrackerManager(TRENDING_CONFIG)
    trending_items = await trending_manager.get_trending_top(limit=5)
    
    if not trending_items:
        print("❌ 未获取到热点数据")
        return
    
    print(f"✅ 共获取到 {len(trending_items)} 个热点:")
    for i, item in enumerate(trending_items, 1):
        print(f"\n   热点 {i}:")
        print(f"   - ID: {item.id}")
        print(f"   - 标题: {item.title}")
        print(f"   - 描述: {item.description[:50]}..." if len(item.description) > 50 else f"   - 描述: {item.description}")
        print(f"   - 分类: {item.category}")
        print(f"   - 热度值: {item.heat_value}")
        print(f"   - 综合评分: {item.trending_score}")
        print(f"   - 关键词: {', '.join(item.keywords) if item.keywords else '无'}")
        print(f"   - 来源: {item.source}")
        print(f"   - URL: {item.url}")
    
    trending_item = trending_items[0]
    print(f"\n   使用第一个热点进行后续处理: {trending_item.title}")
    
    # 2. 生成剧本
    print("\n[2/3] 生成剧本...")
    script_generator = ScriptGenerator(SCRIPT_CONFIG)
    script = await script_generator.generate_from_trending(trending_item, duration=60)
    
    print(f"✅ 剧本生成成功!")
    print(f"   标题: {script.title}")
    print(f"   时长: {script.duration}秒")
    print(f"   描述: {script.description}")
    print(f"   标签: {', '.join(script.hashtags) if script.hashtags else '无'}")
    print(f"   使用的模型: {script.llm_model}")
    print(f"   场景数: {len(script.scenes)}")
    print(f"\n   场景详情:")
    for scene in script.scenes:
        print(f"   场景 {scene.scene_id} ({scene.duration}秒):")
        print(f"     - 画面: {scene.visual}")
        print(f"     - 旁白: {scene.narration}")
        print(f"     - 字幕: {scene.subtitles}")
        print(f"     - 音乐: {scene.music or '无'}")
    
    # 3. 生成视频
    print("\n[3/3] 生成视频...")
    video_generator = VideoGenerator(VIDEO_CONFIG)
    video_result = await video_generator.generate(script)
    
    if video_result.status == "completed":
        print(f"✅ 视频生成成功!")
        print(f"   视频ID: {video_result.video_id}")
        print(f"   文件路径: {video_result.file_path}")
        print(f"   文件大小: {video_result.file_size} 字节")
        print(f"   生成耗时: {video_result.generation_time} 秒")
    else:
        print(f"❌ 视频生成失败: {video_result.error_message}")
    
    print("\n" + "=" * 50)
    print("端到端测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_full_workflow())

