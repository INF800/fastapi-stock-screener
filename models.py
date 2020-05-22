from sqlalchemy import Column, Integer, String, Numeric
from database import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    price = Column(Numeric(10,2)) # 10 digits before and 2 after dec point
    forward_pe = Column(Numeric(10,2)) # be wary of floating calc errors
    forward_eps = Column(Numeric(10,2))
    ma50 = Column(Numeric(10,2))
    ma200 = Column(Numeric(10,2)) 