from pydantic import BaseModel
from .roles import UserRole


class User(BaseModel):
    username: str
    password: str


class UserInDB(User):
    hashed_password: str
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str
