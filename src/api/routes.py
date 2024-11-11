from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import uuid
from datetime import datetime

from src.database.session import get_db
from src.database.models import Session as DBSession, InterviewRecord
from src.core.interview_engine import InterviewEngine
from src.core.code_analyzer import CodeAnalyzer
from src.core.tech_explainer import TechExplainer
from src.database.models import Candidate

router = APIRouter()
interview_engine = InterviewEngine()
code_analyzer = CodeAnalyzer()
tech_explainer = TechExplainer()


@router.post("/interview/start")
async def start_interview(
        request: dict,
        db: Session = Depends(get_db)
):
    """开始新的面试会话"""
    try:
        if not request.get("candidate_id"):
            raise HTTPException(status_code=400, detail="candidate_id is required")

        result = await interview_engine.start_interview(
            candidate_id=request["candidate_id"],
            position_level=request.get("position_level", "junior"),
            technologies=request.get("technologies", ["Python"]),
            db_session=db
        )

        # 验证返回结果包含所有必需字段
        required_fields = ["session_id", "question", "difficulty_level", "session_context"]
        missing_fields = [field for field in required_fields if field not in result]

        if missing_fields:
            raise HTTPException(
                status_code=500,
                detail=f"Missing required fields in response: {', '.join(missing_fields)}"
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error in start_interview route: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interview/answer/{session_id}")
async def process_answer(
    session_id: str,
    answer: str,
    db: Session = Depends(get_db)
):
    # 处理答案并获取下一个问题
    result = await interview_engine.process_answer(answer)
    
    # 记录答案和新问题
    record = InterviewRecord(
        id=str(uuid.uuid4()),
        session_id=session_id,
        question=result["next_question"],
        answer=answer,
        feedback=result["evaluation"]
    )
    db.add(record)
    db.commit()
    
    return result

@router.post("/interview/end/{session_id}")
async def end_interview(
    session_id: str,
    db: Session = Depends(get_db)
):
    # 获取总结报告
    result = await interview_engine.end_interview()
    
    # 更新会话状态
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.end_time = datetime.utcnow()
    session.performance_score = float(result["overall_score"])
    db.commit()
    
    return result

@router.post("/code/analyze")
async def analyze_code(code: str, language: str):
    return await code_analyzer.analyze_code(code, language)

@router.post("/code/optimize")
async def optimize_code(code: str, language: str):
    return await code_analyzer.optimize_code(code, language)

@router.post("/code/explain")
async def explain_code(code: str, language: str):
    return await code_analyzer.explain_code(code, language)

@router.post("/code/security")
async def check_code_security(code: str, language: str):
    return await code_analyzer.check_security(code, language)


@router.post("/explain/concept")
async def explain_technical_concept(
    concept: str,
    level: str = "intermediate"
):
    """获取技术概念解释"""
    return await tech_explainer.explain_concept(concept, level)

@router.post("/explain/learning-path")
async def get_learning_path(
    topic: str,
    current_level: str,
    target_level: str
):
    """获取学习路径建议"""
    return await tech_explainer.create_learning_path(
        topic,
        current_level,
        target_level
    )

@router.post("/explain/concept-relations")
async def get_concept_relations(concept: str):
    """获取知识点关系图"""
    return await tech_explainer.get_concept_relations(concept)


@router.post("/candidates/create")
async def create_candidate(
    candidate: dict,
    db: Session = Depends(get_db)
):
    """创建新的候选人档案"""
    try:
        new_candidate = Candidate(
            id=str(uuid.uuid4()),
            name=candidate["name"],
            years_of_experience=candidate["years_of_experience"],
            skills=candidate["skills"],
            education=candidate["education"],
            current_level=candidate["current_level"]
        )
        db.add(new_candidate)
        db.commit()
        return {"candidate_id": new_candidate.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interview/start")
async def start_interview(
    request: dict,
    db: Session = Depends(get_db)
):
    """开始新的面试会话，包含候选人信息"""
    try:
        result = await interview_engine.start_interview(
            candidate_id=request["candidate_id"],
            position_level=request.get("position_level", "junior"),
            technologies=request.get("technologies", ["Python"]),
            db_session=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interview/answer/{session_id}")
async def process_answer(
    session_id: str,
    request: dict,
    db: Session = Depends(get_db)
):
    """处理答案并返回下一个问题，包含难度调整"""
    try:
        result = await interview_engine.process_answer(
            answer=request["answer"],
            db_session=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))