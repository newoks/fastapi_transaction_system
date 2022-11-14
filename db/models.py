from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)

    balance = relationship('Balance', back_populates='user')


class Balance(Base):
    __tablename__ = 'balance'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    value = Column(Integer)
    updated_at = Column(DateTime, default=datetime.now)

    user = relationship('User', back_populates='balance')