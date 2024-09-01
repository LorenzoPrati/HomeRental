from flask import Blueprint, render_template, request, url_for, flash, redirect, json, jsonify
from flask_login import login_required, current_user
from .models import Carta_Credito, Coupon, Metodo_Pagamento, Pagamento, Paypal, Tipo_Metodo_Pagamento, Tipo_Struttura, Proprieta, Proprietario, Camera, Amenita, servizi, Citta, Soggiorno, occupazioni, Recensione, spendibilita_coupons
from . import db
from sqlalchemy import func
import datetime

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        citta = request.form.getlist('citta')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        num_ospiti = request.form.get('num_ospiti')
        tipo_struttura = request.form.get('tipo_struttura')
        amenita_selezionate = request.form.getlist('amenita_selezionate')

        if check_in and check_out:
            if not num_ospiti:
                num_ospiti=1
            elif int(num_ospiti) <= 0:
                num_ospiti = 1
            return redirect(url_for('views.ricerca', citta=citta, check_in=check_in, check_out=check_out, num_ospiti=num_ospiti, tipo_struttura=tipo_struttura, amenita_selezionate=amenita_selezionate))
        else:
            flash('Inserisci delle date di inizio e fine soggiorno', category='error')

    return render_template("home.html", user=current_user, Citta=Citta, Tipo_Struttura=Tipo_Struttura, Amenita=Amenita)

@views.route('/ricerca', methods=['GET', 'POST'])
@login_required
def ricerca():
    citta = request.args.getlist('citta')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    num_ospiti = request.args.get('num_ospiti')
    tipo_struttura = request.args.getlist('tipo_struttura')
    amenita_selezionate = request.args.getlist('amenita_selezionate')

    if not citta:
        citta = [c.nome for c in db.session.query(Citta).all()]

    if not tipo_struttura:
        tipo_struttura = [t.nome for t in db.session.query(Tipo_Struttura).all()]
    
    if not amenita_selezionate:
        id_proprieta_valide = db.session.query(Proprieta.id).outerjoin(servizi).filter(Proprieta.id_citta.in_(citta)).filter(Proprieta.id_tipo_struttura.in_(tipo_struttura)).distinct().subquery()
    else:
        id_proprieta_valide = db.session.query(Proprieta.id).outerjoin(servizi).filter(servizi.c.id_amenita.in_(amenita_selezionate)).group_by(Proprieta.id).having(func.count()==len(amenita_selezionate)).filter(Proprieta.id_citta.in_(citta)).filter(Proprieta.id_tipo_struttura.in_(tipo_struttura)).distinct().subquery()
    
    id_camere_occupate = db.session.query(Camera.id).outerjoin(occupazioni).outerjoin(Soggiorno).filter(check_in<=Soggiorno.check_out, check_out>=Soggiorno.check_in).distinct().subquery()
    
    lista_proprieta = db.session.query(Proprieta).join(Camera).filter(Camera.id.not_in(id_camere_occupate), Proprieta.id.in_(id_proprieta_valide)).group_by(Proprieta.id).having(func.sum(Camera.num_ospiti)>=num_ospiti).all()
    
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
    id_proprieta = request.args.get('id_proprieta')
    proprieta = Proprieta.query.get(id_proprieta)

    if request.method == 'POST':
        camere = []
        prezzo = 0
        lista_camere_prenotate = request.form.getlist('camere_prenotate')
        id_metodo_pagamento = request.form.get('id_metodo_pagamento')
        id_coupon = request.form.get('id_coupon')

        start_date = datetime.datetime.strptime(check_in, '%Y-%m-%dT%H:%M')
        end_date = datetime.datetime.strptime(check_out, '%Y-%m-%dT%H:%M')
        delta = end_date - start_date
        num_notti = delta.days

        for id in lista_camere_prenotate:
            camera = Camera.query.get(id)
            camere.append(camera)
            prezzo += (camera.prezzo_per_notte * num_notti)
        if len(camere) == 0 and not id_metodo_pagamento:
            flash('Errore.', category='error')
        else:
            soggiorno = Soggiorno(check_in=check_in, check_out=check_out, num_ospiti=num_ospiti, prezzo=prezzo, id_utente=current_user.id, utente=current_user, camere=camere)
            db.session.add(soggiorno)
            db.session.commit()

            pagamento = Pagamento(id_soggiorno=soggiorno.id, 
                                  id_metodo_pagamento = id_metodo_pagamento,
                                  id_coupon=id_coupon)
            if id_coupon:
                coupon = Coupon.query.get(id_coupon)
                pagamento.coupon = coupon

            db.session.add(pagamento)
            db.session.commit()

            flash('Prenotazione effettuata con successo.', category='success')
            return redirect(url_for('views.prenotazioni'))
    
    id_camere_occupate = db.session.query(Camera.id).outerjoin(occupazioni).outerjoin(Soggiorno).filter(check_in<=Soggiorno.check_out, check_out>=Soggiorno.check_in).distinct().subquery()
    
    camere_libere = db.session.query(Camera).filter(Camera.id.not_in(id_camere_occupate), Camera.id_proprieta==id_proprieta).all()
    
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
            proprieta.valutazione_media = (proprieta.valutazione_media * proprieta.num_valutazioni - vecchia_recensione.valutazione + int(valutazione)) / proprieta.num_valutazioni
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

@views.route('/aggiungi_carta', methods=['GET', 'POST'])
@login_required
def aggiungi_carta():
    flag = request.args.get('flag')

    if request.method == 'POST':
        numero_carta = request.form.get('numero_carta')
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        data_scadenza = request.form.get('data_scadenza')
        metodo_pagamento = Metodo_Pagamento(id_utente=current_user.id, tipo=Tipo_Metodo_Pagamento.CARTA_CREDITO.value)
        carta = Carta_Credito(numero_carta=numero_carta, nome=nome, cognome=cognome, data_scadenza=data_scadenza)
        carta.id = metodo_pagamento.id
        metodo_pagamento.carta_credito = carta
        metodo_pagamento.utente = current_user
        db.session.add(metodo_pagamento)
        db.session.commit()
        flash('Metodo di pagamento aggiunto con successo.', category='success')

        if flag:
            return redirect(url_for('views.aggiungi_proprieta'))
        else:
            return redirect(url_for('views.metodi_pagamento'))

    return render_template("aggiungi_carta.html", user=current_user)

@views.route('/aggiungi_paypal', methods=['GET', 'POST'])
@login_required
def aggiungi_paypal():
    flag = request.args.get('flag')

    if request.method == 'POST':

        email = request.form.get('email')
        metodo_pagamento = Metodo_Pagamento(id_utente=current_user.id, tipo=Tipo_Metodo_Pagamento.PAYPAL.value)
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
            telefono = request.form.get('telefono')
            metodo = Metodo_Pagamento.query.get(id)
            proprietario = Proprietario(id=current_user.id, id_metodo_accredito=id, biografia=biografia, telefono=telefono)
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
    soggiorni = db.session.query(Soggiorno).outerjoin(Soggiorno.camere).filter(Camera.id_proprieta==id_proprieta, Soggiorno.check_in >= datetime.datetime.now()).distinct().all()
    db.session.delete(proprieta)
    for soggiorno in soggiorni:
        db.session.delete(soggiorno)
    db.session.commit()
    return jsonify({})

@views.route('/migliori_host', methods=['GET', 'POST'])
@login_required
def migliori_host():
    valutazione_media_globale = db.session.query(func.avg(Proprietario.valutazione_media)).subquery()
    proprietari = db.session.query(Proprietario)\
        .order_by(((Proprietario.valutazione_media * Proprietario.num_valutazioni) / (Proprietario.num_valutazioni + 10)) + \
                            ((10 * valutazione_media_globale.as_scalar()) / (Proprietario.num_valutazioni + 10)))\
        .limit(10)
    
    return render_template("migliori_host.html", user=current_user, proprietari=proprietari)

@views.route('/citta_popolari', methods=['GET', 'POST'])
@login_required
def citta_popolari():
    start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    end_date = datetime.datetime.now()

    citta = db.session.query(Proprieta.id_citta.label('citta'), func.count(func.distinct(Soggiorno.id)).label('numero_soggiorni'))\
        .outerjoin(Proprieta.camere)\
        .outerjoin(Camera.soggiorni)\
        .filter(Soggiorno.check_in >= start_date, Soggiorno.check_out <= end_date)\
        .group_by(Proprieta.id)\
        .order_by(func.count(func.distinct(Soggiorno.id)).desc())\
        .limit(5)

    return render_template("citta_popolari.html", user=current_user, citta=citta)

@views.route('/migliori_proprieta', methods=['GET', 'POST'])
@login_required
def migliori_proprieta():
    valutazione_media_globale = db.session.query(func.avg(Proprieta.valutazione_media)).subquery()
    proprieta = db.session.query(Proprieta)\
        .order_by(((Proprieta.valutazione_media * Proprietario.num_valutazioni) / (Proprieta.num_valutazioni + 10)) + \
                            ((10 * valutazione_media_globale.as_scalar()) / (Proprieta.num_valutazioni + 10)))\
        .limit(10)

    return render_template("migliori_proprieta.html", user=current_user, proprieta=proprieta)

@views.route('/amenita_apprezzate', methods=['GET', 'POST'])
@login_required
def amenita_apprezzate():
    soglia_num_valutazioni = 0
    soglia_valutazione_media = 0

    amenita = db.session.query(Amenita).join(Amenita.proprieta)\
        .filter(Proprieta.valutazione_media >= soglia_valutazione_media, Proprieta.num_valutazioni >= soglia_num_valutazioni)\
        .group_by(Amenita.nome)\
        .order_by(func.count().desc())

    return render_template("amenita_apprezzate.html", user=current_user, amenita=amenita)