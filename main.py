from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import models
from sqlalchemy.orm import Session
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine) #create all tables

templates = Jinja2Templates(directory="templates")

app = FastAPI()

@app.get("/")
def dashboard(request: Request):
	""" for homepage i.e dashboard """
	
	context = {
		"request": request
	}
	return templates.TemplateResponse("dashboard.html", context)



@app.post("/stock")
def create_stock():
	""" adds stocks to db """
	
	return {"something": None}
	
	
