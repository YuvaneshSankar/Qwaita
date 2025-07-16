from fastapi import FastAPI
from prisma import Prisma


app=FastAPI()
db=Prisma()

@app.get("/")
def header():
    return {"message":"Hi there"}