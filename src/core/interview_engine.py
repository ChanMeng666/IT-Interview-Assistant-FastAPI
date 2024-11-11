import uuid

import google.generativeai as genai
from typing import List, Dict, Optional
import json
from src.config import settings
from src.database.models import Candidate, Session
import numpy as np

class InterviewEngine:
    def __init__(self):
        # 配置 Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.context = []
        self.current_difficulty = 1.0
        self.performance_history = []
        self.question_categories = {
            "theoretical": 0,
            "practical": 0,
            "problem_solving": 0,
            "system_design": 0
        }


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

    def _calculate_initial_difficulty(self, candidate: Candidate) -> float:
        """基于候选人背景计算初始难度"""
        base_difficulty = {
            "junior": 1.0,
            "intermediate": 1.5,
            "senior": 2.0
        }

        # 基础难度
        difficulty = base_difficulty.get(candidate.current_level, 1.0)

        # 根据工作经验调整
        experience_factor = min(candidate.years_of_experience / 2, 1.5)
        difficulty *= experience_factor

        # 根据历史面试表现调整
        if candidate.interview_performance:
            avg_performance = np.mean([p.get('score', 0) for p in candidate.interview_performance])
            performance_factor = avg_performance / 50  # 归一化到0-2范围
            difficulty *= performance_factor

        return min(max(difficulty, 0.5), 2.5)  # 限制在0.5-2.5范围内

    def _adjust_difficulty(self, performance_score: float) -> float:
        """根据答题表现动态调整难度"""
        # 记录历史表现
        self.performance_history.append(performance_score)

        # 计算近期表现趋势
        recent_performance = self.performance_history[-3:] if len(
            self.performance_history) >= 3 else self.performance_history
        avg_performance = np.mean(recent_performance)

        # 动态调整难度
        if avg_performance > 85:  # 表现优秀，增加难度
            self.current_difficulty = min(self.current_difficulty * 1.2, 2.5)
        elif avg_performance < 60:  # 表现欠佳，降低难度
            self.current_difficulty = max(self.current_difficulty * 0.8, 0.5)

        return self.current_difficulty

    def _create_adaptive_question(self, topic: str, difficulty: float) -> str:
        """根据难度生成适应性问题"""
        difficulty_descriptors = {
            (0.5, 1.0): "basic concepts and fundamentals",
            (1.0, 1.5): "intermediate concepts and practical applications",
            (1.5, 2.0): "advanced concepts and system design",
            (2.0, 2.5): "expert-level problems and architecture decisions"
        }

        # 确定难度级别描述
        level_desc = next(
            desc for (min_d, max_d), desc in difficulty_descriptors.items()
            if min_d <= difficulty <= max_d
        )

        # 生成问题提示
        prompt = f"""
        Generate a {topic} interview question that focuses on {level_desc}.
        Current difficulty level: {difficulty}/2.5

        The question should:
        1. Match the specified difficulty level
        2. Require practical understanding
        3. Allow for follow-up discussion
        4. Test both theoretical knowledge and practical application

        Format the response as:
        {{
            "question": "The main question",
            "expected_topics": ["Key points the answer should cover"],
            "follow_ups": ["Potential follow-up questions"],
            "evaluation_criteria": ["Criteria for evaluating the answer"]
        }}
        """

        return prompt



    # async def start_interview(self, position_level: str, technologies: List[str]) -> Dict:
    #     """开始新的面试会话"""
    #     prompt = self._create_interview_prompt(position_level, technologies)
    #     try:
    #         response = await self.model.generate_content_async(prompt)
    #         result = json.loads(response.text)
    #
    #         self.context = [{"role": "interviewer", "content": result["question"]}]
    #
    #         return {
    #             "question": result["question"],
    #             "session_context": self.context,
    #             "session_id": "test_session"  # 实际应用中应该生成唯一ID
    #         }
    #     except Exception as e:
    #         print(f"Error in start_interview: {e}")
    #         return {
    #             "question": "Could you tell me about your background in software development?",
    #             "session_context": [],
    #             "session_id": "test_session"
    #         }
    #
    # async def process_answer(self, answer: str) -> Dict:
    #     """处理回答并生成下一个问题"""
    #     self.context.append({"role": "candidate", "content": answer})
    #
    #     prompt = f"""
    #     Based on the following interview context, evaluate the answer and provide a relevant follow-up question:
    #
    #     Previous question: {self.context[-2]['content']}
    #     Candidate's answer: {answer}
    #
    #     Provide your response in this format:
    #     {{
    #         "evaluation": "Brief evaluation of the answer",
    #         "next_question": "Your follow-up question",
    #         "score": "Score out of 10"
    #     }}
    #     """
    #
    #     try:
    #         response = await self.model.generate_content_async(prompt)
    #         result = json.loads(response.text)
    #
    #         self.context.append({"role": "interviewer", "content": result["next_question"]})
    #
    #         return {
    #             "evaluation": result["evaluation"],
    #             "next_question": result["next_question"],
    #             "session_context": self.context
    #         }
    #     except Exception as e:
    #         print(f"Error in process_answer: {e}")
    #         return {
    #             "evaluation": "Thank you for your answer.",
    #             "next_question": "Could you tell me more about your experience?",
    #             "session_context": self.context
    #         }
    #
    # async def end_interview(self) -> Dict:
    #     """结束面试并生成总结"""
    #     full_context = "\n".join([
    #         f"{'Interviewer' if item['role'] == 'interviewer' else 'Candidate'}: {item['content']}"
    #         for item in self.context
    #     ])
    #
    #     prompt = f"""
    #     Based on this complete interview, provide a comprehensive evaluation:
    #     {full_context}
    #
    #     Format your response as:
    #     {{
    #         "overall_score": "Score out of 100",
    #         "strengths": ["List of strengths"],
    #         "areas_for_improvement": ["List of areas to improve"],
    #         "summary": "Brief summary of the interview"
    #     }}
    #     """
    #
    #     try:
    #         response = await self.model.generate_content_async(prompt)
    #         return json.loads(response.text)
    #     except Exception as e:
    #         print(f"Error in end_interview: {e}")
    #         return {
    #             "overall_score": "75",
    #             "strengths": ["Good communication", "Shows potential"],
    #             "areas_for_improvement": ["Need more specific examples", "Could improve technical depth"],
    #             "summary": "The candidate showed promise but needs more practical experience."
    #         }

    async def start_interview(
            self,
            candidate_id: str,
            position_level: str,
            technologies: List[str],
            db_session
    ) -> Dict:
        """开始新的面试会话"""
        try:
            # 获取候选人信息
            candidate = db_session.query(Candidate).get(candidate_id)
            if not candidate:
                raise ValueError("Candidate not found")

            # 计算初始难度
            self.current_difficulty = self._calculate_initial_difficulty(candidate)

            # 根据技术栈和难度生成初始问题
            initial_topic = technologies[0]  # 从第一个技术开始
            question_prompt = self._create_adaptive_question(initial_topic, self.current_difficulty)

            response = await self.model.generate_content_async(question_prompt)
            result = json.loads(response.text)

            # 创建新的面试会话记录
            interview_session = Session(
                id=str(uuid.uuid4()),  # 确保设置了ID
                candidate_id=candidate_id,
                position_level=position_level,
                technologies=",".join(technologies),
                difficulty_level=self.current_difficulty,
                performance_metrics={
                    "questions_asked": 0,
                    "average_score": 0,
                    "topic_coverage": self.question_categories.copy()
                }
            )

            db_session.add(interview_session)
            db_session.commit()

            self.context = [{
                "role": "interviewer",
                "content": result["question"],
                "metadata": {
                    "difficulty": self.current_difficulty,
                    "expected_topics": result["expected_topics"],
                    "evaluation_criteria": result["evaluation_criteria"]
                }
            }]

            # 确保返回所有必需的字段
            return {
                "session_id": interview_session.id,  # 使用新创建的会话ID
                "question": result["question"],
                "difficulty_level": self.current_difficulty,
                "session_context": self.context
            }

        except Exception as e:
            print(f"Error in start_interview: {e}")
            db_session.rollback()  # 确保在出错时回滚数据库事务
            raise

    async def process_answer(self, answer: str, db_session) -> Dict:
        """处理回答并生成下一个问题"""
        if not self.context:
            raise ValueError("No active interview session")

        last_question = self.context[-1]
        evaluation_prompt = f"""
        Evaluate this answer based on the following criteria:
        Question: {last_question['content']}
        Expected topics: {last_question['metadata']['expected_topics']}
        Evaluation criteria: {last_question['metadata']['evaluation_criteria']}

        Answer: {answer}

        Provide evaluation in this format:
        {{
            "score": "Score out of 100",
            "strength_points": ["Strong points in the answer"],
            "weakness_points": ["Areas that need improvement"],
            "missing_topics": ["Expected topics that were not covered"],
            "clarity_score": "Score out of 100 for communication clarity"
        }}
        """

        try:
            # 评估答案
            eval_response = await self.model.generate_content_async(evaluation_prompt)
            evaluation = json.loads(eval_response.text)

            # 调整难度
            score = float(evaluation["score"])
            new_difficulty = self._adjust_difficulty(score)

            # 生成下一个问题
            next_question_prompt = self._create_adaptive_question(
                "next topic",  # 这里可以基于技术栈选择下一个主题
                new_difficulty
            )

            question_response = await self.model.generate_content_async(next_question_prompt)
            next_question = json.loads(question_response.text)

            # 更新上下文
            self.context.append({
                "role": "candidate",
                "content": answer,
                "metadata": {
                    "evaluation": evaluation
                }
            })

            self.context.append({
                "role": "interviewer",
                "content": next_question["question"],
                "metadata": {
                    "difficulty": new_difficulty,
                    "expected_topics": next_question["expected_topics"],
                    "evaluation_criteria": next_question["evaluation_criteria"]
                }
            })

            return {
                "evaluation": evaluation,
                "next_question": next_question["question"],
                "current_difficulty": new_difficulty,
                "session_context": self.context
            }

        except Exception as e:
            print(f"Error in process_answer: {e}")
            raise

    async def end_interview(self, db_session) -> Dict:
        """结束面试并生成详细报告"""
        if not self.context:
            raise ValueError("No interview context found")

        # 收集所有评估数据
        evaluations = [
            msg["metadata"]["evaluation"]
            for msg in self.context
            if msg["role"] == "candidate" and "evaluation" in msg["metadata"]
        ]

        # 计算总体统计
        scores = [float(eval_["score"]) for eval_ in evaluations]
        clarity_scores = [float(eval_["clarity_score"]) for eval_ in evaluations]

        # 收集优势和改进点
        all_strengths = [point for eval_ in evaluations for point in eval_["strength_points"]]
        all_weaknesses = [point for eval_ in evaluations for point in eval_["weakness_points"]]

        # 生成最终报告
        report = {
            "overall_score": np.mean(scores),
            "communication_score": np.mean(clarity_scores),
            "difficulty_progression": self.performance_history,
            "key_strengths": list(set(all_strengths)),
            "areas_for_improvement": list(set(all_weaknesses)),
            "question_count": len(evaluations),
            "performance_trend": "improving" if np.gradient(scores)[-1] > 0 else "steady" if np.gradient(scores)[
                                                                                                 -1] == 0 else "declining",
            "recommendations": await self._generate_recommendations(all_weaknesses)
        }

        return report

    async def _generate_recommendations(self, weaknesses: List[str]) -> List[str]:
        """基于面试表现生成具体改进建议"""
        if not weaknesses:
            return ["Continue practicing and staying updated with latest technologies"]

        prompt = f"""
        Based on these identified weaknesses:
        {json.dumps(weaknesses)}

        Provide specific, actionable recommendations for improvement.
        Focus on:
        1. Learning resources
        2. Practice exercises
        3. Project suggestions
        4. Study strategies

        Format as a list of specific recommendations.
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return ["Unable to generate specific recommendations"]