L'applicazione e' un sito web flask.

E' necessario installare:

    pip install flask
    pip install flask-login
    pip install flask-sqlalchemy

Per lanciare il sito, bisogna avere attiva una connessione a un server MySql e creare un file `website/credentials.py` definendo le variabili.

Esempio di file `credentials.py`:

    user="root"
    password="my_password"
    server="localhost"
    port="5000"

**Il nome del database deve essere `orm_code_first`.**

Infine lanciare `main.py`.