import google.generativeai as genai
from typing import Dict, List
from src.config import settings


class TechExplainer:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    async def explain_concept(self, concept: str, level: str = "intermediate") -> Dict:
        """深入解释技术概念"""
        prompt = f"""
        Explain the technical concept: {concept}
        Level: {level}

        Provide the explanation in this format:
        {{
            "concept": "Name of the concept",
            "definition": "Clear and concise definition",
            "key_points": ["List of key points to understand"],
            "real_world_applications": ["List of practical applications"],
            "code_examples": ["Relevant code examples if applicable"],
            "related_concepts": ["List of related topics to explore"],
            "learning_resources": ["Recommended learning materials"]
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Error in explain_concept: {e}")
            return {
                "error": "Failed to generate explanation",
                "message": str(e)
            }

    async def create_learning_path(self, topic: str, current_level: str, target_level: str) -> Dict:
        """创建学习路径建议"""
        prompt = f"""
        Create a learning path for:
        Topic: {topic}
        Current Level: {current_level}
        Target Level: {target_level}

        Format the response as:
        {{
            "prerequisites": ["Required foundational knowledge"],
            "learning_stages": [
                {{
                    "stage": "Stage name",
                    "topics": ["Topics to cover"],
                    "resources": ["Recommended resources"],
                    "projects": ["Practical projects to try"],
                    "estimated_duration": "Estimated time to complete"
                }}
            ],
            "milestones": ["Key checkpoints to validate progress"],
            "next_steps": ["What to learn after completing this path"]
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Error in create_learning_path: {e}")
            return {
                "error": "Failed to generate learning path",
                "message": str(e)
            }

    async def get_concept_relations(self, concept: str) -> Dict:
        """获取相关知识点联系"""
        prompt = f"""
        Analyze the relationships for the concept: {concept}

        Provide the analysis in this format:
        {{
            "prerequisites": ["Concepts you should know before this"],
            "related_concepts": ["Directly related concepts"],
            "advanced_topics": ["More advanced concepts that build on this"],
            "common_misconceptions": ["Frequently misunderstood points"],
            "practical_applications": ["Where this concept is commonly used"]
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Error in get_concept_relations: {e}")
            return {
                "error": "Failed to analyze concept relations",
                "message": str(e)
            }