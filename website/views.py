from flask import Blueprint, render_template, request, url_for, flash, redirect, session, json, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import Tipo_Struttura, Utente, Proprieta, Proprietario, Camera, Amenita, offerte, Citta, Soggiorno, occupazioni, Recensione
from . import db
from sqlalchemy import delete, text, or_, and_, func
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
    
    #lista_proprieta = Proprieta.query.filter(Proprieta.cittaid == citta).all()
    id_camere_libere = db.session.query(Camera.id).outerjoin(occupazioni).outerjoin(Soggiorno).filter(check_in<=Soggiorno.check_out, check_out>=Soggiorno.check_in).distinct().subquery()
    lista_proprieta = db.session.query(Proprieta).join(Camera).filter(Camera.id.not_in(id_camere_libere), Proprieta.cittaid==citta).group_by(Proprieta.id).having(func.sum(Camera.num_ospiti)>=num_ospiti).all()
    
    return render_template("ricerca.html", user=current_user, citta=citta, lista_proprieta=lista_proprieta, check_in=check_in, check_out=check_out, num_ospiti=num_ospiti)

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
    id_proprieta = request.args.get('proprieta_id')
    proprieta = Proprieta.query.get(id_proprieta)

    if request.method == 'POST':
        camere = []
        lista_camere_prenotate = request.form.getlist('camere_prenotate')
        for id in lista_camere_prenotate:
            camera = Camera.query.get(id)
            camere.append(camera)
        soggiorno = Soggiorno(check_in=check_in, check_out=check_out, num_ospiti=num_ospiti, prezzo_totale=0, utenteid=current_user.id, utente=current_user, camere=camere)
        db.session.add(soggiorno)
        db.session.commit()
        flash('Prenotazione effettuata con successo', category='success')
    
    id_camere_occupate = db.session.query(Camera.id).join(Proprieta).outerjoin(occupazioni).outerjoin(Soggiorno).filter(check_in<=Soggiorno.check_out, check_out>=Soggiorno.check_in).filter(Camera.proprietaid == id_proprieta).distinct().subquery()
    camere_libere = db.session.query(Camera).filter(Camera.id.not_in(id_camere_occupate), Camera.proprietaid == id_proprieta).all()
    return render_template("proprieta.html", user=current_user, citta=citta, check_in=check_in, check_out=check_out, num_ospiti=num_ospiti, proprieta=proprieta, camere_libere=camere_libere)

@views.route('/scrivi_recensione', methods=['GET', 'POST'])
@login_required
def scrivi_recensione():
    proprieta_id = request.args.get('proprieta_id')
    vecchia_recensione = Recensione.query.get((current_user.id, proprieta_id))
    if request.method == 'POST':
        stelle = request.form.get("stelle")
        testo = request.form.get("testo")
        proprieta = Proprieta.query.get(proprieta_id)
        recensione = Recensione(stelle=stelle, testo=testo, utente=current_user, proprieta=proprieta)
        if vecchia_recensione:
            vecchia_recensione.stelle = stelle
            vecchia_recensione.testo = testo
            db.session.commit()
            flash('Recensione modificata.', category='success')
        else:
            proprieta.stelle = (proprieta.stelle * proprieta.num_recensioni + int(stelle)) / (proprieta.num_recensioni + 1)
            proprieta.num_recensioni = proprieta.num_recensioni + 1
            db.session.add(recensione)
            db.session.commit()
            flash('Recensione pubblicata.', category='success')
    
    return render_template("scrivi_recensione.html", user=current_user, vecchia_recensione=vecchia_recensione)

@views.route('/dashboard_proprietario', methods=['GET', 'POST'])
@login_required
def dashboard_proprietario():
    
    return render_template("dashboard_proprietario.html", user=current_user)

@views.route('/gestisci_prenotazioni', methods=['GET', 'POST'])
@login_required
def gestisci_prenotazioni():
    proprieta_id = request.args.get('id')
    soggiorni = db.session.query(Soggiorno).join(occupazioni).join(Camera).filter(Camera.id_proprieta==proprieta_id).distinct()
    
    return render_template("gestisci_prenotazioni.html", user=current_user, soggiorni=soggiorni)

@views.route('/aggiungi_proprieta', methods=['GET', 'POST'])
@login_required
def aggiungi_proprieta():
    lista_citta = Citta.query.all()
    lista_tipi_struttura = Tipo_Struttura.query.all()

    if request.method == 'POST':
        proprieta = Proprieta(
            indirizzo=request.form.get('indirizzo'),
            id_citta = request.form.get('citta'),
            id_tipo_struttura = request.form.get('tipo_struttura'),
            descrizione = request.form.get('descrizione')
        )
        proprietario = current_user.proprietario
        if proprietario:
            proprieta.id_proprietario = proprietario.id
        else:
            current_user.proprietario = Proprietario(id=current_user.id)
            proprieta.id_proprietario = current_user.proprietario.id 
        proprieta.proprietario = current_user.proprietario
        db.session.add(proprieta)
        db.session.commit()
        flash('Property added successfully.', category='success')
        return redirect(url_for('views.dashboard_proprietario'))
    
    return render_template("aggiungi_proprieta.html", user=current_user, lista_citta=lista_citta, lista_tipi_struttura=lista_tipi_struttura)

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