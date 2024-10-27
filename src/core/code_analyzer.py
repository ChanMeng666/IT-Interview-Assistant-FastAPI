import google.generativeai as genai
from typing import Dict
from src.config import settings


class CodeAnalyzer:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    async def analyze_code(self, code: str, language: str) -> Dict:
        """分析代码"""
        prompt = f"""
        Analyze this {language} code:

        ```{language}
        {code}
        ```

        Provide analysis in this format:
        {{
            "complexity": {{
                "time_complexity": "Big O notation with explanation",
                "space_complexity": "Big O notation with explanation"
            }},
            "best_practices": [
                "List of followed best practices",
                "List of violated best practices"
            ],
            "potential_issues": [
                "List of potential problems or security concerns"
            ],
            "suggestions": [
                "List of specific improvement suggestions"
            ]
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error in analyze_code: {e}")
            return {
                "complexity": {
                    "time_complexity": "Unable to determine",
                    "space_complexity": "Unable to determine"
                },
                "best_practices": ["Code analysis unavailable"],
                "potential_issues": ["Unable to analyze code"],
                "suggestions": ["Please try again later"]
            }