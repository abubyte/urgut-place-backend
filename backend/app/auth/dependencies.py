from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os

from app.models.user import UserRole

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/verify-code")

class TokenData(BaseModel):
    login: str
    role: UserRole

def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Decode JWT and return user data."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        role: str = payload.get("role")
        if login is None or role is None:
            raise credentials_exception
        token_data = TokenData(login=login, role=UserRole(role))
    except JWTError:
        raise credentials_exception
    return token_data

def get_admin_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Ensure the user is an admin."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for non-admin users"
        )
    return current_user