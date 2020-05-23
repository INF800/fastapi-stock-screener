from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
import models
from models import Stock
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from pydantic import BaseModel
import yfinance as yf

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

# background task
def fetch_stock_data(pk: int):
	db = SessionLocal() #new session create
	stock = db.query(Stock).filter(Stock.id==pk).first() # find stock using pk id. Note `Stock` used not `stock`
	
	# yf.Ticker returns dict of lots of key-vakue pairs. we take only necessary.
	# check pypi docs for yf
	
	yahoo_data = yf.Ticker(stock.symbol)
	
	stock.ma200 = yahoo_data.info['twoHundredDayAverage']
	stock.ma50 = yahoo_data.info['fiftyDayAverage']
	stock.price = yahoo_data.info['previousClose']
	stock.forward_pe = yahoo_data.info['forwardPE']
	stock.forward_eps = yahoo_data.info['forwardEps']
	if yahoo_data.info['dividendYield'] is not None:
		stock.dividend_yield = yahoo_data.info['dividendYield'] * 100
	
	#save
	db.add(stock)
	db.commit()


#--- routes & funcs ---#


@app.get("/")
def dashboard(request: Request, forward_pe=None, ma50=None, ma200=None , db: Session = Depends(get_db)): #note db session added
	""" for homepage i.e dashboard """
	
	# get all stocks as dict
	#stocks = db.query(Stock).all()
	# instead of selecting all as above, 
	# we will filter based on query params
	stocks = db.query(Stock)
	
	if forward_pe:
		stocks = stocks.filter(Stock.forward_pe < forward_pe)
	if ma50:
		stocks = stocks.filter(Stock.price > Stock.ma50) #note Stock.ma50 not just `ma50` 
	if ma200:
		stocks = stocks.filter(Stock.price > Stock.ma200)
	
	
	# return the dict
	context = {
		"request": request,
		"stocks": stocks,
		
		# query params
		"forward_pe": forward_pe,
		"ma50": ma50,
		"ma200": ma200
	}
	
	return templates.TemplateResponse("dashboard.html", context)
	
	

@app.post("/stock")
def create_stock(stock_req: StockRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
	""" adds stocks to db """
	stock = Stock()
	stock.symbol = stock_req.symbol
	
	db.add(stock)
	db.commit()
	
	background_tasks.add_task(fetch_stock_data, stock.id)
	
	return {"staus": "ok"}
	
@app.delete("/stock")
def delete_stock(stock_req: StockRequest, db: Session = Depends(get_db)):
	""" deletes stock record of a symbol """
	
	if not stock_req.symbol == "DELETEALL":
		stock_to_dlt = db.query(Stock).filter(Stock.symbol==stock_req.symbol).first()
		db.delete(stock_to_dlt)
		db.commit()
	else:
		db.query(Stock).delete() # delete all
		db.commit()
	
