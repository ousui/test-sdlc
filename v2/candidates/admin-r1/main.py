"""Isolated Flask-Admin authentication example with revocable account state."""
import os
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import flask_login
from flask import Flask, abort, has_request_context, jsonify, redirect, render_template, request, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect, FlaskForm
from sqlalchemy import Boolean, Integer, String, event, inspect, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError
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
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default="1")

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        if value and (self._password is None or not self.check_password(value)):
            self._password = generate_password_hash(value, method="pbkdf2:sha256")
            self.alternative_id = uuid4().hex
            if has_request_context() and flask_login.current_user == self:
                flask_login.login_user(self)

    def check_password(self, value):
        return bool(value and self._password and check_password_hash(self._password, value))

    @property
    def is_active(self):
        return bool(self.enabled)

    def get_id(self):
        return self.alternative_id

    def __repr__(self):
        return self.username

    @staticmethod
    def get(value, field):
        return db.session.execute(db.select(User).where(getattr(User, field) == value)).scalar()


@event.listens_for(User.enabled, "set", active_history=True)
def revoke_on_disabled(user, value, old, initiator):
    if old is True and value is not None and not bool(value):
        user.alternative_id = uuid4().hex


@login_manager.user_loader
def load_user(alternative_id):
    user = User.get(alternative_id, "alternative_id")
    return user if user is not None and user.enabled else None


class LoginForm(FlaskForm):
    username = StringField("Username", filters=[lambda value: value.strip() if value else value],
                           validators=[validators.DataRequired(), validators.Length(max=80)])
    password = PasswordField("Password", validators=[validators.DataRequired()])
    user = None

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        self.user = User.get(self.username.data, "username")
        if self.user is None or not self.user.enabled or not self.user.check_password(self.password.data):
            self.password.errors.append("Invalid credentials or inactive account")
            return False
        return True


class RegistrationForm(FlaskForm):
    username = StringField("Username", filters=[lambda value: value.strip() if value else value],
                           validators=[validators.DataRequired(), validators.Length(max=80)])
    password = PasswordField("Password", validators=[validators.DataRequired()])

    def validate_username(self, field):
        if User.get(field.data, "username"):
            raise validators.ValidationError("Username already taken")


class AdminModelForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        self._obj = kwargs.get("obj")
        super().__init__(*args, **kwargs)


class MyModelView(ModelView):
    column_list = ("username", "enabled")
    column_editable_list = ("username", "enabled")
    column_filters = ("enabled",)
    form_excluded_columns = ("alternative_id", "_password")
    form_extra_fields = {"password": PasswordField("Password")}
    form_base_class = AdminModelForm

    def is_accessible(self):
        return flask_login.current_user.is_authenticated and flask_login.current_user.enabled

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.login_view", next=request.path))


def local_next(value):
    if value and value.startswith("/") and not value.startswith("//") and "\\" not in value:
        target = urlsplit(value)
        if not target.netloc and not target.scheme:
            return value
    return url_for("admin.index")


def require_manager():
    if not flask_login.current_user.is_authenticated or not flask_login.current_user.enabled:
        abort(401)


def user_page():
    """One query contract for the HTML page and JSON listing."""
    state = request.args.get("enabled", "all")
    if state not in {"all", "true", "false"}:
        abort(400, description="enabled must be all, true or false")
    numbers = []
    for key, default, maximum in (("page", "1", None), ("per_page", "20", 100)):
        value = request.args.get(key, default)
        if not value.isascii() or not value.isdigit() or len(value) > 9:
            abort(400, description="Invalid pagination")
        number = int(value)
        if number < 1 or (maximum is not None and number > maximum):
            abort(400, description="Invalid pagination")
        numbers.append(number)
    page, per_page = numbers
    query = request.args.get("q", "").strip()
    filters = []
    if state != "all":
        filters.append(User.enabled.is_(state == "true"))
    if query:
        filters.append(db.func.casefold(User.username).contains(query.casefold(), autoescape=True))
    total = db.session.scalar(db.select(db.func.count()).select_from(User).where(*filters))
    users = db.session.scalars(db.select(User).where(*filters).order_by(User.id).offset((page - 1) * per_page).limit(per_page)).all()
    return {"items": [{"id": u.id, "username": u.username, "enabled": u.enabled} for u in users],
            "total": total, "page": page, "per_page": per_page,
            "pages": (total + per_page - 1) // per_page, "enabled": state, "q": query}


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not flask_login.current_user.is_authenticated:
            return redirect(url_for(".login_view"))
        return super().index()

    @expose("/users/data/", methods=("GET",))
    def users_data(self):
        require_manager()
        return jsonify(user_page())

    @expose("/users/bulk/", methods=("GET",))
    def users_bulk(self):
        require_manager()
        return self.render("bulk_users.html", listing=user_page())

    @expose("/users/status/", methods=("POST",))
    def users_status(self):
        require_manager()
        if request.is_json:
            body = request.get_json(silent=True)
            if not isinstance(body, dict):
                return jsonify(error="invalid_request"), 400
            ids, enabled = body.get("ids"), body.get("enabled")
        else:
            raw_ids = request.form.getlist("ids")
            if any(not value.isascii() or not value.isdigit() or len(value) > 19 for value in raw_ids):
                return jsonify(error="invalid_ids"), 400
            ids = [int(value) for value in raw_ids]
            value = request.form.get("enabled")
            enabled = value == "true" if value in {"true", "false"} else None
        if (not isinstance(ids, list) or not 1 <= len(ids) <= 100 or type(enabled) is not bool
                or any(type(identity) is not int or not 1 <= identity <= 9223372036854775807 for identity in ids)):
            return jsonify(error="invalid_request"), 400
        selected = sorted(set(ids))
        if flask_login.current_user.id in selected:
            return jsonify(error="current_account_protected"), 409
        users = db.session.scalars(db.select(User).where(User.id.in_(selected)).order_by(User.id)).all()
        if len(users) != len(selected):
            return jsonify(error="unknown_user"), 404
        changed = 0
        try:
            for user in users:
                if user.enabled != enabled:
                    user.enabled = enabled
                    changed += 1
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify(error="storage_failure"), 503
        if request.is_json:
            return jsonify(requested=len(selected), changed=changed, enabled=enabled)
        return redirect(url_for(".users_bulk", enabled=request.args.get("enabled", "all"),
                                q=request.args.get("q", ""), page=request.args.get("page", "1"),
                                per_page=request.args.get("per_page", "20")))

    @expose("/login/", methods=("GET", "POST"))
    def login_view(self):
        if flask_login.current_user.is_authenticated:
            return redirect(url_for(".index"))
        form = LoginForm()
        if form.validate_on_submit():
            flask_login.login_user(form.user)
            return redirect(local_next(request.args.get("next")))
        return self.render("auth.html", form=form, title="Login", alternate="admin.register_view")

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
        return self.render("auth.html", form=form, title="Register", alternate="admin.login_view")

    @expose("/logout/", methods=("POST",))
    def logout_view(self):
        flask_login.logout_user()
        return redirect(url_for(".login_view"))


def build_sample_db():
    """Create absent tables and apply only the additive legacy enabled migration."""
    db.create_all()
    if db.engine.dialect.name != "sqlite":
        raise RuntimeError("This local example requires SQLite")
    with db.engine.begin() as connection:
        columns = {column["name"] for column in inspect(connection).get_columns("user")}
        if "enabled" not in columns:
            connection.execute(text('ALTER TABLE "user" ADD COLUMN enabled BOOLEAN NOT NULL DEFAULT 1'))


def sqlite_casefold(connection, connection_record):
    connection.create_function("casefold", 1, lambda value: value.casefold() if value is not None else None, deterministic=True)


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("ADMIN_DEMO_SECRET"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("ADMIN_DEMO_DATABASE_URI", "sqlite:///db.sqlite"),
        SQLALCHEMY_ECHO=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Set ADMIN_DEMO_SECRET or provide an explicit application configuration")
    if app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///db.sqlite":
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    admin = Admin(app, name="Example: Auth", index_view=MyAdminIndexView(),
                  theme=Bootstrap4Theme(base_template="my_master.html", fluid=True))
    admin.add_view(MyModelView(User, db.session))
    app.add_url_rule("/", "index", lambda: render_template("index.html"))
    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            event.listen(db.engine, "connect", sqlite_casefold)
        build_sample_db()
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", debug=False)
