from sqlalchemy import Column, String, Float, DateTime, ForeignKey, create_engine, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from src.config import settings
import logging
import os

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    position_level = Column(String)
    technologies = Column(String)  # 存储为JSON字符串
    performance_score = Column(Float, nullable=True)

    candidate_id = Column(String, ForeignKey("candidates.id"))
    candidate = relationship("Candidate", back_populates="sessions")
    difficulty_level = Column(Float, default=1.0)  # 当前面试难度系数
    performance_metrics = Column(JSON)  # 详细表现指标
    
    # 建立与面试记录的关系
    interview_records = relationship("InterviewRecord", back_populates="session")

class InterviewRecord(Base):
    __tablename__ = "interview_records"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    question = Column(String)
    answer = Column(String)
    feedback = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 建立与会话的关系
    session = relationship("Session", back_populates="interview_records")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True)
    name = Column(String)
    years_of_experience = Column(Float)
    skills = Column(JSON)  # 技能和熟练度
    education = Column(String)
    current_level = Column(String)  # junior/intermediate/senior
    interview_performance = Column(JSON)  # 历史面试表现
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="candidate")



# 数据库初始化函数
def init_db():
    """初始化数据库"""
    try:
        # 获取数据库文件路径
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')

        # 如果数据库文件存在，则删除它
        if os.path.exists(db_path) and db_path != ':memory:':
            os.remove(db_path)
            logging.info(f"Removed existing database file: {db_path}")

        # 创建数据库引擎
        engine = create_engine(settings.DATABASE_URL)

        # 删除所有现有表（以防万一）
        Base.metadata.drop_all(engine)
        logging.info("Dropped all existing tables")

        # 创建所有表
        Base.metadata.create_all(engine)
        logging.info("Database initialized successfully with new schema")

    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise
