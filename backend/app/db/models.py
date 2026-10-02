from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class InterviewSession(Base):
    """
    Represents an interview session.
    A session can contain multiple questions/answers and analysis results.
    """
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=True)
    category = Column(String(100), default="general", index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    questions = relationship("QuestionAnswer", back_populates="session", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="session", cascade="all, delete-orphan")


class QuestionAnswer(Base):
    """
    Represents an individual question asked during an interview session and the user's answer.
    """
    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=False)
    category = Column(String(100), default="general", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    session = relationship("InterviewSession", back_populates="questions")
    analysis_result = relationship("AnalysisResult", back_populates="question_answer", uselist=False, cascade="all, delete-orphan")


class AnalysisResult(Base):
    """
    Represents the evaluation/analysis feedback for a specific question-answer pair in a session.
    """
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("question_answers.id", ondelete="CASCADE"), nullable=False)
    calculated_score = Column(Float, nullable=False)
    criteria_scores = Column(JSON, nullable=False)
    fillers_detected = Column(JSON, nullable=False, default=list)
    strengths = Column(JSON, nullable=False, default=list)
    improvements = Column(JSON, nullable=False, default=list)
    improved_answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    session = relationship("InterviewSession", back_populates="analysis_results")
    question_answer = relationship("QuestionAnswer", back_populates="analysis_result")
