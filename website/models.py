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
from sqlalchemy import Table, Column, DateTime
import datetime

from enum import Enum

class Base(DeclarativeBase):
    pass

class Utente(db.Model, UserMixin):
    __tablename__ = "utenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[String] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    
    proprietario: Mapped[Optional["Proprietario"]] = relationship(back_populates="utente") # -> qui ci va il nome del campo dell'altra classe
    soggiorni: Mapped[List["Soggiorno"]] = relationship(back_populates="utente")

class Proprietario(db.Model):
    __tablename__ = "proprietari"

    id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), primary_key=True)
    stelle: Mapped[int] = mapped_column(default=0, nullable=False)
    num_recensioni: Mapped[int] = mapped_column(default=0, nullable=False)

    utente: Mapped["Utente"] = relationship(back_populates="proprietario")
    proprieta: Mapped[List["Proprieta"]] = relationship(back_populates="proprietario")

class Citta(db.Model):
    __tablename__ = "citta"

    nome: Mapped[str] = mapped_column(String(100), primary_key=True)
    descrizione: Mapped[str] = mapped_column(String(200), nullable=False)

    proprieta: Mapped[List["Proprieta"]] = relationship(back_populates="citta")
    
proprieta_amenita = db.Table(
    "proprieta_amenita",
    Column("proprieta_id", db.ForeignKey("proprieta.id"), primary_key=True),
    Column("amenita_id", db.ForeignKey("amenita.nome"), primary_key=True)
)

class Proprieta(db.Model):
    __tablename__ = "proprieta"

    id: Mapped[int] = mapped_column(primary_key=True)
    via: Mapped[str] = mapped_column(String(50), nullable=False)
    num_civico: Mapped[int] = mapped_column(nullable=False)
    cittaid: Mapped[str] = mapped_column(ForeignKey("citta.nome"))
    descrizione: Mapped[str] = mapped_column(String(50))
    stelle: Mapped[int] = mapped_column(default=0, nullable=False)
    num_recensioni: Mapped[int] = mapped_column(default=0, nullable=False)
    proprietarioid: Mapped[int] = mapped_column(ForeignKey("proprietari.id"))

    citta: Mapped["Citta"] = relationship(back_populates="proprieta")
    proprietario: Mapped["Proprietario"] = relationship(back_populates="proprieta")
    camere: Mapped[List["Camera"]] = relationship(back_populates="proprieta", cascade="all, delete")
    amenita: Mapped[List["Amenita"]] = relationship(secondary=proprieta_amenita, back_populates="proprieta")
    
class Amenita(db.Model):
    __tablename__ = "amenita"

    nome: Mapped[str] = mapped_column(String(20), primary_key=True)
    proprieta: Mapped[List["Proprieta"]] = relationship(secondary=proprieta_amenita, back_populates="amenita")

occupazioni = db.Table(
    "occupazioni",
    Column("soggiorno", db.ForeignKey("soggiorni.id"), primary_key=True),
    Column("camera_id", db.ForeignKey("camere.id"), primary_key=True),
)

class Camera(db.Model):
    __tablename__ = "camere"

    id: Mapped[int] = mapped_column(primary_key=True)
    ordinale: Mapped[int] = mapped_column(nullable=False)
    proprietaid: Mapped[int] = mapped_column(ForeignKey("proprieta.id"), nullable=False)
    num_ospiti: Mapped[int] = mapped_column(nullable=False)
    prezzo: Mapped[int] = mapped_column(nullable=False)

    proprieta: Mapped["Proprieta"] = relationship(back_populates="camere")
    soggiorni: Mapped[List["Soggiorno"]] = relationship(secondary=occupazioni, back_populates="camere")
    
class Soggiorno(db.Model):
    __tablename__ = "soggiorni"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_in: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    num_ospiti: Mapped[int] = mapped_column(nullable=False)
    prezzo_totale: Mapped[int] = mapped_column(nullable=False)
    utenteid: Mapped[int] = mapped_column(ForeignKey("utenti.id"))

    utente: Mapped["Utente"] = relationship(back_populates="soggiorni")
    camere: Mapped[List["Camera"]] = relationship(secondary=occupazioni, back_populates="soggiorni")

    



    