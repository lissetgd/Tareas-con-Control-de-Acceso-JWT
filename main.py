# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas
from database import engine, get_db
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import jwt

# Configuración de JWT
SECRET_KEY = "clave_secreta_super_segura_para_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Funciones auxiliares para generar y validar tokens
def crear_token_acceso(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def obtener_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    usuario = db.query(models.User).filter(models.User.username == username).first()
    if usuario is None:
        raise credentials_exception
    return usuario

# Crear las tablas en Neon automáticamente (si no existen)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRUD FastAPI con Neon DB y JWT", version="1.0")

from fastapi.middleware.cors import CORSMiddleware

# ... (después de crear app = FastAPI(...))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite solicitudes desde cualquier origen (ideal para desarrollo local)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Permite todos los headers (incluyendo Authorization para el token JWT)
)

# 1. CREATE (Crear un elemento - Protegido con JWT)
@app.post("/tareas/", response_model=schemas.TareaResponse, status_code=status.HTTP_201_CREATED)
def crear_tarea(
    tarea: schemas.TareaCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(obtener_usuario_actual)
):
    nueva_tarea = models.Tarea(
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        completada=tarea.completada
    )
    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    return nueva_tarea

# 2. READ (Consultar todos los elementos - Protegido con JWT)
@app.get("/tareas/", response_model=list[schemas.TareaResponse])
def obtener_tareas(
    skip: int = 0, 
    limit: int = 10, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(obtener_usuario_actual)
):
    tareas = db.query(models.Tarea).offset(skip).limit(limit).all()
    return tareas

# 2. READ (Consultar un solo elemento por ID - Protegido con JWT)
@app.get("/tareas/{tarea_id}", response_model=schemas.TareaResponse)
def obtener_tarea(
    tarea_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(obtener_usuario_actual)
):
    tarea = db.query(models.Tarea).filter(models.Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea

# 3. UPDATE (Actualizar un elemento - Protegido con JWT)
@app.put("/tareas/{tarea_id}", response_model=schemas.TareaResponse)
def actualizar_tarea(
    tarea_id: int, 
    tarea_actualizada: schemas.TareaUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(obtener_usuario_actual)
):
    tarea_query = db.query(models.Tarea).filter(models.Tarea.id == tarea_id)
    tarea = tarea_query.first()
    
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    datos_actualizacion = tarea_actualizada.model_dump(exclude_unset=True)
    tarea_query.update(datos_actualizacion, synchronize_session=False)
    
    db.commit()
    db.refresh(tarea)
    return tarea

# 4. DELETE (Borrar un elemento - Protegido con JWT)
@app.delete("/tareas/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_tarea(
    tarea_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(obtener_usuario_actual)
):
    tarea = db.query(models.Tarea).filter(models.Tarea.id == tarea_id).first()
    
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    db.delete(tarea)
    db.commit()
    return None

# 5. REGISTER (Registrar nuevo usuario)
@app.post("/register", status_code=status.HTTP_201_CREATED)
def registrar_usuario(user: schemas.UserCreate, db: Session = Depends(get_db)):
    usuario_existente = db.query(models.User).filter(models.User.username == user.username).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    nuevo_usuario = models.User(username=user.username, password=user.password)
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return {"mensaje": "Usuario registrado exitosamente", "username": nuevo_usuario.username}

# 6. LOGIN (Iniciar sesión para obtener el Token JWT)
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not usuario or usuario.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = crear_token_acceso(data={"sub": usuario.username})
    return {"access_token": access_token, "token_type": "bearer"}