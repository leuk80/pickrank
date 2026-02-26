from pydantic import BaseModel, EmailStr


class SubscriptionCreate(BaseModel):
    email: EmailStr
    language: str = "de"


class SubscriptionResponse(BaseModel):
    message: str
    email: str
