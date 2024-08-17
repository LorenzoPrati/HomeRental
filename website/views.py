from flask import Blueprint, render_template, request, url_for, flash, redirect, session, json, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import Utente, Proprieta, Proprietario, Camera, Amenita, proprieta_amenita, Citta, Soggiorno, occupazioni
from . import db
from sqlalchemy import delete, text
import datetime

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        citta = request.form.get('citta')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        num_ospiti = request.form.get('num_ospiti')
        return redirect(url_for('views.ricerca', citta=citta, check_in=check_in, check_out=check_out, num_ospiti=num_ospiti))

    return render_template("home.html", user=current_user, Citta=Citta)

@views.route('/ricerca', methods=['GET', 'POST'])
@login_required
def ricerca():
    citta = request.args.get('citta')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    num_ospiti = request.args.get('num_ospiti')
    lista_proprieta = Proprieta.query.filter(Proprieta.cittaid == citta).all()
    return render_template("ricerca.html", user=current_user, citta=citta, lista_proprieta=lista_proprieta,check_in=check_in, check_out=check_out, num_ospiti=num_ospiti)

@views.route('/prenotazioni')
@login_required
def prenotazioni():
    return render_template("prenotazioni.html", user=current_user, now=datetime.datetime.now())

@views.route('/proprieta', methods=['GET', 'POST'])
@login_required
def proprieta():
    citta = request.args.get('citta')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    num_ospiti = request.args.get('num_ospiti')
    proprieta_id = request.args.get('proprieta_id')
    proprieta = Proprieta.query.get(proprieta_id)
    if request.method == 'POST':
        camere_id = []
        camere = []
        #for camera in proprieta.camere:
            #id = camera.id
            #if request.form.get(str(id)):
                #camere_id.append(id)
                #flash('Eccoci', category='success')
        lista_camere_prenotate = request.form.getlist('camere_prenotate')
        for id in lista_camere_prenotate:
            camera = Camera.query.get(id)
            camere.append(camera)
        soggiorno = Soggiorno(check_in=check_in, check_out=check_out, num_ospiti=num_ospiti, prezzo_totale=0, utenteid=current_user.id, utente=current_user, camere=camere)
        db.session.add(soggiorno)
        db.session.commit()
    
    
    return render_template("proprieta.html", user=current_user, citta=citta, check_in=check_in, check_out=check_out, num_ospiti=num_ospiti, proprieta=proprieta)

@views.route('/dashboard_proprietario', methods=['GET', 'POST'])
@login_required
def dashboard_proprietario():
    
    return render_template("dashboard_proprietario.html", user=current_user)

@views.route('/gestisci_prenotazioni', methods=['GET', 'POST'])
@login_required
def gestisci_prenotazioni():
    proprieta_id = request.args.get('id')
    #proprieta = Proprieta.query.get(proprieta_id)
    soggiorni = db.session.query(Soggiorno).join(occupazioni).join(Camera).filter(Camera.proprietaid==proprieta_id).distinct()
    return render_template("gestisci_prenotazioni.html", user=current_user, soggiorni=soggiorni)

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
            cittaid = request.form.get('citta'),
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
    return render_template("dettagli_proprieta_proprietario.html", user=current_user, p=p, Amenita=Amenita)

#@views.route('/removeBed', methods=['POST'])
#def remove_bed():
    #bed = json.loads(request.data)
    #bedid = bed['id']
    #bed = Letto.query.get(bedid)
    #ordinale = bed.ordinale
    #ordinaleCamera = bed.ordinaleCamera
    #proprietaid = bed.proprietaid
    #letti_da_modificare = Letto.query.filter_by(ordinaleCamera=ordinaleCamera, proprietaid=proprietaid).where(Letto.ordinale > ordinale).all()
    #for l in letti_da_modificare:
        #l.ordinale = l.ordinale - 1
    #db.session.delete(bed)
    #db.session.commit()
    #return jsonify({})

@views.route('/removeRoom', methods=['POST'])
def remove_room():
    obj = json.loads(request.data)
    camera_id = obj['camera_id']

    room = Camera.query.get(camera_id)
    db.session.delete(room)
    db.session.commit()
    return jsonify({})

@views.route('/addRoom', methods=['POST'])
def add_room():
    obj = json.loads(request.data)
    proprieta_id = obj['proprieta_id']
    prezzo = int(obj['prezzo'])
    num_ospiti = int(obj['num_ospiti'])

    proprieta = Proprieta.query.get(proprieta_id)
    ordinale = len(proprieta.camere) + 1
    nuova_camera = Camera(proprietaid=proprieta_id, ordinale=ordinale, prezzo=prezzo, num_ospiti=num_ospiti, proprieta=proprieta, soggiorni=[])

    db.session.add(nuova_camera)
    db.session.commit()
    return jsonify({})

#@views.route('/addBed', methods=['POST'])
#def add_bed():
    #c = json.loads(request.data)
    #ordinalecamera = c['ordinalecamera']
    #proprietaid = c['proprietaid']

    #c = Camera.query.get((ordinalecamera, proprietaid))
    #ordinale = c.getNumLetti() + 1
    #nuovo_letto = Letto(ordinale=ordinale, ordinaleCamera=ordinalecamera, proprietaid=proprietaid, camera=c, tipo=Tipo_Letto.MATRIMONIALE)

    #db.session.add(nuovo_letto)
    #db.session.commit()
    #return jsonify({})

@views.route('/removeAmenity', methods=['POST'])
def remove_amenity():
    obj = json.loads(request.data)
    nome = obj['nome']
    proprietaid = obj['proprietaid']
    p = Proprieta.query.get(proprietaid)
    
    for a in p.amenita:
        if a.nome == nome:
            p.amenita.remove(a)
            db.session.commit()
    return jsonify({})

@views.route('/addAmenity', methods=['POST'])
def add_amenity():
    obj = json.loads(request.data)
    nome = obj['nome']
    proprietaid = obj['proprietaid']

    st = proprieta_amenita.insert().values(proprieta_id=proprietaid, amenita_id=nome)
    db.session.execute(st)
    db.session.commit()
    return jsonify({})

@views.route('/rimuovi_proprieta', methods=['POST'])
def rimuovi_proprieta():
    obj = json.loads(request.data)
    proprietaid = obj['proprietaid']

    p = Proprieta.query.get(proprietaid)
    db.session.delete(p)
    db.session.commit()
    return jsonify({})