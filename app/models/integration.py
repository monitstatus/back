from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Integration(Base):
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    kind = Column(String)
    owner_id = Column(Integer, ForeignKey("user.id"))

    # slack
    slack_bot_token = Column(String)
    slack_channel = Column(String)
    slack_incoming_webhook = Column(String)
    slack_team_name = Column(String)

    # telegram
    telegram_random_string = Column(String)
    telegram_chat_id = Column(String)
    telegram_chat_name = Column(String)

    owner = relationship("User", back_populates="integrations")
