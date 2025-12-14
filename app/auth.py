import datetime

import bcrypt
from fastapi import Depends, HTTPException, status
import jwt
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_user_by_name
from app.database.db import get_session
from app.models import UserResponse

SECRET_KEY='mysecretkey'
ALGORITHM='HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=2


oauth2_scheme=OAuth2PasswordBearer(tokenUrl='token')

def get_password_hash(password: str):
    salt=bcrypt.gensalt()
    hashed=bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(normal_password: str, hashed_password: str):
    return bcrypt.checkpw(normal_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_token(data: dict):
    to_encode=data.copy()
    expire=datetime.datetime.now()+datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    except PyJWTError:
        return None

async def get_current_user(token: str= Depends(oauth2_scheme), db: AsyncSession=Depends(get_session)):
    payload=await verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не авторизован')

    name: str=payload.get('sub')
    if name is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не авторизован')

    user=await get_user_by_name(name, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не авторизован')


    return UserResponse.model_validate(user)

async def authentificate_user(session:AsyncSession, name:str, password:str):
    user=await get_user_by_name(name, session)

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return UserResponse.model_validate(user)



