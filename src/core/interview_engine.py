import google.generativeai as genai
from typing import List, Dict, Optional
import json
from src.config import settings


class InterviewEngine:
    def __init__(self):
        # 配置 Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.context = []

    def _create_interview_prompt(self, position_level: str, technologies: List[str]) -> str:
        tech_str = ", ".join(technologies)
        return f"""
        You are an experienced IT technical interviewer. Your task is to:
        1. Focus on {position_level} level position involving {tech_str}
        2. Ask technical questions appropriate for this level
        3. Each question should be specific and clear
        4. Evaluate the candidate's responses
        5. Provide constructive feedback

        Format your responses in this structure:
        {{
            "question": "Your technical question here",
            "context": "Brief context or background for the question"
        }}
        """

    async def start_interview(self, position_level: str, technologies: List[str]) -> Dict:
        """开始新的面试会话"""
        prompt = self._create_interview_prompt(position_level, technologies)
        try:
            response = await self.model.generate_content_async(prompt)
            result = json.loads(response.text)

            self.context = [{"role": "interviewer", "content": result["question"]}]

            return {
                "question": result["question"],
                "session_context": self.context,
                "session_id": "test_session"  # 实际应用中应该生成唯一ID
            }
        except Exception as e:
            print(f"Error in start_interview: {e}")
            return {
                "question": "Could you tell me about your background in software development?",
                "session_context": [],
                "session_id": "test_session"
            }

    async def process_answer(self, answer: str) -> Dict:
        """处理回答并生成下一个问题"""
        self.context.append({"role": "candidate", "content": answer})

        prompt = f"""
        Based on the following interview context, evaluate the answer and provide a relevant follow-up question:

        Previous question: {self.context[-2]['content']}
        Candidate's answer: {answer}

        Provide your response in this format:
        {{
            "evaluation": "Brief evaluation of the answer",
            "next_question": "Your follow-up question",
            "score": "Score out of 10"
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            result = json.loads(response.text)

            self.context.append({"role": "interviewer", "content": result["next_question"]})

            return {
                "evaluation": result["evaluation"],
                "next_question": result["next_question"],
                "session_context": self.context
            }
        except Exception as e:
            print(f"Error in process_answer: {e}")
            return {
                "evaluation": "Thank you for your answer.",
                "next_question": "Could you tell me more about your experience?",
                "session_context": self.context
            }

    async def end_interview(self) -> Dict:
        """结束面试并生成总结"""
        full_context = "\n".join([
            f"{'Interviewer' if item['role'] == 'interviewer' else 'Candidate'}: {item['content']}"
            for item in self.context
        ])

        prompt = f"""
        Based on this complete interview, provide a comprehensive evaluation:
        {full_context}

        Format your response as:
        {{
            "overall_score": "Score out of 100",
            "strengths": ["List of strengths"],
            "areas_for_improvement": ["List of areas to improve"],
            "summary": "Brief summary of the interview"
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error in end_interview: {e}")
            return {
                "overall_score": "75",
                "strengths": ["Good communication", "Shows potential"],
                "areas_for_improvement": ["Need more specific examples", "Could improve technical depth"],
                "summary": "The candidate showed promise but needs more practical experience."
            }