from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import uuid
from datetime import datetime

from src.database.session import get_db
from src.database.models import Session as DBSession, InterviewRecord
from src.core.interview_engine import InterviewEngine
from src.core.code_analyzer import CodeAnalyzer

router = APIRouter()
interview_engine = InterviewEngine()
code_analyzer = CodeAnalyzer()

@router.post("/interview/start")
async def start_interview(
        request: dict,
        db: Session = Depends(get_db)
):
    try:
        position_level = request.get("position_level", "初级")
        technologies = request.get("technologies", ["Python"])

        result = await interview_engine.start_interview(position_level, technologies)

        # 创建新的面试会话
        session_id = str(uuid.uuid4())
        db_session = DBSession(
            id=session_id,
            position_level=position_level,
            technologies=",".join(technologies)
        )
        db.add(db_session)
        db.commit()

        # 记录第一个问题
        record = InterviewRecord(
            id=str(uuid.uuid4()),
            session_id=session_id,
            question=result.get("question", "")
        )
        db.add(record)
        db.commit()

        return {
            "session_id": session_id,
            "question": result.get("question", "让我们开始面试。请做个自我介绍。"),
            "session_context": result.get("session_context", [])
        }
    except Exception as e:
        db.rollback()
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
