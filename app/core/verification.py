# import uuid
# import secrets
# import string
# from datetime import datetime, timedelta
# from typing import Optional, Dict, Any
# from sqlmodel import Session, select
# from app.models import User, VerificationCode
# from app.core.email import send_verification_email
# from app.core.config import settings
# import jwt

# # Constants
# ALGORITHM = "HS256"
# OTP_EXPIRY_MINUTES = 10

# def generate_otp() -> str:
#     """Generate a 6-digit OTP code for email verification"""
#     digits = string.digits
#     otp = ''.join(secrets.choice(digits) for _ in range(6))
#     return otp

# def create_verification_code(session: Session, user_id: uuid.UUID) -> VerificationCode:
#     """Create a new verification code for a user"""
#     # Delete any existing verification codes for this user
#     existing_codes = session.exec(
#         select(VerificationCode).where(VerificationCode.user_id == user_id, VerificationCode.is_used == False)
#     ).all()
    
#     for code in existing_codes:
#         session.delete(code)
    
#     # Create a new verification code
#     otp = generate_otp()
#     expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
#     verification_code = VerificationCode(
#         user_id=user_id,
#         code=otp,
#         expires_at=expires_at
#     )
    
#     session.add(verification_code)
#     session.commit()
#     session.refresh(verification_code)
    
#     return verification_code

# def verify_otp(session: Session, user_id: uuid.UUID, otp: str) -> bool:
#     """Verify if the provided OTP matches the stored OTP for the user"""
#     verification_code = session.exec(
#         select(VerificationCode).where(
#             VerificationCode.user_id == user_id,
#             VerificationCode.code == otp,
#             VerificationCode.is_used == False,
#             VerificationCode.expires_at > datetime.now()
#         )
#     ).first()
    
#     if verification_code:
#         # Mark the code as used
#         verification_code.is_used = True
#         session.add(verification_code)
#         session.commit()
        
#         # Mark the user as verified
#         user = session.get(User, user_id)
#         if user:
#             user.is_verified = True
#             session.add(user)
#             session.commit()
        
#         return True
    
#     return False

# def generate_verification_token(user_id: uuid.UUID) -> str:
#     """Generate a verification token for email verification link"""
#     expire = datetime.now() + timedelta(hours=24)
#     to_encode = {"exp": expire, "sub": str(user_id), "purpose": "email_verification"}
#     encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# def verify_token(session: Session, token: str) -> Optional[User]:
#     """Verify a token and return the user if valid"""
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("sub")
#         purpose = payload.get("purpose")
        
#         if not user_id or purpose != "email_verification":
#             return None
        
#         user = session.get(User, uuid.UUID(user_id))
#         if not user:
#             return None
        
#         # Mark the user as verified
#         user.is_verified = True
#         session.add(user)
#         session.commit()
        
#         return user
#     except jwt.PyJWTError:
#         return None

# def send_verification_email_to_user(session: Session, user: User, base_url: str) -> bool:
#     """Send a verification email to the user"""
#     # Create verification code
#     verification_code = create_verification_code(session, user.id)
    
#     # Generate verification link
#     verification_token = generate_verification_token(user.id)
#     verification_link = f"{base_url}/api/v1/users/verify-email?token={verification_token}"
    
#     # Send email
#     return send_verification_email(
#         email=user.email,
#         otp_code=verification_code.code,
#         verification_link=verification_link
#     )
