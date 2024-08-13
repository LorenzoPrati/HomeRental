from flask import Blueprint, render_template, request, url_for, flash, redirect
from flask_login import login_user, login_required, logout_user, current_user
from .models import Utente, Proprieta, Proprietario
from . import db

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/dashboard_proprietario', methods=['GET', 'POST'])
@login_required
def dashboard_proprietario():
    
    return render_template("dashboard_proprietario.html", user=current_user)

@views.route('/aggiungi_proprieta', methods=['GET', 'POST'])
@login_required
def aggiungi_proprieta():
    if request.method == 'POST':
        p = Proprietario.query.filter_by(id=current_user.id).first()
        if not p:
            p = Proprietario(utente=current_user, id=current_user.id)
            db.session.add(p)
        citta = request.form.get('citta')
        via = request.form.get('via')
        numero_civico = request.form.get('numerocivico')
        descrizione = request.form.get('descrizione')
        nuova_proprieta = Proprieta(
            citta = citta, 
            via = via,
            num_civico = numero_civico,
            descrizione = descrizione, 
            proprietarioid = p.id, 
            proprietario=p
        )
        db.session.add(nuova_proprieta)
        db.session.commit()
        flash('Property added successfully.', category='success')
        return redirect(url_for('views.dashboard_proprietario'))

    return render_template("aggiungi_proprieta.html", user=current_user)