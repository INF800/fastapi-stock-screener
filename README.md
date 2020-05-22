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