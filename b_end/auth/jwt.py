from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from decouple import config

# Import User models
from .models import User, UserInDB

# Import user roles
from .roles import UserRole

SECRET_KEY = config('JWT_SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#TODO
# Mock database for user details
users_db = {
    "tester": {
        "username": "tester",
        "hashed_password": pwd_context.hash("password123"),
        "role": UserRole.ADMIN
    }
}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db, username: str):
    user_dict = db.get(username)
    if user_dict:
        return UserInDB(username=user_dict["username"],
                        hashed_password=user_dict["hashed_password"],
                        password="dummy",
                        role=user_dict["role"]
                        )
    return UserInDB(**user_dict) if user_dict else None



def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
