"""提示词模板"""
from typing import Dict, Any


class PromptTemplates:
    """提示词模板集合"""
    
    @staticmethod
    def script_generation_template(trending_title: str, trending_description: str = "", 
                                   keywords: list = None, duration: int = 60,
                                   platform: str = "抖音", target_audience: str = "年轻人") -> str:
        """
        生成剧本的提示词模板
        
        Args:
            trending_title: 热点标题
            trending_description: 热点描述
            keywords: 关键词列表
            duration: 视频时长（秒）
            platform: 目标平台
            target_audience: 目标观众
            
        Returns:
            完整的提示词
        """
        keywords_str = "、".join(keywords) if keywords else "无"
        
        prompt = f"""你是一位专业的短视频编剧。请根据以下热点话题创作一个 {duration} 秒的短视频剧本。

【热点信息】
标题: {trending_title}
描述: {trending_description}
关键词: {keywords_str}

【创作要求】
1. 开头 3 秒必须抓住眼球
2. 节奏紧凑，信息密度高
3. 适合 {platform} 平台风格
4. 目标观众: {target_audience}
5. 总时长控制在 {duration} 秒左右

【输出格式】
请严格按照以下 JSON 格式输出:
{{
  "title": "视频标题",
  "duration": {duration},
  "scenes": [
    {{
      "scene_id": 1,
      "duration": 5,
      "visual": "画面描述",
      "narration": "旁白文案",
      "subtitles": "字幕文本",
      "music": "背景音乐类型"
    }}
  ],
  "hashtags": ["#标签1", "#标签2"],
  "description": "视频简介"
}}

请确保：
- scenes 数组包含多个场景，每个场景时长 5-20 秒
- 所有场景的总时长接近 {duration} 秒
- 旁白文案要口语化、有吸引力
- 字幕文本要简洁有力
"""
        return prompt
    
    @staticmethod
    def optimize_prompt(base_prompt: str, additional_context: Dict[str, Any] = None) -> str:
        """
        优化提示词，添加上下文信息
        
        Args:
            base_prompt: 基础提示词
            additional_context: 额外的上下文信息
            
        Returns:
            优化后的提示词
        """
        if not additional_context:
            return base_prompt
        
        context_str = "\n【额外上下文】\n"
        for key, value in additional_context.items():
            context_str += f"{key}: {value}\n"
        
        return base_prompt + context_str

