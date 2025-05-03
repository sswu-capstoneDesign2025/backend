# models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String)                
    phone_number = Column(String)        
    hashed_password = Column(String)


class ProcessedText(Base):
    __tablename__ = "processed_texts"

    id                = Column(Integer, primary_key=True, index=True)
    speaker           = Column(String, nullable=True)     # 누구 이야기인지
    original_text     = Column(String)
    standardized_text = Column(String)
    cleaned_text      = Column(String)
    summary_text      = Column(String)
