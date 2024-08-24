from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Utente
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        utente = Utente.query.filter_by(email=email).first()
        if utente:
            if utente.password == password:
                flash('Loggato con successo.', category='success')
                login_user(utente, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Password sbagliata, prova di nuovo.', category='error')
        else:
            flash('Email non esiste.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        nome_utente = request.form.get('nome_utente')
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        utente = Utente.query.filter_by(email=email).first()
        if utente:
            flash('Email in uso.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match', category='error') 
        else:
            utente = Utente(email=email, password=password1, nome_utente=nome_utente, nome=nome, cognome=cognome)
            db.session.add(utente)
            db.session.commit()
            login_user(utente, remember=True)
            flash('Account creato con successo.', category='success')
            return redirect(url_for('views.home'))
        
    return render_template("sign_up.html", user=current_user)

