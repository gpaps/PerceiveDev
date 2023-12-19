from pydantic import BaseModel, validator
from .roles import UserRole


class User(BaseModel):
    username: str
    password: str

    # @validator('password')
    # def password_length_validator(cls, v):
    #     if not (8 <= len(v) <= 64):
    #         raise ValueError('Password must be between 8 and 64 characters')
    #     return v


class UserInDB(User):
    hashed_password: str
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str
