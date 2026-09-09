"""Local Flask-Admin example; source and BSD license are retained in SOURCE.md."""
import os
from urllib.parse import urlsplit
from uuid import uuid4

import flask_login
from flask import Flask, has_request_context, redirect, render_template, request, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import BaseForm
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect, FlaskForm
from sqlalchemy import Boolean, Integer, String, event, inspect, text
from sqlalchemy.orm import Mapped, Session, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, StringField, validators


db = SQLAlchemy()
login_manager = flask_login.LoginManager()
csrf = CSRFProtect()


class User(db.Model, flask_login.UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    _password: Mapped[str | None] = mapped_column(String(256), nullable=True)
    alternative_id: Mapped[str] = mapped_column(String(32), default=lambda: uuid4().hex, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1", active_history=True)

    @property
    def is_active(self):
        return bool(self.enabled)

    def get_id(self):
        return self.alternative_id

    def __repr__(self):
        return self.username

    @staticmethod
    def get(data, field):
        return db.session.execute(db.select(User).where(getattr(User, field) == data)).scalar_one_or_none()

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        if not value or self.check_password(value):
            return
        self._password = generate_password_hash(value, method="pbkdf2:sha256")
        self.alternative_id = uuid4().hex
        if has_request_context() and flask_login.current_user.is_authenticated and flask_login.current_user.id == self.id:
            flask_login.login_user(self)

    def check_password(self, value):
        return bool(value and self._password and check_password_hash(self._password, value))


@event.listens_for(Session, "before_flush")
def revoke_disabled_sessions(session, flush_context, instances):
    for user in session.dirty:
        if not isinstance(user, User):
            continue
        history = inspect(user).attrs.enabled.history
        if history.has_changes() and history.deleted and bool(history.deleted[0]) and not user.enabled:
            user.alternative_id = uuid4().hex


@login_manager.user_loader
def load_user(marker):
    user = User.get(marker, "alternative_id")
    return user if user is not None and user.enabled else None


class LoginForm(FlaskForm):
    username = StringField(validators=[validators.InputRequired(), validators.Length(max=80)])
    password = PasswordField(validators=[validators.InputRequired()])
    user = None

    def validate_username(self, field):
        self.user = User.get(field.data.strip(), "username")
        if self.user is None or not self.user.enabled:
            raise validators.ValidationError("Invalid credentials or inactive account")

    def validate_password(self, field):
        if self.user is not None and not self.user.check_password(field.data):
            raise validators.ValidationError("Invalid credentials or inactive account")


class RegistrationForm(FlaskForm):
    username = StringField(validators=[validators.InputRequired(), validators.Length(max=80)])
    password = PasswordField(validators=[validators.InputRequired()])

    def validate_username(self, field):
        field.data = field.data.strip()
        if not field.data or User.get(field.data, "username") is not None:
            raise validators.ValidationError("Username unavailable")


class AdminForm(FlaskForm, BaseForm):
    """Keep Flask-WTF CSRF and Flask-Admin object-aware unique validators."""


class MyModelView(ModelView):
    column_list = ("username", "enabled")
    column_filters = ("enabled",)
    column_editable_list = ("username", "enabled")
    form_base_class = AdminForm
    form_columns = ("username", "password", "enabled")
    form_extra_fields = {"password": PasswordField("Password")}

    def is_accessible(self):
        return flask_login.current_user.is_authenticated and flask_login.current_user.is_active

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.login_view", next=request.path))


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not flask_login.current_user.is_authenticated:
            return redirect(url_for(".login_view"))
        return super().index()

    @expose("/login/", methods=("GET", "POST"))
    def login_view(self):
        if flask_login.current_user.is_authenticated:
            return redirect(url_for(".index"))
        form = LoginForm()
        if form.validate_on_submit():
            flask_login.login_user(form.user)
            target = request.args.get("next", "")
            parsed = urlsplit(target)
            if target.startswith("/") and not target.startswith("//") and not parsed.scheme and not parsed.netloc and "\\" not in target:
                return redirect(target)
            return redirect(url_for(".index"))
        return self.render("auth.html", form=form, title="Log in", other_url=url_for(".register_view"), other_label="Register")

    @expose("/register/", methods=("GET", "POST"))
    def register_view(self):
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, enabled=True)
            user.password = form.password.data
            db.session.add(user)
            db.session.commit()
            flask_login.login_user(user)
            return redirect(url_for(".index"))
        return self.render("auth.html", form=form, title="Register", other_url=url_for(".login_view"), other_label="Log in")

    @expose("/logout/", methods=("POST",))
    def logout_view(self):
        flask_login.logout_user()
        return redirect(url_for(".login_view"))


def migrate_database():
    """Add the status column without replacing existing records or authentication IDs."""
    db.create_all()
    with db.engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql('PRAGMA table_info("user")')}
        if "enabled" not in columns:
            connection.exec_driver_sql('ALTER TABLE "user" ADD COLUMN enabled BOOLEAN NOT NULL DEFAULT 1')


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get("ADMIN_DEMO_SECRET"), SQLALCHEMY_DATABASE_URI="sqlite:///db.sqlite", SQLALCHEMY_TRACK_MODIFICATIONS=False, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
    if config:
        app.config.update(config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("ADMIN_DEMO_SECRET or explicit SECRET_KEY is required")
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    admin = Admin(app, name="Example: Auth", index_view=MyAdminIndexView(), theme=Bootstrap4Theme(base_template="my_master.html", fluid=True))
    admin.add_view(MyModelView(User, db.session))

    @app.get("/")
    def index():
        return render_template("index.html")

    with app.app_context():
        migrate_database()
    return app


def build_sample_db():
    """Retained safe initialization: migrate empty or existing tables; never seed/delete."""
    migrate_database()


if __name__ == "__main__":
    create_app().run(debug=False)
