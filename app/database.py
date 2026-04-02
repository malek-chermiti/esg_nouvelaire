from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DB_USERNAME = "root"
DB_PASSWORD = "malek"
MYSQLHOST = "localhost"
MYSQLPORT = 3306

# MySQL connection URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{MYSQLHOST}:{MYSQLPORT}/esg_nouvelair"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Set to False in production
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
