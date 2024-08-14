from flask import Blueprint, render_template, request, url_for, flash, redirect, session, json, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import Utente, Proprieta, Proprietario, Camera, Letto, Tipo_Letto, Amenita, proprieta_amenita
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
        nuova_proprieta = Proprieta(
            via=request.form.get('via'),
            num_civico = request.form.get('numerocivico'),
            citta = request.form.get('citta'),
            descrizione = request.form.get('descrizione'),
            proprietarioid = p.id
        )
        db.session.add(nuova_proprieta)
        db.session.commit()
        flash('Property added successfully.', category='success')
        return redirect(url_for('views.dashboard_proprietario'))
    return render_template("aggiungi_proprieta.html", user=current_user)

@views.route('/dettagli_proprieta_proprietario', methods=['GET', 'POST'])
@login_required
def dettagli_proprieta_proprietario():
    if request.method == 'POST':
        proprietaid = session.get('proprietaid')
        p = Proprieta.query.get(proprietaid)
        p.descrizione = request.form.get('descrizione')
        db.session.commit()
    id = request.args.get('id')
    p = db.session.query(Proprieta).filter_by(id=id).one()
    session['proprietaid'] = p.id
    return render_template("dettagli_proprieta_proprietario.html", user=current_user, p=p, en=Tipo_Letto, Amenita=Amenita)

@views.route('/removeBed', methods=['POST'])
def remove_bed():
    bed = json.loads(request.data)
    bedid = bed['id']
    bed = Letto.query.get(bedid)
    ordinale = bed.ordinale
    ordinaleCamera = bed.ordinaleCamera
    proprietaid = bed.proprietaid
    letti_da_modificare = Letto.query.filter_by(ordinaleCamera=ordinaleCamera, proprietaid=proprietaid).where(Letto.ordinale > ordinale).all()
    for l in letti_da_modificare:
        l.ordinale = l.ordinale - 1
    db.session.delete(bed)
    db.session.commit()
    return jsonify({})

@views.route('/removeRoom', methods=['POST'])
def remove_room():
    room = json.loads(request.data)
    ordinale = room['ordinale']
    proprietaid = room['proprietaid']

    room = Camera.query.get((ordinale, proprietaid))
    db.session.delete(room)
    db.session.commit()
    return jsonify({})

@views.route('/addRoom', methods=['POST'])
def add_room():
    p = json.loads(request.data)
    proprietaid = p['proprietaid']

    p = Proprieta.query.get(proprietaid)
    ordinale = p.getNumCamere() + 1
    nuova_camera = Camera(ordinale=ordinale, proprietaid=proprietaid, proprieta=p)

    db.session.add(nuova_camera)
    db.session.commit()
    return jsonify({})

@views.route('/addBed', methods=['POST'])
def add_bed():
    c = json.loads(request.data)
    ordinalecamera = c['ordinalecamera']
    proprietaid = c['proprietaid']

    c = Camera.query.get((ordinalecamera, proprietaid))
    ordinale = c.getNumLetti() + 1
    nuovo_letto = Letto(ordinale=ordinale, ordinaleCamera=ordinalecamera, proprietaid=proprietaid, camera=c, tipo=Tipo_Letto.MATRIMONIALE)

    db.session.add(nuovo_letto)
    db.session.commit()
    return jsonify({})

@views.route('/removeAmenity', methods=['POST'])
def remove_amenity():
    obj = json.loads(request.data)
    nome = obj['nome']
    proprietaid = obj['proprietaid']
    p = Proprieta.query.get(proprietaid)
    for a in p.amenita:
        if a.nome == nome:
            db.session.delete(a)
    
    db.session.commit()
    return jsonify({})