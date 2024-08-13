from . import db

from flask_login import UserMixin
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Utente(db.Model, UserMixin):
    __tablename__ = "utenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[String] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
   
    proprietario: Mapped[Optional["Proprietario"]] = relationship(back_populates="utente") # -> qui ci va il nome del campo dell'altra classe

class Proprietario(db.Model):
    __tablename__ = "proprietari"

    id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), primary_key=True)
    stelle: Mapped[int] = mapped_column(default=0, nullable=False)
    num_recensioni: Mapped[int] = mapped_column(default=0, nullable=False)

    utente: Mapped["Utente"] = relationship(back_populates="proprietario")
    proprieta: Mapped[List["Proprieta"]] = relationship(back_populates="proprietario")
    

class Proprieta(db.Model):
    __tablename__ = "proprieta"

    id: Mapped[int] = mapped_column(primary_key=True)
    via: Mapped[str] = mapped_column(String(50), nullable=False)
    num_civico: Mapped[int] = mapped_column(nullable=False)
    citta: Mapped[str] = mapped_column(String(50))
    descrizione: Mapped[str] = mapped_column(String(50))
    stelle: Mapped[int] = mapped_column(default=0, nullable=False)
    num_recensioni: Mapped[int] = mapped_column(default=0, nullable=False)
    proprietarioid: Mapped[int] = mapped_column(ForeignKey("proprietari.id"))

    proprietario: Mapped["Proprietario"] = relationship(back_populates="proprieta")
    camere: Mapped[List["Camera"]] = relationship(back_populates="proprieta")
    
class Camera(db.Model):
    __tablename__ = "camere"

    ordinale: Mapped[int] = mapped_column(primary_key=True)
    proprietaid: Mapped[int] = mapped_column(ForeignKey("proprieta.id"), primary_key=True)

    proprieta: Mapped["Proprieta"] = relationship(back_populates="camere")

