# models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ProcessedText(Base):
    __tablename__ = "processed_texts"

    id                = Column(Integer, primary_key=True, index=True)
    speaker           = Column(String, nullable=True)     # 누구 이야기인지
    original_text     = Column(String)
    standardized_text = Column(String)
    cleaned_text      = Column(String)
    summary_text      = Column(String)

class SummaryNote(Base):
    __tablename__ = "summary_notes"

    id = Column(Integer, primary_key=True, index=True)
    sum_title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
