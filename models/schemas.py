from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BalanceBase(BaseModel):
    updated_at: Optional[datetime]


class BalanceUpdate(BalanceBase):
    pass


class Balance(BalanceBase):
    id: Optional[int]
    user_id: Optional[int]
    value: Optional[int]

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    name: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    is_active: bool
    balance: list[Balance] = []

    class Config:
        orm_mode = True