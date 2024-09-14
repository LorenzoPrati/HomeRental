L'applicazione e' un sito web flask.

E' necessario installare:

    pip install flask
    pip install flask-login
    pip install flask-sqlalchemy

Per lanciare il sito, bisogna collegarsi a un server MySql configurando i parametri in un file `credentials.py` da creare dentro la cartella `website/`.

Esempio di file `credentials.py`:

    user="root"
    password="my_password"
    server="localhost"
    port="5000"

Il database MySql deve essere stato **già creato vuoto** con il nome `orm_code_first`.

Infine lanciare `main.py`.