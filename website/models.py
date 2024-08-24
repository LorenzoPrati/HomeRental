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

    proprietario: Mapped[Optional["Proprietario"]] = relationship(back_populates="utente")
    soggiorni: Mapped[Optional[List["Soggiorno"]]] = relationship(back_populates="utente")
    recensioni: Mapped[Optional[List["Recensione"]]] = relationship(back_populates="utente")
    metodi_pagamento: Mapped[Optional[List["Metodo_Pagamento"]]] = relationship(back_populates="utente")

class Proprietario(db.Model):
    __tablename__ = "proprietari"

    id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), primary_key=True)
    biografia: Mapped[str] = mapped_column(String(500), nullable=True)
    valutazione_media: Mapped[int] = mapped_column(DECIMAL(2,1), default=0)
    num_valutazioni: Mapped[int] = mapped_column(default=0)
    id_metodo_accredito: Mapped[int] = mapped_column(ForeignKey("metodi_pagamento.id"))

    utente: Mapped["Utente"] = relationship(back_populates="proprietario")
    proprieta: Mapped[Optional[List["Proprieta"]]] = relationship(back_populates="proprietario")
    metodo_accredito: Mapped["Metodo_Pagamento"] = relationship(back_populates="proprietario")

class Citta(db.Model):
    __tablename__ = "citta"

    nome: Mapped[str] = mapped_column(String(256), primary_key=True)

    proprieta: Mapped[Optional[List["Proprieta"]]] = relationship(back_populates="citta")
    
servizi = db.Table(
    "servizi",
    Column("id_proprieta", db.ForeignKey("proprieta.id"), primary_key=True),
    Column("id_amenita", db.ForeignKey("amenita.nome"), primary_key=True)
)

class Amenita(db.Model):
    __tablename__ = "amenita"

    nome: Mapped[str] = mapped_column(String(256), primary_key=True)

    proprieta: Mapped[Optional[List["Proprieta"]]] = relationship(secondary=servizi, back_populates="amenita")

spendibilita_coupons = db.Table(
    "spendibilita_coupons",
    Column("id_coupon", db.ForeignKey("coupons.id"), primary_key=True),
    Column("id_tipo_struttura", db.ForeignKey("tipi_struttura.nome"), primary_key=True),
)

class Tipo_Struttura(db.Model):
    __tablename__ = "tipi_struttura"

    nome: Mapped[str] = mapped_column(String(256), primary_key=True)

    proprieta: Mapped[Optional[List["Proprieta"]]] = relationship(back_populates="tipo_struttura")
    coupons: Mapped[Optional[List["Coupon"]]] = relationship(secondary=spendibilita_coupons, back_populates="tipi_struttura")

class Proprieta(db.Model):
    __tablename__ = "proprieta"

    id: Mapped[int] = mapped_column(primary_key=True)
    indirizzo: Mapped[str] = mapped_column(String(500))
    descrizione: Mapped[str] = mapped_column(String(500), nullable=True)
    valutazione_media: Mapped[int] = mapped_column(DECIMAL(2,1), default=0)
    num_valutazioni: Mapped[int] = mapped_column(default=0)
    data_creazione: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    id_citta: Mapped[str] = mapped_column(ForeignKey("citta.nome"))
    id_tipo_struttura: Mapped[str] = mapped_column(ForeignKey("tipi_struttura.nome"))
    id_proprietario: Mapped[int] = mapped_column(ForeignKey("proprietari.id"))

    proprietario: Mapped["Proprietario"] = relationship(back_populates="proprieta")
    amenita: Mapped[Optional[List["Amenita"]]] = relationship(secondary=servizi, back_populates="proprieta")
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
    num_ospiti: Mapped[int] = mapped_column()
    prezzo_per_notte: Mapped[int] = mapped_column()
    id_proprieta: Mapped[int] = mapped_column(ForeignKey("proprieta.id"))

    proprieta: Mapped["Proprieta"] = relationship(back_populates="camere")
    soggiorni: Mapped[Optional[List["Soggiorno"]]] = relationship(secondary=occupazioni, back_populates="camere")
    
class Soggiorno(db.Model):
    __tablename__ = "soggiorni"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_in: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    check_out: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    num_ospiti: Mapped[int] = mapped_column()
    prezzo: Mapped[int] = mapped_column()
    id_utente: Mapped[int] = mapped_column(ForeignKey("utenti.id"))

    utente: Mapped["Utente"] = relationship(back_populates="soggiorni")
    camere: Mapped[List["Camera"]] = relationship(secondary=occupazioni, back_populates="soggiorni")
    pagamento: Mapped["Pagamento"] = relationship(back_populates="soggiorno")

class Recensione(db.Model):
    __tablename__ = "recensioni"

    id_utente: Mapped[int] = mapped_column(ForeignKey("utenti.id"), primary_key=True)
    id_proprieta: Mapped[int] = mapped_column(ForeignKey("proprieta.id"), primary_key=True)
    valutazione: Mapped[int] = mapped_column(DECIMAL(1,1))
    testo: Mapped[str] = mapped_column(String(500), nullable=True)
    data_ultima_modifica: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    utente: Mapped["Utente"] = relationship(back_populates="recensioni")
    proprieta: Mapped["Proprieta"] = relationship(back_populates="recensioni")

class Metodo_Pagamento(db.Model):
    __tablename__ = "metodi_pagamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_utente: Mapped[int] = mapped_column(ForeignKey("utenti.id"))

    utente: Mapped["Utente"] = relationship(back_populates="metodi_pagamento")
    proprietario: Mapped[Optional["Proprietario"]] = relationship(back_populates="metodo_accredito")
    paypal: Mapped[Optional["Paypal"]] = relationship(back_populates="metodo_pagamento")
    carta: Mapped[Optional["Carta"]] = relationship(back_populates="metodo_pagamento")
    pagamenti: Mapped[Optional[List["Pagamento"]]] = relationship(back_populates="metodo_pagamento")

class Paypal(db.Model):
    __tablename__ = "paypals"

    id: Mapped[int] = mapped_column(ForeignKey("metodi_pagamento.id"), primary_key=True)
    email: Mapped[str] = mapped_column(String(256), unique=True)

    metodo_pagamento: Mapped["Metodo_Pagamento"] = relationship(back_populates="paypal")

class Carta(db.Model):
    __tablename__ = "carte"

    id: Mapped[int] = mapped_column(ForeignKey("metodi_pagamento.id"), primary_key=True)
    numero_carta: Mapped[str] = mapped_column(String(256), unique=True)
    cvc: Mapped[int] = mapped_column()
    data_scadenza: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    
    metodo_pagamento: Mapped["Metodo_Pagamento"] = relationship(back_populates="carta")

class Coupon(db.Model):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    percentuale_sconto: Mapped[int] = mapped_column()
    id_utente: Mapped[int] = mapped_column(ForeignKey("utenti.id"))

    tipi_struttura: Mapped[Optional[List[Tipo_Struttura]]] = relationship(secondary=spendibilita_coupons, back_populates="coupons")
    pagamento: Mapped[Optional["Pagamento"]] = relationship(back_populates="coupon")

class Pagamento(db.Model):
    __tablename__ = "pagamenti"

    id: Mapped[int] = mapped_column(ForeignKey("soggiorni.id"), primary_key=True)
    totale: Mapped[int] = mapped_column()
    id_metodo_pagamento: Mapped[int] = mapped_column(ForeignKey("metodi_pagamento.id"))
    id_coupon: Mapped[int] = mapped_column(ForeignKey("coupons.id"), unique=True, nullable=True)

    soggiorno: Mapped["Soggiorno"] = relationship(back_populates="pagamento")
    metodo_pagamento: Mapped["Metodo_Pagamento"] = relationship(back_populates="pagamenti")
    coupon: Mapped[Optional["Coupon"]] = relationship(back_populates="pagamento")