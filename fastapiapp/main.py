from fastapi import FastAPI, Depends, status, HTTPException
from blog import schemas
from typing import List
from blog import models
from blog.database import engine, SessionLocal
from sqlalchemy.orm import Session, relationship
from blog.hashing import Hash
from datetime import timedelta
from blog.token import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from blog import oauth
from fastapi.security import OAuth2PasswordRequestForm



app = FastAPI()

models.Base.metadata.create_all(engine)

#Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post('/blog', status_code=status.HTTP_201_CREATED, tags=["blogs"])
def create(request: schemas.Blog, db: Session = Depends(get_db)):
    new_blog = models.Blog(title=request.title, body=request.body, user_id=1)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

@app.get('/blog', response_model=List[schemas.ShowBlog], tags=["blogs"])
def all(db: Session = Depends(get_db), get_current_user: schemas.User= Depends(oauth.get_current_user)):
    blogs = db.query(models.Blog).all()
    return blogs

@app.get('/blog/{id}', status_code = status.HTTP_200_OK, response_model=schemas.ShowBlog, tags=["blogs"])
def show(id: int, db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if blog is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, 
                            detail=f'Blog with id {id} is not available')
    return blog

@app.delete('/blog/{id}', status_code=status.HTTP_204_NO_CONTENT, tags=["blogs"])
def destroy(id: int,  db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    if not blog.first():
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, 
                            detail=f'Blog with id {id} is not found')
    blog.delete(synchronize_session=False)
    db.commit()
    return "deleted"

@app.put('/blog/{id}', status_code=status.HTTP_202_ACCEPTED, tags=["blogs"])
def update(id: int, request: schemas.Blog,  db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    if not blog.first():
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, 
                            detail=f'Blog with id {id} is not found')
    blog.update({'title':request.title, 'body':request.body})
    db.commit()
    return 'updated'


@app.post('/user', response_model=schemas.ShowUser, tags=["users"])
def create_user(request: schemas.User, db: Session = Depends(get_db)):
    new_user = models.User(name=request.name, email=request.email,password=Hash.bcrypt(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# @app.post('/blog')
# def create(y\title, body):
#     return {'title':title, 'body':body}

@app.get('/user/{id}', response_model=schemas.ShowUser, tags=["users"])
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, 
                            detail=f'User with id {id} is not found')
    return user

@app.post('/login', status_code=status.HTTP_202_ACCEPTED, tags=["Authentication"])
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.username).first()
    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, 
                            detail=f'Invalid Credentials')
    if not Hash.verify(user.password, request.password):
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, 
                            detail=f'Incorrect password')
    
    # access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
    data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}
