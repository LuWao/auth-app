from fastapi_sqlalchemy.middleware import Session
from sqlalchemy import Column, Integer, String

from .database import Base
from .entities import NewUser


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)


def create(session: Session, user_data: NewUser) -> User:
    user = User(
        name=user_data.username,
        password=user_data.password,
        first_name=user_data.firstName,
        last_name=user_data.lastName,
        email=user_data.email,
        phone=user_data.phone
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get(session: Session, username: str, password: str = None) -> User:
    qr = session.query(User).filter(User.name == username)
    if password:
        qr = qr.filter(User.password == password)
    return qr.first()
