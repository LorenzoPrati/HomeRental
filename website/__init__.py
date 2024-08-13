from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from .credentials import user as db_user
from .credentials import password as db_password
from .credentials import server as db_server
from .credentials import port as db_port

db = SQLAlchemy()
DB_NAME = 'orm_code_first'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'raxephon'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_server}:{db_port}/orm_code_first'
    app.config['SQLALCHEMY_ECHO'] = True #To see raw SQL
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import Utente

    with app.app_context():
        db.create_all()
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Utente.query.get((int(id)))

    return app
           