from . import db

from flask_login import UserMixin
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy import String, DECIMAL, func
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
    email: Mapped[str] = mapped_column(String(256), unique=True)
    password: Mapped[str] = mapped_column(String(256))
    nome_utente: Mapped[str] = mapped_column(String(256), unique=True)
    nome: Mapped[String] = mapped_column(String(256))
    cognome: Mapped[str] = mapped_column(String(256))
    data_creazione: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    proprietario: Mapped[Optional["Proprietario"]] = relationship(back_populates="utente")
    soggiorni: Mapped[List["Soggiorno"]] = relationship(back_populates="utente")
    recensioni: Mapped[List["Recensione"]] = relationship(back_populates="utente")

class Proprietario(db.Model):
    __tablename__ = "proprietari"

    id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), primary_key=True)
    valutazione_media: Mapped[int] = mapped_column(DECIMAL(2,1), default=0)
    num_valutazioni: Mapped[int] = mapped_column(default=0)

    utente: Mapped["Utente"] = relationship(back_populates="proprietario")
    proprieta: Mapped[List["Proprieta"]] = relationship(back_populates="proprietario")

class Citta(db.Model):
    __tablename__ = "citta"

    nome: Mapped[str] = mapped_column(String(256), primary_key=True)

    proprieta: Mapped[Optional[List["Proprieta"]]] = relationship(back_populates="citta")
    
offerte = db.Table(
    "offerte",
    Column("id_proprieta", db.ForeignKey("proprieta.id"), primary_key=True),
    Column("amenita", db.ForeignKey("amenita.nome"), primary_key=True)
)

class Amenita(db.Model):
    __tablename__ = "amenita"

    nome: Mapped[str] = mapped_column(String(256), primary_key=True)

    proprieta: Mapped[Optional[List["Proprieta"]]] = relationship(secondary=offerte, back_populates="amenita")

class Tipo_Struttura(db.Model):
    __tablename__ = "tipi_struttura"

    nome: Mapped[str] = mapped_column(String(256), primary_key=True)

    proprieta: Mapped[Optional[List["Proprieta"]]] = relationship(back_populates="tipo_struttura")

class Proprieta(db.Model):
    __tablename__ = "proprieta"

    id: Mapped[int] = mapped_column(primary_key=True)
    indirizzo: Mapped[str] = mapped_column(String(256))
    id_citta: Mapped[str] = mapped_column(ForeignKey("citta.nome"))
    id_tipo_struttura: Mapped[str] = mapped_column(ForeignKey("tipi_struttura.nome"))
    descrizione: Mapped[str] = mapped_column(String(500))
    valutazione_media: Mapped[int] = mapped_column(DECIMAL(2,1), default=0)
    num_valutazioni: Mapped[int] = mapped_column(default=0)
    id_proprietario: Mapped[int] = mapped_column(ForeignKey("proprietari.id"))
    data_creazione: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    proprietario: Mapped["Proprietario"] = relationship(back_populates="proprieta")
    amenita: Mapped[Optional[List["Amenita"]]] = relationship(secondary=offerte, back_populates="proprieta")
    citta: Mapped["Citta"] = relationship(back_populates="proprieta")
    tipo_struttura: Mapped["Tipo_Struttura"] = relationship(back_populates="proprieta")
    camere: Mapped[Optional[List["Camera"]]] = relationship(back_populates="proprieta")
    recensioni: Mapped[Optional[List["Recensione"]]] = relationship(back_populates="proprieta")

occupazioni = db.Table(
    "occupazioni",
    Column("id_soggiorno", db.ForeignKey("soggiorni.id"), primary_key=True),
    Column("id_camera", db.ForeignKey("camere.id"), primary_key=True),
)

class Camera(db.Model):
    __tablename__ = "camere"
    __table_args__ = (
        UniqueConstraint("id_proprieta", "ordinale"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ordinale: Mapped[int] = mapped_column(nullable=False)
    num_ospiti: Mapped[int] = mapped_column(nullable=False, default=1)
    prezzo_per_notte: Mapped[int] = mapped_column(nullable=False, default=0)
    id_proprieta: Mapped[int] = mapped_column(ForeignKey("proprieta.id"), nullable=False)

    proprieta: Mapped["Proprieta"] = relationship(back_populates="camere")
    soggiorni: Mapped[Optional[List["Soggiorno"]]] = relationship(secondary=occupazioni, back_populates="camere")
    
class Soggiorno(db.Model):
    __tablename__ = "soggiorni"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_in: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    num_ospiti: Mapped[int] = mapped_column(nullable=False)
    prezzo: Mapped[int] = mapped_column(nullable=False)
    id_utente: Mapped[int] = mapped_column(ForeignKey("utenti.id"))

    utente: Mapped["Utente"] = relationship(back_populates="soggiorni")
    camere: Mapped[List["Camera"]] = relationship(secondary=occupazioni, back_populates="soggiorni")

class Recensione(db.Model):
    __tablename__ = "recensioni"

    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), primary_key=True)
    proprieta_id: Mapped[int] = mapped_column(ForeignKey("proprieta.id"), primary_key=True)
    valutazione: Mapped[int] = mapped_column(DECIMAL(1,1), nullable=False, default=5)
    testo: Mapped[str] = mapped_column(String(500))
    data_creazione: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    utente: Mapped["Utente"] = relationship(back_populates="recensioni")
    proprieta: Mapped["Proprieta"] = relationship(back_populates="recensioni")
    