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
        
        user = Utente.query.filter_by(email=email).first()
        if user:
            if user.password == password:
                flash('Logged in successfully.', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

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
        user_name = request.form.get('username')
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        user = Utente.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        if len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(user_name) < 2:
            flash('Username must be greater than 1 characters.', category='error') 
        elif password1 != password2:
            flash('Passwords don\'t match', category='error') 
        elif len(password1) < 7:
            flash('Passwords must be at least 7 characters.', category='error') 
        else:
            utente = Utente(first_name=first_name, last_name=last_name, username=user_name, email=email, password=password1,)
            db.session.add(utente)
            db.session.commit()
            login_user(utente, remember=True)
            flash('Account created.', category='success')
            return redirect(url_for('views.home'))
        
    return render_template("sign_up.html", user=current_user)

