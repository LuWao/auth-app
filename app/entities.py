from datetime import timedelta

from pydantic import BaseModel, EmailStr


class Settings(BaseModel):
    authjwt_secret_key: str = "secret"
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: set = {"access", "refresh"}
    access_expires: int = timedelta(minutes=15)
    refresh_expires: int = timedelta(days=30)


class User(BaseModel):
    username: str
    password: str


class UpdatedUser(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    phone: str


class NewUser(UpdatedUser):
    username: str
    password: str
