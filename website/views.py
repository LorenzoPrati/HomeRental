from flask import Blueprint, render_template, request, url_for, flash, redirect, session, json, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import Coupon, Metodo_Pagamento, Pagamento, Paypal, Tipo_Struttura, Utente, Proprieta, Proprietario, Camera, Amenita, servizi, Citta, Soggiorno, occupazioni, Recensione, spendibilita_coupons
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
    
    id_camere_occupate = db.session.query(Camera.id).outerjoin(occupazioni).outerjoin(Soggiorno).filter(check_in<=Soggiorno.check_out, check_out>=Soggiorno.check_in).distinct().subquery()
    lista_proprieta = db.session.query(Proprieta).join(Camera).filter(Camera.id.not_in(id_camere_occupate), Proprieta.id_citta==citta).group_by(Proprieta.id).having(func.sum(Camera.num_ospiti)>=num_ospiti).all()
    
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
        prezzo = 0
        lista_camere_prenotate = request.form.getlist('camere_prenotate')
        for id in lista_camere_prenotate:
            camera = Camera.query.get(id)
            camere.append(camera)
            prezzo += camera.prezzo_per_notte
        soggiorno = Soggiorno(check_in=check_in, check_out=check_out, num_ospiti=num_ospiti, prezzo=prezzo, id_utente=current_user.id, utente=current_user, camere=camere)
        db.session.add(soggiorno)
        db.session.commit()

        id_metodo_pagamento = request.form.get('id_metodo_pagamento')
        id_coupon = request.form.get('id_coupon')

        if not id_metodo_pagamento:
            flash('Devi selezionare un metodo di pagamento.', category='error')
        else:
            pagamento = Pagamento(id=soggiorno.id, id_metodo_pagamento=id_metodo_pagamento, id_coupon=id_coupon)
            if id_coupon:
                coupon = Coupon.query.get(id_coupon)
                pagamento.coupon = coupon
            db.session.add(pagamento)
            db.session.commit()

            flash('Prenotazione effettuata con successo.', category='success')
            return redirect(url_for('views.prenotazioni'))
    
    id_camere_occupate = db.session.query(Camera.id).join(Proprieta).outerjoin(occupazioni).outerjoin(Soggiorno).filter(check_in<=Soggiorno.check_out, check_out>=Soggiorno.check_in).filter(Camera.id_proprieta == id_proprieta).distinct().subquery()
    camere_libere = db.session.query(Camera).filter(Camera.id.not_in(id_camere_occupate), Camera.id_proprieta == id_proprieta).all()
    
    coupons = db.session.query(Coupon).outerjoin(Pagamento).outerjoin(spendibilita_coupons).filter(spendibilita_coupons.c.id_tipo_struttura==proprieta.id_tipo_struttura, Coupon.id_utente==current_user.id, Pagamento.id_coupon==None).all()

    return render_template("proprieta.html", user=current_user, citta=citta, check_in=check_in, check_out=check_out, num_ospiti=num_ospiti, proprieta=proprieta, camere_libere=camere_libere, coupons=coupons)

@views.route('/scrivi_recensione', methods=['GET', 'POST'])
@login_required
def scrivi_recensione():
    id_proprieta = request.args.get('id_proprieta')
    vecchia_recensione = Recensione.query.get((current_user.id, id_proprieta))
    if request.method == 'POST':
        valutazione = request.form.get("valutazione")
        testo = request.form.get("testo")
        proprieta = Proprieta.query.get(id_proprieta)
        
        if vecchia_recensione:
            vecchia_recensione.testo = testo
            proprieta.valutazione_media = (proprieta.valutazione_media * proprieta.num_recensioni - vecchia_recensione.valutazione + valutazione) / proprieta.num_recensioni
            vecchia_recensione.valutazione = valutazione
            vecchia_recensione.data_ultima_modifica = datetime.datetime.now()
            db.session.commit()
            flash('Recensione modificata.', category='success')
        else:
            recensione = Recensione(valutazione=valutazione, testo=testo, utente=current_user, proprieta=proprieta, data_ultima_modifica=datetime.datetime.now())
            proprieta.valutazione_media = (proprieta.valutazione_media * proprieta.num_valutazioni + int(valutazione)) / (proprieta.num_valutazioni + 1)
            proprieta.num_valutazioni += 1
            proprietario = proprieta.proprietario
            proprietario.valutazione_media = (proprietario.valutazione_media * proprietario.num_valutazioni + proprieta.valutazione_media) / (proprietario.num_valutazioni + 1)
            proprietario.num_valutazioni += 1
            db.session.add(recensione)
            db.session.commit()
            flash('Recensione pubblicata.', category='success')
    
    return render_template("scrivi_recensione.html", user=current_user, vecchia_recensione=vecchia_recensione)

@views.route('/profilo', methods=['GET', 'POST'])
@login_required
def profilo():
    if request.method == 'POST':
        biografia = request.form.get('biografia')
        current_user.proprietario.biografia = biografia
        db.session.commit()

    return render_template("profilo.html", user=current_user, Coupon=Coupon)

@views.route('/dashboard_proprietario', methods=['GET', 'POST'])
@login_required
def dashboard_proprietario():
    flag = True
    
    return render_template("dashboard_proprietario.html", user=current_user, flag=flag)

@views.route('/pagamento', methods=['GET', 'POST'])
@login_required
def pagamento():
    id_pagamento = request.args.get('id_pagamento')
    pagamento = Pagamento.query.get(id_pagamento)

    return render_template("pagamento.html", user=current_user, pagamento=pagamento)

@views.route('/metodi_pagamento', methods=['GET', 'POST'])
@login_required
def metodi_pagamento():
    flag = request.args.get('flag')

    return render_template("metodi_pagamento.html", user=current_user, flag=flag)

@views.route('/aggiungi_paypal', methods=['GET', 'POST'])
@login_required
def aggiungi_paypal():
    flag = request.args.get('flag')

    if request.method == 'POST':

        email = request.form.get('email')
        metodo_pagamento = Metodo_Pagamento(id_utente=current_user.id)
        paypal = Paypal(email=email)
        paypal.id = metodo_pagamento.id
        metodo_pagamento.paypal = paypal
        metodo_pagamento.utente = current_user
        db.session.add(metodo_pagamento)
        db.session.commit()
        flash('Metodo di pagamento aggiunto con successo.', category='success')

        if flag:
            return redirect(url_for('views.aggiungi_proprieta'))
        else:
            return redirect(url_for('views.metodi_pagamento'))

    return render_template("aggiungi_paypal.html", user=current_user)

@views.route('/gestisci_prenotazioni', methods=['GET', 'POST'])
@login_required
def gestisci_prenotazioni():
    proprieta_id = request.args.get('id')
    soggiorni = db.session.query(Soggiorno).join(occupazioni).join(Camera).filter(Camera.id_proprieta==proprieta_id).distinct()
    
    return render_template("gestisci_prenotazioni.html", user=current_user, soggiorni=soggiorni)

@views.route('/recensioni', methods=['GET', 'POST'])
@login_required
def recensioni():
    id_proprieta = request.args.get('id')
    proprieta = Proprieta.query.get(id_proprieta)
    return render_template("recensioni.html", user=current_user, proprieta=proprieta)

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
        if not current_user.proprietario:
            id = request.form.get('metodo_pagamento')
            biografia = request.form.get('biografia')
            metodo = Metodo_Pagamento.query.get(id)
            proprietario = Proprietario(id=current_user.id, id_metodo_accredito=id, biografia=biografia)
            proprietario.metodo_accredito = metodo 
            proprietario.utente = current_user
            db.session.add(proprietario)
            flash("Profilo proprietario creato con successo.")
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
    id = request.args.get('id')
    if request.method == 'POST':
        proprieta = Proprieta.query.get(id)
        proprieta.descrizione = request.form.get('descrizione')
        db.session.commit()
    
    proprieta = Proprieta.query.get(id)
    return render_template("dettagli_proprieta_proprietario.html", user=current_user, proprieta=proprieta, Amenita=Amenita)

@views.route('/rimuovi_camera', methods=['POST'])
def rimuovi_camera():
    obj = json.loads(request.data)
    id_camera = obj['id_camera']

    camera = Camera.query.get(id_camera)
    camere_da_modificare = db.session.query(Camera).filter(Camera.id_proprieta==camera.id_proprieta, Camera.ordinale > camera.ordinale).all()
    db.session.delete(camera)
    db.session.commit()
    for camera_da_modificare in camere_da_modificare:
        camera_da_modificare.ordinale -= 1
    db.session.commit()
    return jsonify({})

@views.route('/aggiungi_camera', methods=['POST'])
def aggiungi_camera():
    obj = json.loads(request.data)
    id_proprieta = obj['id_proprieta']
    prezzo_per_notte = int(obj['prezzo_per_notte'])
    num_ospiti = int(obj['num_ospiti'])

    proprieta = Proprieta.query.get(id_proprieta)
    ordinale = len(proprieta.camere) + 1
    nuova_camera = Camera(id_proprieta=id_proprieta, ordinale=ordinale, prezzo_per_notte=prezzo_per_notte, num_ospiti=num_ospiti, proprieta=proprieta)

    db.session.add(nuova_camera)
    db.session.commit()
    return jsonify({})

@views.route('/rimuovi_amenita', methods=['POST'])
def remove_amenity():
    obj = json.loads(request.data)
    nome = obj['nome']
    id_proprieta = obj['id_proprieta']
    proprieta = Proprieta.query.get(id_proprieta)
    amenita = Amenita.query.get(nome)
    
    if amenita in proprieta.amenita:
        proprieta.amenita.remove(amenita)
    db.session.commit()
    return jsonify({})

@views.route('/aggiungi_amenita', methods=['POST'])
def aggiungi_amenita():
    obj = json.loads(request.data)
    nome = obj['nome']
    id_proprieta = obj['id_proprieta']

    proprieta = Proprieta.query.get(id_proprieta)
    amenita = Amenita.query.get(nome)
    proprieta.amenita.append(amenita)
    db.session.commit()
    return jsonify({})

@views.route('/rimuovi_proprieta', methods=['POST'])
def rimuovi_proprieta():
    obj = json.loads(request.data)
    id_proprieta = obj['id_proprieta']

    proprieta = Proprieta.query.get(id_proprieta)
    db.session.delete(proprieta)
    db.session.commit()
    return jsonify({})