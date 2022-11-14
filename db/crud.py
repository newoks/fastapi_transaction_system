from sqlalchemy.orm import Session

from . import models


def get_users(pg_session: Session, skip: int = 0, limit: int = 100):
    return pg_session.query(models.User).offset(skip).limit(limit).all()


def get_balance(pg_session: Session, user_id: int) -> models.Balance:
    return pg_session.query(models.Balance).filter(models.Balance.user_id == user_id).order_by(models.Balance.id.desc()).first()