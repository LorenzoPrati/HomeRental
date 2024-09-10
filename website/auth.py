from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Amenita, Citta, Utente, Coupon, Tipo_Struttura, spendibilita_coupons
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import random

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        utente = Utente.query.filter_by(email=email).first()
        if utente:
            if utente.password == password:
                login_user(utente, remember=True)
                return redirect(url_for("views.home"))
            else:
                flash("Password sbagliata, prova di nuovo.", category="error")
        else:
            flash("Email non esiste.", category="error")

    return render_template("login.html", user=current_user)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        email = request.form.get("email")
        nome_utente = request.form.get("nome_utente")
        nome = request.form.get("nome")
        cognome = request.form.get("cognome")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        utente_stessa_mail = Utente.query.filter_by(email=email).first()
        utente_stesso_nick = Utente.query.filter_by(nome_utente=nome_utente).first()
        if utente_stessa_mail or utente_stesso_nick:
            flash("Email o nome_utente in uso.", category="error")
        elif password1 != password2:
            flash("Passwords don't match", category="error")
        else:
            utente = Utente(
                email=email,
                password=password1,
                nome_utente=nome_utente,
                nome=nome,
                cognome=cognome,
            )
            db.session.add(utente)
            db.session.commit()
            login_user(utente, remember=True)
            flash("Account creato.", category="success")

            num_utenti = db.session.query(Utente).count()
            if num_utenti == 1:
                """For testing, insert basic cities, amenities and structures."""
                citta = Citta.query.all()
                if not citta:
                    for c in ["Milano", "Roma", "Bari", "Monza", "Cagliari"]:
                        db.session.add(Citta(nome=c))
                amenita = Amenita.query.all()
                if not amenita:
                    for a in ["wi-fi", "piscina", "tv"]:
                        db.session.add(Amenita(nome=a))
                tipi_struttura = Tipo_Struttura.query.all()
                if not tipi_struttura:
                    for t in ["Appartamento", "Cottage", "Baita"]:
                        db.session.add(Tipo_Struttura(nome=t))

                db.session.commit()

            tipi_struttura = Tipo_Struttura.query.all()
            if tipi_struttura:
                for i in range(3):
                    num_tipi_struttura = random.randint(1, 3)
                    tipi_struttura_casuali = random.sample(
                        tipi_struttura, num_tipi_struttura
                    )
                    percentuale_sconto_casuale = random.randrange(10, 50, 10)
                    coupon = Coupon(
                        percentuale_sconto=percentuale_sconto_casuale,
                        id_utente=utente.id,
                    )
                    coupon.utente = utente
                    coupon.tipi_struttura = tipi_struttura_casuali
                    db.session.add(coupon)
                    db.session.commit()

            return redirect(url_for("views.home"))

    return render_template("sign_up.html", user=current_user)
