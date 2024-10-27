from sqlalchemy import Column, String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from src.config import settings

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    position_level = Column(String)
    technologies = Column(String)  # 存储为JSON字符串
    performance_score = Column(Float, nullable=True)
    
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

# 数据库初始化函数
def init_db():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)
