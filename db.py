from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase

URL_DATABASE = 'postgresql://postgres:123@localhost:5432/Tennis_Sofa'

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    pass
