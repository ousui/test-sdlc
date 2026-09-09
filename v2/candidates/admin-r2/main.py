"""Isolated Flask-Admin authentication example with revocable account state."""
import os
import hashlib
import json
import re
from datetime import datetime, timezone
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
from sqlalchemy import Boolean, ForeignKey, Integer, String, event, inspect, text
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
    audit_identity: Mapped[str] = mapped_column(String(32), default=lambda: uuid4().hex, unique=True, index=True)
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


class StatusOperation(db.Model):
    """A receipt contains snapshots, never authentication credentials."""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(String(32), unique=True)
    operation_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    request_digest: Mapped[str] = mapped_column(String(64))
    actor_id: Mapped[int] = mapped_column(Integer, index=True)
    actor_name: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[str] = mapped_column(String(40))
    requested: Mapped[int] = mapped_column(Integer)
    changed: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean)

    def receipt(self):
        return {"requested": self.requested, "changed": self.changed, "enabled": self.enabled}


class StatusAudit(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[int] = mapped_column(ForeignKey("status_operation.id"), index=True)
    target_id: Mapped[int] = mapped_column(Integer, index=True)
    target_name: Mapped[str] = mapped_column(String(80))
    before_enabled: Mapped[bool] = mapped_column(Boolean)
    after_enabled: Mapped[bool] = mapped_column(Boolean)
    changed: Mapped[bool] = mapped_column(Boolean)


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
    form_excluded_columns = ("alternative_id", "audit_identity", "_password")
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


def audited_status(selected, enabled, operation_key):
    # Authentication reads may already own a session transaction. End that read,
    # then recheck the same live login under SQLite's write lock before mutation.
    actor_id = flask_login.current_user.id
    actor_login = flask_login.current_user.alternative_id
    db.session.rollback()
    try:
        db.session.execute(text("BEGIN IMMEDIATE"))
        actor = db.session.scalar(db.select(User).where(User.id == actor_id,
            User.alternative_id == actor_login, User.enabled.is_(True)))
        if actor is None:
            db.session.rollback()
            abort(401)
        # SQLite integer IDs can be reused after deletion. This identity is stable
        # across login revocation/rename, distinct for each newly created account.
        digest = hashlib.sha256(json.dumps([actor_id, actor.audit_identity, selected, enabled],
            separators=(",", ":")).encode()).hexdigest()
        if operation_key is not None:
            previous = db.session.scalar(db.select(StatusOperation).where(StatusOperation.operation_key == operation_key))
            if previous is not None:
                if previous.request_digest != digest:
                    db.session.rollback()
                    return {"error": "operation_conflict"}, None, 409
                receipt, identity = previous.receipt(), previous.operation_id
                db.session.rollback()
                return receipt, identity, 200
        if actor_id in selected:
            db.session.rollback()
            return {"error": "current_account_protected"}, None, 409
        users = db.session.scalars(db.select(User).where(User.id.in_(selected)).order_by(User.id)).all()
        if len(users) != len(selected):
            db.session.rollback()
            return {"error": "unknown_user"}, None, 404
        identity = uuid4().hex
        operation = StatusOperation(operation_id=identity, operation_key=operation_key,
            request_digest=digest, actor_id=actor_id, actor_name=actor.username,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            requested=len(users), changed=sum(u.enabled != enabled for u in users), enabled=enabled)
        db.session.add(operation)
        db.session.flush()
        for user in users:
            before = user.enabled
            db.session.add(StatusAudit(operation_id=operation.id, target_id=user.id,
                target_name=user.username, before_enabled=before, after_enabled=enabled,
                changed=before != enabled))
            if before != enabled:
                user.enabled = enabled
        receipt = operation.receipt()
        db.session.commit()
        return receipt, identity, 200
    except SQLAlchemyError:
        db.session.rollback()
        return {"error": "storage_failure"}, None, 503


def audit_page():
    numbers = {}
    for name, default, maximum in (("page", "1", 999999999), ("per_page", "20", 100),
                                    ("actor_id", None, 9223372036854775807),
                                    ("target_id", None, 9223372036854775807)):
        value = request.args.get(name, default)
        if value is None or (value == "" and default is None):
            continue
        if (not value.isascii() or not value.isdigit() or len(value) > 19
                or not 1 <= int(value) <= maximum):
            abort(400, description="Invalid audit filter or pagination")
        numbers[name] = int(value)
    filters = []
    if "actor_id" in numbers:
        filters.append(StatusOperation.actor_id == numbers["actor_id"])
    if "target_id" in numbers:
        filters.append(StatusOperation.id.in_(db.select(StatusAudit.operation_id).where(
            StatusAudit.target_id == numbers["target_id"])))
    total = db.session.scalar(db.select(db.func.count()).select_from(StatusOperation).where(*filters))
    page, per_page = numbers["page"], numbers["per_page"]
    operations = db.session.scalars(db.select(StatusOperation).where(*filters).order_by(StatusOperation.id)
        .offset((page - 1) * per_page).limit(per_page)).all()
    items = []
    for operation in operations:
        targets = db.session.scalars(db.select(StatusAudit).where(StatusAudit.operation_id == operation.id)
            .order_by(StatusAudit.target_id)).all()
        items.append({"operation_id": operation.operation_id, "actor_id": operation.actor_id,
            "actor_name": operation.actor_name, "created_at": operation.created_at, **operation.receipt(),
            "targets": [{"target_id": t.target_id, "target_name": t.target_name,
                         "before_enabled": t.before_enabled, "after_enabled": t.after_enabled,
                         "changed": t.changed} for t in targets]})
    return {"items": items, "total": total, "page": page, "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
            "actor_id": numbers.get("actor_id", ""), "target_id": numbers.get("target_id", "")}


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
        return self.render("bulk_users.html", listing=user_page(), operation_key=uuid4().hex)

    @expose("/users/status/", methods=("POST",))
    def users_status(self):
        require_manager()
        if request.is_json:
            body = request.get_json(silent=True)
            if not isinstance(body, dict):
                return jsonify(error="invalid_request"), 400
            ids, enabled = body.get("ids"), body.get("enabled")
            operation_key = body.get("operation_key")
            key_present = "operation_key" in body
        else:
            operation_key = request.form.get("operation_key")
            key_present = "operation_key" in request.form
            raw_ids = request.form.getlist("ids")
            if any(not value.isascii() or not value.isdigit() or len(value) > 19 for value in raw_ids):
                return jsonify(error="invalid_ids"), 400
            ids = [int(value) for value in raw_ids]
            value = request.form.get("enabled")
            enabled = value == "true" if value in {"true", "false"} else None
        if (not isinstance(ids, list) or not 1 <= len(ids) <= 100 or type(enabled) is not bool
                or any(type(identity) is not int or not 1 <= identity <= 9223372036854775807 for identity in ids)):
            return jsonify(error="invalid_request"), 400
        if key_present and (not isinstance(operation_key, str) or re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", operation_key) is None):
            return jsonify(error="invalid_operation_key"), 400
        receipt, identity, status = audited_status(sorted(set(ids)), enabled, operation_key)
        if status != 200:
            return jsonify(receipt), status
        if request.is_json:
            response = jsonify(receipt)
            response.headers["X-Operation-ID"] = identity
            return response
        return redirect(url_for(".users_bulk", enabled=request.args.get("enabled", "all"),
                                q=request.args.get("q", ""), page=request.args.get("page", "1"),
                                per_page=request.args.get("per_page", "20")))

    @expose("/users/audit/data/", methods=("GET",))
    def audit_data(self):
        require_manager()
        return jsonify(audit_page())

    @expose("/users/audit/", methods=("GET",))
    def audit_view(self):
        require_manager()
        return self.render("status_audit.html", listing=audit_page())

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
    """Apply additive account-state and stable audit identity migrations idempotently."""
    db.create_all()
    if db.engine.dialect.name != "sqlite":
        raise RuntimeError("This local example requires SQLite")
    with db.engine.begin() as connection:
        columns = {column["name"] for column in inspect(connection).get_columns("user")}
        if "enabled" not in columns:
            connection.execute(text('ALTER TABLE "user" ADD COLUMN enabled BOOLEAN NOT NULL DEFAULT 1'))
        if "audit_identity" not in columns:
            connection.execute(text('ALTER TABLE "user" ADD COLUMN audit_identity VARCHAR(32)'))
        missing = connection.execute(text("SELECT id FROM user WHERE audit_identity IS NULL OR audit_identity=:empty"), {"empty": ""}).scalars().all()
        for identity in missing:
            connection.execute(text('UPDATE "user" SET audit_identity=:value WHERE id=:id'),
                               {"value": uuid4().hex, "id": identity})
        connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_user_audit_identity ON "user" (audit_identity)'))


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
