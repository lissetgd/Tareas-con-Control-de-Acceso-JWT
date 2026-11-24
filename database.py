# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Reemplaza esta URL con tu connection string de Neon (o usa variables de entorno)
# Ejemplo: "postgresql://usuario:password@ep-cool-cloud-123456.us-east-2.aws.neon.tech/neondb?sslmode=require"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_1nERxY4eLdlu@ep-solitary-band-b53pq362-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependencia para obtener la sesión de base de datos en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
