from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegistrationRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str) -> str:
        return " ".join(value.split())


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    user: UserResponse
