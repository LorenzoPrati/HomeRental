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
from sqlalchemy import Table, Column

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

class Proprietario(db.Model):
    __tablename__ = "proprietari"

    id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), primary_key=True)
    stelle: Mapped[int] = mapped_column(default=0, nullable=False)
    num_recensioni: Mapped[int] = mapped_column(default=0, nullable=False)

    utente: Mapped["Utente"] = relationship(back_populates="proprietario")
    proprieta: Mapped[List["Proprieta"]] = relationship(back_populates="proprietario")
    
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
    citta: Mapped[str] = mapped_column(String(50))
    descrizione: Mapped[str] = mapped_column(String(50))
    stelle: Mapped[int] = mapped_column(default=0, nullable=False)
    num_recensioni: Mapped[int] = mapped_column(default=0, nullable=False)
    proprietarioid: Mapped[int] = mapped_column(ForeignKey("proprietari.id"))

    proprietario: Mapped["Proprietario"] = relationship(back_populates="proprieta")
    camere: Mapped[List["Camera"]] = relationship(back_populates="proprieta")
    amenita: Mapped[List["Amenita"]] = relationship(secondary=proprieta_amenita, back_populates="proprieta")

    def getNumCamere(self):
        if self.camere:
            return len(self.camere)
        else:
            return 0
    
class Amenita(db.Model):
    __tablename__ = "amenita"

    nome: Mapped[str] = mapped_column(String(20), primary_key=True)
    proprieta: Mapped[List["Proprieta"]] = relationship(secondary=proprieta_amenita, back_populates="amenita")
    
class Camera(db.Model):
    __tablename__ = "camere"

    ordinale: Mapped[int] = mapped_column(primary_key=True)
    proprietaid: Mapped[int] = mapped_column(ForeignKey("proprieta.id"), primary_key=True)

    proprieta: Mapped["Proprieta"] = relationship(back_populates="camere")
    letti: Mapped[List["Letto"]] = relationship(back_populates="camera")

    def getNumLetti(self):
        if self.letti:
            return len(self.letti)
        else:
            return 0

Tipo_Letto = Enum('Tipo_Letto', ['SINGOLO', 'UNA PIAZZA E MEZZO', 'MATRIMONIALE'])

class Letto(db.Model):
    __tablename__ = "letti"

    id: Mapped[int] = mapped_column(primary_key=True)
    ordinale: Mapped[int] = mapped_column(nullable=False)
    ordinaleCamera: Mapped[int] = mapped_column(ForeignKey("camere.ordinale"))
    proprietaid: Mapped[int] = mapped_column(ForeignKey("proprieta.id"))
    tipo: Mapped["Tipo_Letto"] = mapped_column(nullable=False)

    camera: Mapped["Camera"] = relationship(back_populates="letti")


    