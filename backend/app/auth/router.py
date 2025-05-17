from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from datetime import datetime, timedelta
import re
import random
import string

from app.db.session import get_session
from app.models.verification import VerificationCode
from app.schemas.user import UserAuthRequest, UserVerifyRequest
from app.auth.service import verify_code_and_get_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["auth"])

def is_phone_number(login: str) -> bool:
    """Check if the input is a phone number."""
    phone_pattern = r"^\+998\d{9}$"  # Matches +998901234567
    return bool(re.match(phone_pattern, login))

def is_valid_email(email: str) -> bool:
    """Check if the input is a valid email."""

    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(email_pattern, email))


def generate_code(length: int = 6) -> str:
    """Generate a random verification code of given length."""
    return ''.join(random.choices(string.digits, k=length))

@router.post("/request-code")
async def request_code(auth_data: UserAuthRequest, session: Session = Depends(get_session)):
    """Request a verification code for login (phone or email)."""
    login = auth_data.login.strip()

    # Validate login
    if not (is_phone_number(login) or is_valid_email(login)):
        raise HTTPException(status_code=400, detail="Invalid phone number or email")

    # Generate a verification code
    code = generate_code()

    # Set expiry (2 minutes from now)
    expires_at = datetime.utcnow() + timedelta(minutes=2)

    # Store in DB
    verification = VerificationCode(
        login=login,
        code=code,
        expires_at=expires_at
    )
    session.add(verification)
    session.commit()
    session.refresh(verification)

    # Mock sending the code (print to console for now)
    print(f"Sending code {code} to {login} via {'SMS' if is_phone_number(login) else 'Email'}")

    return {"message": "Verification code sent"}


@router.post("/verify-code")
async def verify_code(verify_data: UserVerifyRequest, session: Session = Depends(get_session)):
    """Verify the code and return a JWT token."""
    user = verify_code_and_get_user(verify_data.login, verify_data.code, session)
    
    # Generate JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.login, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "login": user.login,
            "role": user.role.value
        }
    }