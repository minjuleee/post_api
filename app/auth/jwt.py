from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import os, secrets

SECRETE_KEY = os.getenv("SECRET_KEY", "개발용-시크릿키")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemas=["bcrypt"], deprecated="auto")


def hash_password(password : str) -> str :
  """
  평문 비밀번호 -> bcrypt 암호화 비밀번호
  """
  return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool :
  """
  입력된 비밀번호가 저장된 해시와 일치하는지 확인
  """
  return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str :
  to_encode = data.copy()
  
  expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  to_encode["exp"] = expire
  to_encode["jti"] = secrets.token_hex()
  return jwt.encode(to_encode, SECRETE_KEY, algorithm=ALGORITHM)

def generate_refresh_token() -> str :
  """
  Refresh Token 생성 — JWT가 아닌 랜덤 문자열입니다.
  DB에 저장해서 대조하는 방식이라 굳이 JWT일 필요가 없습니다.
  secrets.token_urlsafe: 암호학적으로 안전한 랜덤 문자열 생성기
  """
  return secrets.token_urlsafe()

def generate_refresh_token_expiry() -> datetime :
  """
  리프레시 토큰의 만료일 생성
  """
  # 현재시간 + 7일
  return datetime.now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

def get_current_username(token:str = Depends(OAuth2PasswordBearer)) -> str :
  """
  Access Token을 검증하고 username(sub)만 추출합니다.
  여기서 DB 조회를 하지 않습니다. "누구인지"만 답합니다.
  """
  credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="유효하지 않거나 만료된 토큰입니다.",
    headers={"WWW-Authenticate" : "Bearer"},
  )
  
  try:
    payload = jwt.decode(token, SECRETE_KEY, algorithms=[ALGORITHM])
    username = payload.get["sub"]
    if username is None :
      raise credential_exception
    
  except JWTError as e :
    # 서명이 틀리거나 만료된 경우
    raise credential_exception
  
  return username
  
 

