from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker
from sqlalchemy import create_engine, Enum
import uuid
import os
from dotenv import load_dotenv
import enum
from datetime import datetime

# Cargar variables de entorno
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuración de base de datos
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class UserRole(enum.Enum):
    alumno = "alumno"
    monitor = "monitor"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Tabla: room_names (catálogo de nombres)
class RoomName(Base):
    __tablename__ = 'room_names'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

# Tabla: room_sessions
class RoomSession(Base):
    __tablename__ = 'room_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_name = Column(Text, nullable=False)
    topic = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Tabla: messages
class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    room_session_id = Column(UUID(as_uuid=True), ForeignKey('room_sessions.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AgentPrompt(Base):
    __tablename__ = 'agent_prompts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)





def create_room_name(name: str) -> int:
    session = Session()
    try:
        nuevo_nombre = RoomName(name=name)
        session.add(nuevo_nombre)
        session.commit()
        session.refresh(nuevo_nombre)
        return nuevo_nombre.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        
def insert_message(room_session_id: str, user_id: str, content: str) :
    session = Session()
    try:
        nuevo_mensaje = Message(
            room_session_id=room_session_id,
            user_id=user_id,
            content=content
        )
        session.add(nuevo_mensaje)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def create_room_session(room_name: str, topic: str = None) -> str:
    session = Session()
    try:
        nueva_sesion = RoomSession(room_name=room_name, topic=topic)
        session.add(nueva_sesion)
        session.commit()
        session.refresh(nueva_sesion)
        return str(nueva_sesion.id)
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()