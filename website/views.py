from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
    flash,
    redirect,
    json,
    jsonify,
)
from flask_login import login_required, current_user
from .models import (
    Carta_Credito,
    Coupon,
    Metodo_Pagamento,
    Pagamento,
    Paypal,
    Tipo_Metodo_Pagamento,
    Tipo_Struttura,
    Proprieta,
    Proprietario,
    Camera,
    Amenita,
    Utente,
    servizi,
    Citta,
    Soggiorno,
    occupazioni,
    Recensione,
    spendibilita_coupons,
)
from . import db
from sqlalchemy import func, or_, select
import datetime

views = Blueprint("views", __name__)


@views.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        citta = request.form.getlist("citta")
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")
        num_ospiti = request.form.get("num_ospiti")
        tipi_struttura = request.form.getlist("tipi_struttura")
        amenita = request.form.getlist("amenita")

        if check_in and check_out:
            start_date = datetime.datetime.strptime(check_in, "%Y-%m-%dT%H:%M")
            end_date = datetime.datetime.strptime(check_out, "%Y-%m-%dT%H:%M")

            if (
                start_date
                and end_date
                and start_date > datetime.datetime.now()
                and end_date > start_date
            ):
                if not num_ospiti:
                    num_ospiti = 1
                elif int(num_ospiti) <= 0:
                    num_ospiti = 1
                return redirect(
                    url_for(
                        "views.ricerca",
                        citta=citta,
                        check_in=check_in,
                        check_out=check_out,
                        num_ospiti=num_ospiti,
                        tipi_struttura=tipi_struttura,
                        amenita=amenita,
                    )
                )
            else:
                flash("Errore: Date non valide.", category="error")
        else:
            flash("Errore: Inserisce delle date.", category="error")

    citta = Citta.query.all()
    tipi_struttura = Tipo_Struttura.query.all()
    amenita = Amenita.query.all()

    soggiorno = (
        db.session.query(Soggiorno)
        .filter(
            Soggiorno.id_utente == current_user.id,
            Soggiorno.data_cancellazione.is_(None),
            Soggiorno.check_in > datetime.datetime.now(),
        )
        .order_by(Soggiorno.check_in)
        .first()
    )

    giorni = 0
    ore = 0
    if soggiorno:
        tempo_mancante = soggiorno.check_in - datetime.datetime.now()
        giorni = tempo_mancante.days
        ore = tempo_mancante.seconds // 3600

    return render_template(
        "home.html",
        user=current_user,
        citta=citta,
        tipi_struttura=tipi_struttura,
        amenita=amenita,
        soggiorno=soggiorno,
        giorni=giorni,
        ore=ore,
    )


@views.route("/ricerca", methods=["GET", "POST"])
@login_required
def ricerca():
    citta = request.args.getlist("citta")
    check_in = request.args.get("check_in")
    check_out = request.args.get("check_out")
    num_ospiti = request.args.get("num_ospiti")
    tipi_struttura = request.args.getlist("tipi_struttura")
    amenita = request.args.getlist("amenita")

    if not citta:
        citta = [c.nome for c in db.session.query(Citta).all()]
    if not tipi_struttura:
        tipi_struttura = [t.nome for t in db.session.query(Tipo_Struttura).all()]

    if not amenita:
        proprieta_valide = (
            select(
                Proprieta.id.label("id"),
                Proprieta.id_citta.label("id_citta"),
                Proprieta.indirizzo.label("indirizzo"),
                Proprieta.id_tipo_struttura.label("id_tipo_struttura"),
                Proprieta.valutazione_media.label("valutazione_media"),
                Proprieta.num_valutazioni.label("num_valutazioni"),
                Utente.nome.label("nome"),
                Utente.cognome.label("cognome"),
            )
            .select_from(Proprieta)
            .join(Proprietario)
            .join(Utente)
            .where(
                Proprieta.id_proprietario != current_user.id,
                Proprieta.data_rimozione.is_(None),
                Proprieta.id_citta.in_(citta),
                Proprieta.id_tipo_struttura.in_(tipi_struttura),
            )
            .cte("proprieta_valide")
        )
    else:
        proprieta_valide = (
            select(
                Proprieta.id.label("id"),
                Proprieta.id_citta.label("id_citta"),
                Proprieta.indirizzo.label("indirizzo"),
                Proprieta.id_tipo_struttura.label("id_tipo_struttura"),
                Proprieta.valutazione_media.label("valutazione_media"),
                Proprieta.num_valutazioni.label("num_valutazioni"),
                Utente.nome.label("nome"),
                Utente.cognome.label("cognome"),
            )
            .select_from(Proprieta)
            .join(Proprietario)
            .join(Utente)
            .join(servizi)  # outer ?
            .where(
                Proprieta.id_proprietario != current_user.id,
                Proprieta.data_rimozione.is_(None),
                Proprieta.id_citta.in_(citta),
                Proprieta.id_tipo_struttura.in_(tipi_struttura),
                servizi.c.id_amenita.in_(amenita),
            )
            .group_by(Proprieta.id)
            .having(
                func.count() == len(amenita)
            )  # func.count(distinct servizi.c.id_amenita)
            .distinct()
            .cte("proprieta_valide")
        )

    # res = db.session.execute(proprieta_valide).fetchall()

    camere_libere = (
        select(
            Camera.id.distinct(),
            Camera.num_ospiti.label("num_ospiti"),
            proprieta_valide,
        )
        .select_from(proprieta_valide)
        .join(Camera, proprieta_valide.c.id == Camera.id_proprieta)  # on clause ?
        .outerjoin(occupazioni)
        .outerjoin(Soggiorno)
        .filter(
            Camera.data_rimozione.is_(None),
            or_(
                Soggiorno.id.is_(None),
                Soggiorno.data_cancellazione.isnot(None),  # is ?
                check_in > Soggiorno.check_out,
                check_out < Soggiorno.check_in,
            ),
        )
        .cte("camere_libere")
    )

    lista_proprieta = (
        select(
            camere_libere.c.id,
            camere_libere.c.id_citta.label("id_citta"),
            camere_libere.c.indirizzo.label("indirizzo"),
            camere_libere.c.id_tipo_struttura.label("id_tipo_struttura"),
            camere_libere.c.nome.label("nome"),
            camere_libere.c.cognome.label("cognome"),
            camere_libere.c.valutazione_media.label("valutaione_media"),
            camere_libere.c.num_valutazioni.label("num_valutazioni"),
        )
        .select_from(camere_libere)
        .group_by(camere_libere.c.id)
        .having(func.sum(camere_libere.c.num_ospiti) >= num_ospiti)
    )

    lista_proprieta = db.session.execute(lista_proprieta).fetchall()

    return render_template(
        "ricerca.html",
        user=current_user,
        citta=citta,
        proprieta=lista_proprieta,
        check_in=check_in,
        check_out=check_out,
        num_ospiti=num_ospiti,
    )


@views.route("/tuoi_soggiorni")
@login_required
def tuoi_soggiorni():
    soggiorni = (
        db.session.query(Soggiorno)
        .filter(Soggiorno.id_utente == current_user.id)
        .join(Pagamento)
        .order_by(Pagamento.data_creazione.desc())
        .all()
    )

    return render_template(
        "tuoi_soggiorni.html",
        user=current_user,
        soggiorni=soggiorni,
        now=datetime.datetime.now(),
    )


@views.route("/prenota_proprieta", methods=["GET", "POST"])
@login_required
def prenota_proprieta():
    citta = request.args.get("citta")
    check_in = request.args.get("check_in")
    check_out = request.args.get("check_out")
    num_ospiti = request.args.get("num_ospiti")
    id_proprieta = request.args.get("id_proprieta")
    proprieta = Proprieta.query.get(id_proprieta)

    camere = (
        db.session.query(Camera)
        .outerjoin(occupazioni)
        .outerjoin(Soggiorno)
        .filter(
            Camera.data_rimozione.is_(None),
            Camera.id_proprieta == proprieta.id,
            or_(
                Soggiorno.id.is_(None),
                Soggiorno.data_cancellazione.isnot(None),
                check_in > Soggiorno.check_out,
                check_out < Soggiorno.check_in,
            ),
        )
        .distinct()
    )

    if request.method == "POST":
        id_camere = request.form.getlist("camere_prenotate")
        id_metodo_pagamento = request.form.get("id_metodo_pagamento")
        id_coupon = request.form.get("id_coupon")

        start_date = datetime.datetime.strptime(check_in, "%Y-%m-%dT%H:%M")
        end_date = datetime.datetime.strptime(check_out, "%Y-%m-%dT%H:%M")
        delta = end_date - start_date
        num_notti = delta.days

        if id_camere and id_metodo_pagamento:
            camere = db.session.query(Camera).filter(Camera.id.in_(id_camere)).all()

            prezzo = 0
            for c in camere:
                prezzo += c.prezzo_per_notte * num_notti

            soggiorno = Soggiorno(
                check_in=check_in,
                check_out=check_out,
                num_ospiti=num_ospiti,
                prezzo=prezzo,
                id_utente=current_user.id,
                utente=current_user,
                camere=camere,
            )
            """db.session.add(soggiorno)
            db.session.commit()"""

            pagamento = Pagamento(
                id_metodo_addebito=id_metodo_pagamento,
                id_metodo_accredito=proprieta.proprietario.id_metodo_accredito,
            )
            pagamento.id = soggiorno.id
            pagamento.soggiorno = soggiorno
            if id_coupon:
                pagamento.id_coupon = id_coupon
                coupon = Coupon.query.get(id_coupon)
                pagamento.coupon = coupon

            db.session.add(soggiorno)
            db.session.commit()

            flash("Prenotazione effettuata.", category="success")

            return redirect(url_for("views.tuoi_soggiorni"))
        else:
            flash(
                "Errore: mancano informazioni necessarie per effettuare la prenotazione (camere e/o metodo di pagamento) e/o camere non più libere.",
                category="error",
            )

    coupons = (
        db.session.query(Coupon)
        .outerjoin(Pagamento)
        .outerjoin(spendibilita_coupons)
        .filter(
            spendibilita_coupons.c.id_tipo_struttura == proprieta.id_tipo_struttura,
            Coupon.id_utente == current_user.id,
            Pagamento.id_coupon.is_(None),
        )
        .all()
    )

    return render_template(
        "prenota_proprieta.html",
        user=current_user,
        citta=citta,
        check_in=check_in,
        check_out=check_out,
        num_ospiti=num_ospiti,
        proprieta=proprieta,
        camere=camere,
        coupons=coupons,
    )


@views.route("/scrivi_recensione", methods=["GET", "POST"])
@login_required
def scrivi_recensione():
    id_proprieta = request.args.get("id_proprieta")
    vecchia_recensione = Recensione.query.get((current_user.id, id_proprieta))

    if request.method == "POST":
        valutazione = request.form.get("valutazione")
        testo = request.form.get("testo")
        proprieta = Proprieta.query.get(id_proprieta)

        if testo and valutazione:
            if vecchia_recensione:
                vecchia_valutazione_media = proprieta.valutazione_media

                proprieta.valutazione_media = (
                    proprieta.valutazione_media * proprieta.num_valutazioni
                    - vecchia_recensione.valutazione
                    + int(valutazione)
                ) / proprieta.num_valutazioni

                proprietario = proprieta.proprietario
                proprietario.valutazione_media = (
                    proprietario.valutazione_media * proprietario.num_valutazioni
                    - vecchia_valutazione_media
                    + proprieta.valutazione_media
                ) / proprietario.num_valutazioni

                vecchia_recensione.testo = testo
                vecchia_recensione.valutazione = valutazione
                vecchia_recensione.data_ultima_modifica = datetime.datetime.now()

                db.session.commit()

                flash("Recensione modificata.", category="success")
            else:
                recensione = Recensione(
                    valutazione=valutazione,
                    testo=testo,
                    id_utente=current_user.id,
                    id_proprieta=proprieta.id,
                    utente=current_user,
                    proprieta=proprieta,
                    data_ultima_modifica=datetime.datetime.now(),
                )

                proprieta.valutazione_media = (
                    proprieta.valutazione_media * proprieta.num_valutazioni
                    + int(valutazione)
                ) / (proprieta.num_valutazioni + 1)
                proprieta.num_valutazioni += 1

                proprietario = proprieta.proprietario
                proprietario.valutazione_media = (
                    proprietario.valutazione_media * proprietario.num_valutazioni
                    + proprieta.valutazione_media
                ) / (proprietario.num_valutazioni + 1)
                proprietario.num_valutazioni += 1

                db.session.add(recensione)
                db.session.commit()

                flash("Recensione pubblicata.", category="success")
        else:
            flash("Errore: mancano valutazione e/o testo.", category="error")

    return render_template(
        "scrivi_recensione.html",
        user=current_user,
        vecchia_recensione=vecchia_recensione,
    )


@views.route("/profilo", methods=["GET", "POST"])
@login_required
def profilo():
    if request.method == "POST":
        biografia = request.form.get("biografia")
        telefono = request.form.get("telefono")
        if biografia:
            current_user.proprietario.biografia = biografia
        if telefono:
            current_user.proprietario.telefono = telefono
        db.session.commit()

    return render_template("profilo.html", user=current_user)


@views.route("/tue_proprieta", methods=["GET", "POST"])
@login_required
def tue_proprieta():
    flag = True

    return render_template("tue_proprieta.html", user=current_user, flag=flag)


@views.route("/pagamento", methods=["GET", "POST"])
@login_required
def pagamento():
    id_pagamento = request.args.get("id_pagamento")
    pagamento = Pagamento.query.get(id_pagamento)

    return render_template("pagamento.html", user=current_user, pagamento=pagamento)


@views.route("/metodi_pagamento", methods=["GET", "POST"])
@login_required
def metodi_pagamento():
    flag = request.args.get("flag")

    if request.method == "POST":
        id_metodo_accredito = request.form.get("id_metodo_accredito")
        if id_metodo_accredito:
            metodo_accredito = Metodo_Pagamento.query.get(id_metodo_accredito)
            current_user.proprietario.metodo_accredito = metodo_accredito

            db.session.commit()

            flash("Metodo di accredito modificato.")

    return render_template("metodi_pagamento.html", user=current_user, flag=flag)


@views.route("/aggiungi_carta", methods=["GET", "POST"])
@login_required
def aggiungi_carta():
    flag = request.args.get("flag")

    if request.method == "POST":
        numero_carta = request.form.get("numero_carta")
        nome = request.form.get("nome")
        cognome = request.form.get("cognome")
        data_scadenza = request.form.get("data_scadenza")

        carta = (
            db.session.query(Carta_Credito)
            .filter(Carta_Credito.numero_carta == numero_carta)
            .first()
        )
        if carta:
            flash("Carta già registrata.", category="error")
        else:
            metodo_pagamento = Metodo_Pagamento(
                id_utente=current_user.id, tipo=Tipo_Metodo_Pagamento.CARTA_CREDITO.name
            )

            carta = Carta_Credito(
                numero_carta=numero_carta,
                nome=nome,
                cognome=cognome,
                data_scadenza=data_scadenza,
            )
            carta.id = metodo_pagamento.id

            metodo_pagamento.carta_credito = carta
            metodo_pagamento.utente = current_user

            db.session.add(metodo_pagamento)
            db.session.commit()

            if flag:
                return redirect(url_for("views.aggiungi_proprieta"))
            else:
                return redirect(url_for("views.metodi_pagamento"))

    return render_template("aggiungi_carta.html", user=current_user)


@views.route("/aggiungi_paypal", methods=["GET", "POST"])
@login_required
def aggiungi_paypal():
    flag = request.args.get("flag")

    if request.method == "POST":
        email = request.form.get("email")

        paypal = db.session.query(Paypal).filter(Paypal.email == email).first()
        if paypal:
            flash("Paypal già registrato.", category="error")
        else:
            metodo_pagamento = Metodo_Pagamento(
                id_utente=current_user.id, tipo=Tipo_Metodo_Pagamento.PAYPAL.name
            )

            paypal = Paypal(email=email)
            paypal.id = metodo_pagamento.id

            metodo_pagamento.paypal = paypal
            metodo_pagamento.utente = current_user

            db.session.add(metodo_pagamento)
            db.session.commit()

            if flag:
                return redirect(url_for("views.aggiungi_proprieta"))
            else:
                return redirect(url_for("views.metodi_pagamento"))

    return render_template("aggiungi_paypal.html", user=current_user)


@views.route("/soggiorni_tua_proprieta", methods=["GET", "POST"])
@login_required
def soggiorni_tua_proprieta():
    id_proprieta = request.args.get("id")
    proprieta = Proprieta.query.get(id_proprieta)

    soggiorni = (
        db.session.query(Soggiorno)
        .outerjoin(occupazioni)
        .join(Camera)
        .filter(Camera.id_proprieta == id_proprieta)
        .order_by(Soggiorno.check_in)
        .distinct()
        .all()
    )

    return render_template(
        "soggiorni_tua_proprieta.html",
        user=current_user,
        proprieta=proprieta,
        soggiorni=soggiorni,
        now=datetime.datetime.now(),
    )


@views.route("/recensioni_tua_proprieta", methods=["GET", "POST"])
@login_required
def recensioni_tua_proprieta():
    id_proprieta = request.args.get("id")
    proprieta = Proprieta.query.get(id_proprieta)

    return render_template(
        "recensioni_tua_proprieta.html", user=current_user, proprieta=proprieta
    )


@views.route("/aggiungi_proprieta", methods=["GET", "POST"])
@login_required
def aggiungi_proprieta():
    citta = Citta.query.all()
    tipi_struttura = Tipo_Struttura.query.all()

    if request.method == "POST":
        indirizzo = request.form.get("indirizzo")
        id_citta = request.form.get("citta")
        id_tipo_struttura = request.form.get("tipo_struttura")
        descrizione = request.form.get("descrizione")

        if indirizzo and id_citta and id_tipo_struttura:
            proprieta = Proprieta(
                indirizzo=indirizzo,
                id_citta=id_citta,
                id_tipo_struttura=id_tipo_struttura,
            )

            if descrizione:
                proprieta.descrizione = descrizione

            if not current_user.proprietario:
                id_metodo_pagamento = request.form.get("metodo_pagamento")
                biografia = request.form.get("biografia")
                telefono = request.form.get("telefono")

                metodo_pagamento = Metodo_Pagamento.query.get(id_metodo_pagamento)
                proprietario = Proprietario(
                    id=current_user.id,
                    id_metodo_accredito=id_metodo_pagamento,
                    biografia=biografia,
                    telefono=telefono,
                )
                proprietario.metodo_accredito = metodo_pagamento
                proprietario.utente = current_user

                db.session.add(proprietario)

                flash("Profilo host creato.", category="success")

            proprieta.id_proprietario = current_user.proprietario.id
            proprieta.proprietario = current_user.proprietario

            db.session.add(proprieta)
            db.session.commit()

            return redirect(url_for("views.modifica_proprieta", id=proprieta.id))
        else:
            flash(
                "Errore. Mancano città e/o tipo struttura e/o l'indirizzo.",
                category="error",
            )

    return render_template(
        "aggiungi_proprieta.html",
        user=current_user,
        citta=citta,
        tipi_struttura=tipi_struttura,
    )


@views.route("/modifica_proprieta", methods=["GET", "POST"])
@login_required
def modifica_proprieta():
    id = request.args.get("id")
    proprieta = Proprieta.query.get(id)

    amenita = Amenita.query.all()

    if request.method == "POST":
        descrizione = request.form.get("descrizione")
        if descrizione:
            proprieta.descrizione = descrizione
        db.session.commit()

    if proprieta.proprietario.id == current_user.id:
        return render_template(
            "modifica_proprieta.html",
            user=current_user,
            proprieta=proprieta,
            amenita=amenita,
        )


@views.route("/rimuovi_camera", methods=["POST"])
@login_required
def rimuovi_camera():
    obj = json.loads(request.data)
    id_camera = obj["id_camera"]

    camera = Camera.query.get(id_camera)

    camera.data_rimozione = datetime.datetime.now()

    camere_da_modificare = (
        db.session.query(Camera)
        .filter(
            Camera.id_proprieta == camera.id_proprieta,
            Camera.ordinale > camera.ordinale,
            Camera.data_rimozione.is_(None),
        )
        .all()
    )

    for camera_da_modificare in camere_da_modificare:
        camera_da_modificare.ordinale -= 1

    """Setto cancellati solo i soggiorni non ancora compiuti"""
    for s in camera.soggiorni:
        if not s.data_cancellazione and s.check_in > datetime.datetime.now():
            s.data_cancellazione = datetime.datetime.now()

    db.session.commit()

    return jsonify({})


@views.route("/aggiungi_camera", methods=["POST"])
@login_required
def aggiungi_camera():
    obj = json.loads(request.data)
    id_proprieta = obj["id_proprieta"]
    prezzo_per_notte = int(obj["prezzo_per_notte"])
    num_ospiti = int(obj["num_ospiti"])
    descrizione_camera = obj["descrizione_camera"]
    proprieta = Proprieta.query.get(id_proprieta)

    camere = [
        c
        for c in db.session.query(Camera)
        .filter(Camera.id_proprieta == proprieta.id, Camera.data_rimozione.is_(None))
        .all()
    ]

    ordinale = len(camere) + 1

    nuova_camera = Camera(
        id_proprieta=id_proprieta,
        ordinale=ordinale,
        prezzo_per_notte=prezzo_per_notte,
        num_ospiti=num_ospiti,
        descrizione=descrizione_camera,
        proprieta=proprieta,
    )

    db.session.add(nuova_camera)
    db.session.commit()

    return jsonify({})


@views.route("/rimuovi_amenita", methods=["POST"])
def remove_amenity():
    obj = json.loads(request.data)
    nome = obj["nome"]
    id_proprieta = obj["id_proprieta"]

    proprieta = Proprieta.query.get(id_proprieta)
    amenita = Amenita.query.get(nome)

    if amenita in proprieta.amenita:
        proprieta.amenita.remove(amenita)

    db.session.commit()

    return jsonify({})


@views.route("/aggiungi_amenita", methods=["POST"])
def aggiungi_amenita():
    obj = json.loads(request.data)
    nome = obj["nome"]
    id_proprieta = obj["id_proprieta"]

    proprieta = Proprieta.query.get(id_proprieta)
    amenita = Amenita.query.get(nome)

    proprieta.amenita.append(amenita)

    db.session.commit()

    return jsonify({})


@views.route("/rimuovi_proprieta", methods=["POST"])
def rimuovi_proprieta():
    obj = json.loads(request.data)
    id_proprieta = obj["id_proprieta"]

    proprieta = Proprieta.query.get(id_proprieta)
    proprieta.data_rimozione = datetime.datetime.now()

    soggiorni = (
        db.session.query(Soggiorno)
        .outerjoin(occupazioni)
        .join(Camera)
        .filter(
            Camera.id_proprieta == id_proprieta,
            Soggiorno.data_cancellazione.is_(None),
            Soggiorno.check_in > datetime.datetime.now(),
        )
        .distinct()
    )

    for s in soggiorni:
        s.data_cancellazione = datetime.datetime.now()

    for c in proprieta.camere:
        if not c.data_rimozione:
            c.data_rimozione = datetime.datetime.now()

    db.session.commit()

    return jsonify({})


@views.route("/annulla_soggiorno", methods=["GET", "POST"])
@login_required
def annulla_soggiorno():
    obj = json.loads(request.data)
    id_soggiorno = obj["id_soggiorno"]

    soggiorno = Soggiorno.query.get(id_soggiorno)

    if not soggiorno.data_cancellazione:
        soggiorno.data_cancellazione = datetime.datetime.now()

    db.session.commit()

    return jsonify({})


@views.route("/migliori_host", methods=["GET", "POST"])
@login_required
def migliori_host():
    valutazione_media_globale = db.session.query(
        func.avg(Proprietario.valutazione_media)
    ).subquery()

    proprietari = (
        db.session.query(Proprietario)
        .order_by(
            (
                (Proprietario.valutazione_media * Proprietario.num_valutazioni)
                / (Proprietario.num_valutazioni + 10)
            )
            + (
                (10 * valutazione_media_globale.as_scalar())
                / (Proprietario.num_valutazioni + 10)
            ).desc()
        )
        .limit(10)
    )

    return render_template(
        "migliori_host.html", user=current_user, proprietari=proprietari
    )


@views.route("/citta_popolari", methods=["GET", "POST"])
@login_required
def citta_popolari():
    start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    end_date = datetime.datetime.now()

    citta = (
        db.session.query(
            Proprieta.id_citta.label("citta"),
            func.count(func.distinct(Soggiorno.id)).label("numero_soggiorni"),
        )
        .outerjoin(Proprieta.camere)
        .outerjoin(Camera.soggiorni)
        .filter(
            Soggiorno.data_cancellazione.is_(None),
            Soggiorno.check_in >= start_date,
            Soggiorno.check_out <= end_date,
        )
        .group_by(Proprieta.id)
        .order_by(func.count(func.distinct(Soggiorno.id)).desc())
        .limit(5)
    )

    return render_template("citta_popolari.html", user=current_user, citta=citta)


@views.route("/migliori_citta", methods=["GET", "POST"])
@login_required
def migliori_citta():
    citta = (
        db.session.query(
            Proprieta.id_citta.label("id_citta"),
            func.avg(Proprieta.valutazione_media).label("valutazione_media"),
        )
        .filter(Proprieta.data_rimozione.is_(None), Proprieta.num_valutazioni > 0)
        .group_by(Proprieta.id_citta)
        .limit(5)
    )

    return render_template("migliori_citta.html", user=current_user, citta=citta)


@views.route("/amenita_apprezzate", methods=["GET", "POST"])
@login_required
def amenita_apprezzate():
    amenita = (
        db.session.query(Amenita)
        .join(Amenita.proprieta)
        .filter(
            Proprieta.data_rimozione.is_(None),
            Proprieta.valutazione_media >= 2,
            Proprieta.num_valutazioni >= 1,
        )
        .group_by(Amenita.nome)
        .order_by(func.count().desc())
        .limit(5)
    )

    return render_template(
        "amenita_apprezzate.html", user=current_user, amenita=amenita
    )
