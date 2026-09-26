"""Contratos HTTP mínimos de autenticação."""
from pydantic import BaseModel, ConfigDict

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    password: str

class AuthenticatedUser(BaseModel):
    id: int
    name: str
    email: str
    currency: str

class AuthSessionResponse(BaseModel):
    user: AuthenticatedUser
    csrf_token: str

class LogoutResponse(BaseModel):
    authenticated: bool = False
