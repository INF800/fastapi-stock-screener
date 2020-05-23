- create `virtualenv`
- add gitignore
- install from req.txt
- test helloworld
- run using `uvicorn main-file:app-name` use `--reload` in dev envt or use executable `run`

### 1. UI Skeleton

- render template for list of stocks
- endpoint to add stock to db.

**main.py**
```
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def dashboard():
	""" for homepage i.e dashboard """
	
	return "home" #will return template later



@app.post("/stock")
def create_stock():
	""" adds stocks to db """
	
	return {"something": None}
	
```

- test using /docs
- render template using jinja2. can do the same with js frameworks
	- create `templates` in main dir and inside it,
		- `dashboard.html` 
		- `layout` (dashboard will br injected here)
	- tell fastapi where our templates are
		```
		from fastapi import Request
		from fastapi.templating import Jinja2Templates
		templates = Jinja2Templates(directory="templates")
		
		...
		
		
		def somefunc(request: Request):
			context = { #Note: context is not optional while returning template
				"request": request
				"var1": 123
			}
			return templates.TemplateResponse("dashboard.html", context)
		```
		```
		<!-- use context in html using -->
		{{ var 1 }}
		```

*layout.html*
```
<html>
	
	<head>
		<title> Dashboard </title>
	<head>
	
	<body>
		<h2> Dashboard </h2>
		
		{% block content %}
		{% endblock %}
		
	</body>
</html>
```
*dashboard.html*:
```
{% extends "layout.html" %}

{% block content %}
<p> injected successfully! </p>
{% endblock %}
```
*main.html*
```
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

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
```

- beautify html with css if wanted (I am not doing it)

- Add table in *dashboard.html*
```
{% extends "layout.html" %}

{% block content %}

<div>
	<!-- for fiktering -->
	<input type="text" placeholder="P/E"/>
	<input type="text" placeholder="Div Yield" />
	<input type="checkbox"> <label> Above 50 day </label>
	<input type="checkbox"> <label> Above 200 day </label>
	<button> Filter </button>
</div>

<div>
	<table>
		<thead>
			<tr>
				<th>Symbol</th>
				<th>P/E</th>
				<th>Dividend Yield</th>
			</tr>
		</thead>
		<tbody>
			<tr>
				<td>val1</td>
				<td>val2</td>
				<td>val3</td>
			</tr>
			<tr>
				<td>val4</td>
				<td>val5</td>
				<td>val6</td>
			</tr>
		</tbody>
	</table>
</div>

{% endblock %}
```


### 2. setup database

- sqlite with sqlalchemy for orm
- check FastAPI sql docs
- create new file `database.py` in main directory 

*database.py*: copy from (docs here)[https://fastapi.tiangolo.com/tutorial/sql-databases/]
```
# import engine, base and a session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# .db file created by itself
SQLALCHEMY_DATABASE_URL = "sqlite:///./stocks.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# intermediate for conn and db for querying and all
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```
- create models.py (same from docs - sqlalchemy models)

*models.py**:
```
from sqlalchemy import Column, Integer, String, Numeric
#from sqlalchemy.orm import relationship
# dont need relationships as we will have only one table

from .database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    price = Column(Numeric(10,2)) # 10 digits before and 2 after dec point
		forward_pe = Column(Numeric(10,2)) # be wary of floating calc errors
		forward_eps = Column(Numeric(10,2))
		ma50 = Column(Numeric(10,2))
		ma200 = Column(Numeric(10,2)) 
```

- Note `.database` you can remove `.` by declaring entire dir as *python pkg* by
	- create empty `__init__.py` in main dir

- **create table**

tell sqlalchemy to create all tables

*main.py*:
```
...

import models
from sqlalchemy.orm import Session
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine) #creates tables
# stocks db will appear once you run uvicorn

app = ...
```

- check sqlite db if table is created or not
```
// get into db
$ sqlite3 stocks.db

// view schema for created table(s)
sqlite> .schema

...

// can `select * from table-name`
// can `insert into table-name (col-name) values ('col-value');`
sqlite> insert into stocks (symbol) values ('AAPL');
sqlite> select * from stocks

...

// can delete using
sqlie> delete from stocks
```
we will be adding the details using form

### 3. api interact with db

- wire them all together. we will dive deeper into fastapi
- 3 main features
	- pydantic - define structure of http requests
	- dependency injection - to make sure we have db conn
	- backgrounf tasks - fetch data in bg from yfinance

**i. stock post request**

- get stock symbol from endpoint, and insert into db.
- we need String (Use pydantic for the req.)

*main.py*:
```
...

from pydantic import BaseModel

...

class StockRequest(BaseModel):
	symbol: str
	
...

@app.post("/stock")
def create_stock(stock_req: StockRequest):
	return {"test": "SUCCESS"}
```

test it using expected post req `{"symbol": "AAPL"}` and unexpected in `/docs` "try it out"

*ii. dependency injection*

- to make sure we have conn to db befor create_stock func or any func executes

**main.py**
```
from fastapi import Depends

...

def get_db():
	""" returns db session """
	
	try:
		db = SessionLocal()
		yield db
	finally:
		db.close

...

# our endpoints (funcs) that use db must get db as ref
# note: always put Depends at end of func signature. 

@app.post("/stock")
def create_stock(stock_req: Request, db: Session = Depends(get_db)):
	
	...
```
Now, you can use sqlalchemy using db "session"
```
from models import Stock

...

@app.post("/stock")
def create_stock(StockRequest: Request, db: Session = Depends(get_db)):
	
	# instantiate model table and fill
	stock = Stock()
	stock.symbol = stock_req.symbol
	
	#add to db
	db.add(stock)
	db.commit()
```

- test using `{"symbol": "xyz"}` and check in sqlite `select * from stocks`. 

Delete everything inside stocks table once you know everything is working. (avoids integrity errors and more).

- Note that `stock` is not json. cannot return it.

**iii. Fetch from yfinance**

- background tasks
- use `async` keyword for *main func*

*main.py*
```
from fastapi import BackgroundTasks

...

# define bg func (regular one)
def fetch_stock_data(pk: int):
	pass

...

# add to func signature
# define when to kick start bg task (after adding to records)
# note `async`
@app.post('/stock')
async def create_stock(stock_req: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
	
	...
	
	db.commit() # added to db
	
	background_tasks.add_task(fetch_stock_data, stock.id) # pk is id of `stock` just inserted. Note we pass pk not to actual bg func 
```

Let's define the bg func
```
def fetch_stock_data(pk: int):
	db = SessionLocal() #new session create
	stock = db.query(Stock).filter(Stock.id==pk).first() # find stock using pk id. Note `Stock` used not `stock`
	
	#test with dummy values
	stock.forward_pe = "123"
	
	#save
	db.add(stock)
	db.commit()
```
check in sqlite after sending `{"symbol": "xyz"}`

Real data
```
import yfinance as yf

...

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
```

> apt install python3-lxml 

- check db


table values for different requests. note "fb" instead of "FB" raises some error 
but uvicorn reloads and db is populated
```
1|AAPL|316.85|21.571623|14.73|288.25687|285.28754
2|test|||||                                                
3|fb|231.39|23.879713|9.81|192.61858|195.6634
4|FB|231.39|23.874617|9.81|192.61858|195.6634
```
**Note:** If you send json request for same stock symbol more than 1 time, we will have error as it wont be unique.

### 4. wire up ui

- simple form post as in django responseapi didnt work!

**i. POST data through api using feild tobadd into db**

	- using jquery ajax, check commit `post using js, jquery done` `635b8249d6b756142798bf25578397f3f33c5f8a`
		
	- using axios, first see ajax command then check commit `post using axios` `ba7db0876a4060dc30178780232342812c5446a0`

**ii. Display ALL updated db records in dashboard**

*main.py*: (dashboard endpoint)
```
@app.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)): #note db session added
	
	# get all stocks as dict
	stocks = db.query(Stock).all()
	
	# return the dict
	context = {
		"request': request,
		"stocks": stocks
	}
	
	return templates.TemplateResponse("dashboard.html", context)
```
check in dashboard.html using `{{ stocks }}`

*dashboard.html*:
```
			{% for record_col in stocks %}
			<tr>
				<td>{{ record_col.symbol }}</td>
				<td>{{ record_col.price }}</td>
				<td>{{ record_col.ma50 }}</td>
				<td>{{ record_col.ma200 }}</td>
				
				...
				
			</tr>
			{% endfor %}
```

**iii. add delete stock button**

- same endpoint can be used

*main.py*:
```
@app.delete("/stock") # Note same endpoint can be used!
def delete_stock(stock_req: StockRequest, db: Session = Depends(get_db)):
	""" deletes stock record of a symbol """
	
	stock_to_dlt = db.query(Stock).filter(Stock.symbol==stock_req.symbol).first() 
	db.delete(stock_to_dlt)
	db.commit()
```
test using `docs` with `{"symbol": "JNJ"}`

- send DELETE request to API just like we did for POST using ajax or axios (i used axios)
- check commit `delete button added` `1c4c9aa953d7b4cf53356dbfcb55e2edc7e20005`
- check commit `DELETE ALL button added` `7d0a229563cefd127b9275f5b41c620b8b87a219`

**iv. Filter**

- use GET request in dashboard with *query params* (Note query params and requests arr entirely different)
- to get `/?` with `&` in `http://localhost:8000/` so that we can pass *Query params*
	- get route
```
@app.get("/")
def dashboard(request: Request, forward_eps=None, forward_pe=None, db: Session = Depends(get_db)): #note db session added
	""" for homepage i.e dashboard """
	
	# get all stocks as dict
	#stocks = db.query(Stock).all()
	# instead of selecting all as above, 
	# we will filter based on query params
	stocks = db.query(Stock)
	
	# filter
	if forward_pe:
		stocks = stocks.filter(Stock.forward_pe < forward_pe)
	if forward_eps:
		stocks = stocks.filter(Stock.forward_eps < forward_eps)
	
	
	# return the dict stocks
	context = {
		"request": request,
		"stocks": stocks # it will be looped in dashboard.html
	}
	
	return templates.TemplateResponse("dashboard.html", context)
```
	- make a form with `form` `name="query-key"` 
	- and most importantly `<input type="submit" ...>` not `type="button"`
		```
		<form> <!--no method or action used-->
			<input type="text" name="forward_pe"> <!--name coresponds yo key-->
			<input type="submit" value="click me">
		</form>
		```
		It makes url field
		```
		http://localhost:8000/http://localhost:8000/?forward_pe=44&forward_eps=22
		```
	- to retain the entered values,
		- send the querys through `context` and put a `if` condition in text field
			```
			context = {
				...
				"forward_pe": forward_pe
			}
			```
			```
			<input type="text" name="forward_pe" placeholder="P/E" {% if forward_pe %} value={{forward_pe}} {% endif %} />
			or
			<input type="checkbox" name="ma200" {% if ma200 %} checked {% endif %}> <label> Above 200 day </label>
			```

- add the code to `dashboard.html` and `main.py`
	- commit `filter done` `0c148e1ae2ea26fcb3e22224e4ad7c207b51802d`


## HEROKU DEPLOYMENT

- add `runtime.txt` with `python-3.8.3` inside (specifis versions avl. in heroku)
- add `gunicorn==20.0.4` to `requirements.txt`
- crrate `Procfile` with `web: gunicorn -k uvicorn.workers.UvicornWorker main:app`

> heroku isn't working with requirements.txt as expected. Add `pip freeze > "requirements.txt"` and add `gunicorn==20.0.4` in ot as well. Only one long-term solution - use docker! api is compleyely fine yfinance is what causing issues.

All set!


## INTERESTING ARTICLE (File arrangement)

- https://medium.com/analytics-vidhya/building-a-rest-api-using-python-fastapi-and-heroku-b7e9341f578
- add sessions