import os

import redis
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import SessionLocal, engine
from app.entities import NewUser, Settings, User

models.Base.metadata.create_all(bind=engine)

redis_conn = redis.Redis.from_url(os.environ['AUTH_BROKER_URI'])

app = FastAPI()

# origins = [
#     "http://localhost",
#     "http://localhost:3000",
#     "http://0.0.0.0:3000",
#     "http://0.0.0.0"
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JWTException(Exception):
    ...


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# callback to get your configuration
@AuthJWT.load_config
def get_config():
    return Settings()


@AuthJWT.token_in_denylist_loader
def check_if_token_in_denylist(decrypted_token):
    jti = decrypted_token['jti']
    entry = redis_conn.get(jti)
    return entry and entry.decode('utf-8') == 'true'


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


def get_userid(authorize: AuthJWT) -> str:
    try:
        authorize.jwt_required()
        return authorize.get_jwt_subject()
    except Exception as e:
        JWTException(e)


@app.post('/register/')
async def create_user(user: NewUser, db: Session = Depends(get_db)) -> dict:
    if models.get(db, user.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='This name already exists')
    new_user = models.create(db, user)
    return {'id': new_user.id}


@app.post('/login/')
def login(user: User, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    user = models.get(db, user.username, user.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    access_token = Authorize.create_access_token(subject=str(user.id))
    return JSONResponse(headers={'Authorization': f'Bearer {access_token}',
                                 'Access-Control-Expose-Headers': 'authorization'})


@app.get('/auth/')
def auth(Authorize: AuthJWT = Depends()):
    if user_id := get_userid(Authorize):
        return JSONResponse(headers={'X-User': user_id})
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@app.post('/logout/')
async def logout(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    jti = Authorize.get_raw_jwt()['jti']
    redis_conn.setex(jti, Settings().access_expires, 'true')
