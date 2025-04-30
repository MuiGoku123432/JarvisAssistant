# db.py
from sqlalchemy import (
    create_engine, Column, Integer, Text, Boolean, JSON, TIMESTAMP, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
import os

# Pull your DB URL from env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:crf2122006@localhost:5432/jarvis"
)

engine  = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base    = declarative_base()

class Conversation(Base):
    __tablename__ = "conversation_history"
    id         = Column(Integer, primary_key=True)
    role       = Column(Text, nullable=False)
    message    = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    embedding  = Column(Vector(384))

class Project(Base):
    __tablename__ = "projects"
    id          = Column(Integer, primary_key=True)
    name        = Column(Text, nullable=False)
    description = Column(Text)
    proj_meta   = Column('metadata', JSON)                 # renamed attr
    created_at  = Column(TIMESTAMP(timezone=True), server_default=func.now())

class FileIndex(Base):
    __tablename__ = "file_index"
    id         = Column(Integer, primary_key=True)
    path       = Column(Text, unique=True, nullable=False)
    is_dir     = Column(Boolean, nullable=False)
    file_meta  = Column('metadata', JSON)                  # renamed attr
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class WatchedRoot(Base):
    __tablename__ = "watched_roots"
    id       = Column(Integer, primary_key=True)
    root     = Column(Text, unique=True, nullable=False)
    added_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

Base.metadata.create_all(engine)
