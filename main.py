from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def index():
    return {'data':{'name':'minal'}}

@app.get('/about')
def about():
    return {'data':'about page'}