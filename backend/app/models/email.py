from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    gmail_id = Column(String, unique=True, index=True, nullable=False)
    thread_id = Column(String, index=True, nullable=False)

    subject = Column(String, nullable=True)
    sender = Column(String, nullable=True)
    snippet = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    received_at = Column(String, nullable=True)   # raw Gmail date header for now
    labels = Column(JSON, nullable=True)

    # Fields for Phases 5–8 — nullable now, filled in later
    category = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    has_action_item = Column(String, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)

    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="emails")