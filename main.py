from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
import models
from models import Stock
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from pydantic import BaseModel

app = FastAPI()

models.Base.metadata.create_all(bind=engine) #create all tables

templates = Jinja2Templates(directory="templates")

# for POST request at "/stock"
class StockRequest(BaseModel):
	symbol: str #note static data members

# for dependency injection
def get_db():
	""" returns db session """
	try:
		db = SessionLocal()
		yield db
	finally:
		db.close


#--- routes & funcs ---#

@app.get("/")
def dashboard(request: Request):
	""" for homepage i.e dashboard """
	
	context = {
		"request": request
	}
	return templates.TemplateResponse("dashboard.html", context)


@app.post("/stock")
def create_stock(stock_req: StockRequest, db: Session = Depends(get_db)):
	""" adds stocks to db """
	stock = Stock()
	stock.symbol = stock_req.symbol
	
	db.add(stock)
	db.commit()
	
	print(stock)
	return {"status": stock}
	
	
