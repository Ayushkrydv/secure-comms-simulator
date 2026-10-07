import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../instance/comms.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access the system."
    login_manager.login_message_category = "warning"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.field import field_bp
    from app.routes.command import command_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(field_bp)
    app.register_blueprint(command_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        _seed_default_users()

    return app


def _seed_default_users():
    from app.models import User
    from werkzeug.security import generate_password_hash

    defaults = [
        ("admin", "Admin@123", "admin", "System Administrator"),
        ("personnel_a", "Field@123", "field", "Personnel-Alpha"),
        ("personnel_b", "Field@123", "field", "Personnel-Bravo"),
        ("command_centre", "Cmd@123", "command", "Command Centre"),
    ]
    for username, pw, role, name in defaults:
        if not User.query.filter_by(username=username).first():
            u = User(
                username=username,
                name=name,
                role=role,
                password_hash=generate_password_hash(pw),
                status="active",
            )
            db.session.add(u)
    db.session.commit()
