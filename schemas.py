# schemas.py
from pydantic import BaseModel
from typing import Optional

class TareaBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    completada: Optional[bool] = False

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    completada: Optional[bool] = None

class TareaResponse(TareaBase):
    id: int

    class Config:
        from_attributes = True

# Agrega la clase UserCreate para la creación de usuarios
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str