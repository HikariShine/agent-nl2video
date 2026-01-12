"""阿里通义千问策略"""
import json
from typing import Optional
import dashscope
from dashscope import Generation
from .strategy import LLMStrategy
from .models import Script, Scene
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config.settings import settings


class QwenStrategy(LLMStrategy):
    """阿里通义千问策略"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        api_key = config.get("api_key") or settings.qwen_api_key
        if api_key:
            dashscope.api_key = api_key
        self.model = config.get("model", "qwen-max")
    
    async def generate(self, prompt: str, config: Optional[dict] = None) -> Script:
        """
        使用通义千问生成剧本
        
        Args:
            prompt: 提示词
            config: 生成配置
            
        Returns:
            生成的剧本
        """
        if config is None:
            config = {}
        
        try:
            # 调用通义千问API
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 2000),
            )
            
            if response.status_code == 200:
                content = response.output.text
                # 解析JSON响应
                script_data = self._parse_response(content)
                return self._create_script(script_data)
            else:
                raise Exception(f"API调用失败: {response.message}")
                
        except Exception as e:
            # 如果API调用失败，返回一个示例剧本
            print(f"通义千问API调用失败: {e}，返回示例剧本")
            return self._create_example_script()
    
    def _parse_response(self, content: str) -> dict:
        """
        解析API响应
        
        Args:
            content: API返回的文本内容
            
        Returns:
            解析后的剧本数据
        """
        try:
            # 尝试提取JSON部分
            # 如果响应包含markdown代码块，提取其中的JSON
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # 尝试解析JSON
            return json.loads(content)
        except json.JSONDecodeError:
            # 如果解析失败，返回默认结构
            return self._get_default_script_data()
    
    def _create_script(self, data: dict) -> Script:
        """
        从数据创建Script对象
        
        Args:
            data: 剧本数据字典
            
        Returns:
            Script对象
        """
        scenes = []
        for scene_data in data.get("scenes", []):
            scene = Scene(
                scene_id=scene_data.get("scene_id", len(scenes) + 1),
                duration=scene_data.get("duration", 5),
                visual=scene_data.get("visual", ""),
                narration=scene_data.get("narration", ""),
                subtitles=scene_data.get("subtitles", ""),
                music=scene_data.get("music"),
            )
            scenes.append(scene)
        
        return Script(
            title=data.get("title", "未命名视频"),
            duration=data.get("duration", 60),
            scenes=scenes,
            hashtags=data.get("hashtags", []),
            description=data.get("description", ""),
            llm_model=self.model,
        )
    
    def _create_example_script(self) -> Script:
        """创建示例剧本（用于测试）"""
        return Script(
            title="示例视频：AI改变生活",
            duration=60,
            scenes=[
                Scene(
                    scene_id=1,
                    duration=10,
                    visual="展示AI技术的应用场景",
                    narration="AI正在改变我们的生活方式",
                    subtitles="AI改变生活",
                    music="轻快",
                ),
                Scene(
                    scene_id=2,
                    duration=15,
                    visual="展示具体应用案例",
                    narration="从智能家居到自动驾驶，AI无处不在",
                    subtitles="AI无处不在",
                    music="轻快",
                ),
                Scene(
                    scene_id=3,
                    duration=20,
                    visual="展示未来展望",
                    narration="未来，AI将带来更多可能性",
                    subtitles="未来已来",
                    music="激昂",
                ),
            ],
            hashtags=["#AI", "#科技", "#未来"],
            description="探索AI如何改变我们的生活",
            llm_model=self.model,
        )
    
    def _get_default_script_data(self) -> dict:
        """获取默认剧本数据结构"""
        return {
            "title": "未命名视频",
            "duration": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "duration": 20,
                    "visual": "画面描述",
                    "narration": "旁白文案",
                    "subtitles": "字幕文本",
                    "music": "背景音乐",
                }
            ],
            "hashtags": ["#标签"],
            "description": "视频简介",
        }
    
    def validate_api_key(self) -> bool:
        """验证API密钥"""
        try:
            # 简单的验证：检查API密钥是否存在
            return bool(dashscope.api_key)
        except:
            return False

