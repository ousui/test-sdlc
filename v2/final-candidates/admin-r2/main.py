"""Local Flask-Admin example; source and BSD license are retained in SOURCE.md."""
import os
import json
from datetime import datetime, timezone
import re
from functools import wraps
from urllib.parse import urlsplit
from uuid import uuid4

import flask_login
from flask import Flask, has_request_context, jsonify, redirect, render_template, request, session as browser_session, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import BaseForm
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect, FlaskForm
from sqlalchemy import Boolean, Integer, String, Text, event, func, inspect, text
from sqlalchemy.exc import SQLAlchemyError
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

    audit_identity: Mapped[str] = mapped_column(String(32), nullable=False, default=lambda: uuid4().hex, unique=True)

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


class StatusOperation(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    operation_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    actor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_identity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actor_name: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    request_ids: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requested: Mapped[int] = mapped_column(Integer, nullable=False)
    changed: Mapped[int] = mapped_column(Integer, nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)


class StatusAudit(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_identity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_name: Mapped[str] = mapped_column(String(80), nullable=False)
    before_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    after_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    changed: Mapped[bool] = mapped_column(Boolean, nullable=False)


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


MAX_SQLITE_ID = 2**63 - 1


class StatusError(Exception):
    def __init__(self, code, status=400):
        self.code, self.status = code, status


def management_required(view):
    @wraps(view)
    def guarded(*args, **kwargs):
        if not flask_login.current_user.is_authenticated or not flask_login.current_user.is_active:
            return jsonify(error="authentication_required"), 401
        return view(*args, **kwargs)
    return guarded


def parse_user_query(args):
    enabled = args.get("enabled", "all")
    if enabled not in {"all", "true", "false"}:
        raise StatusError("invalid_query")
    result = {"enabled": enabled, "q": args.get("q", "").strip()}
    for name, default, maximum in [("page", "1", 2**31 - 1), ("per_page", "20", 100)]:
        raw = args.get(name, default)
        if not re.fullmatch(r"[0-9]{1,10}", raw) or not 1 <= int(raw) <= maximum:
            raise StatusError("invalid_query")
        result[name] = int(raw)
    return result


def query_users(filters):
    conditions = []
    if filters["enabled"] != "all":
        conditions.append(User.enabled.is_(filters["enabled"] == "true"))
    if filters["q"]:
        conditions.append(func.casefold(User.username).contains(filters["q"].casefold(), autoescape=True))
    total = db.session.scalar(db.select(func.count()).select_from(User).where(*conditions))
    per_page, page = filters["per_page"], filters["page"]
    users = db.session.scalars(db.select(User).where(*conditions).order_by(User.id).limit(per_page).offset((page - 1) * per_page))
    return {**filters, "total": total, "pages": (total + per_page - 1) // per_page,
            "items": [{"id": user.id, "username": user.username, "enabled": bool(user.enabled)} for user in users]}


def parse_bulk_request():
    if request.is_json:
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not {"ids", "enabled"} <= set(data) or set(data) - {"ids", "enabled", "operation_key"}:
            raise StatusError("invalid_payload")
        raw_ids, enabled = data["ids"], data["enabled"]
    else:
        raw_ids = request.form.getlist("ids")
        if any(not re.fullmatch(r"[0-9]{1,19}", value) for value in raw_ids):
            raise StatusError("invalid_payload")
        raw_ids = [int(value) for value in raw_ids]
        value = request.form.get("enabled")
        if value not in {"true", "false"}:
            raise StatusError("invalid_payload")
        enabled = value == "true"
    if type(enabled) is not bool or not isinstance(raw_ids, list) or not 1 <= len(raw_ids) <= 100:
        raise StatusError("invalid_payload")
    if any(type(value) is not int or not 1 <= value <= MAX_SQLITE_ID for value in raw_ids):
        raise StatusError("invalid_payload")
    data = request.get_json(silent=True) if request.is_json else request.form
    operation_key = data.get("operation_key") if "operation_key" in data else None
    if "operation_key" in data and (not isinstance(operation_key, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", operation_key)):
        raise StatusError("invalid_payload")
    return sorted(set(raw_ids)), enabled, operation_key


def apply_bulk_status(identities, enabled, operation_key=None):
    actor_id = flask_login.current_user.id
    login_marker = browser_session.get("_user_id")
    canonical_ids = json.dumps(identities, separators=(",", ":"))
    try:
        # Authentication may have read before another transaction revoked this cookie.
        db.session.rollback()
        db.session.execute(text("BEGIN IMMEDIATE"))
        actor = db.session.get(User, actor_id, populate_existing=True)
        if actor is None or not actor.enabled or actor.alternative_id != login_marker:
            raise StatusError("authentication_required", 401)
        if actor_id in identities:
            raise StatusError("current_account_protected", 409)
        receipt = db.session.scalar(db.select(StatusOperation).where(StatusOperation.operation_key == operation_key)) if operation_key is not None else None
        if receipt is not None:
            if (not receipt.actor_identity or receipt.actor_identity != actor.audit_identity
                    or receipt.actor_id != actor_id or receipt.request_ids != canonical_ids or receipt.enabled != enabled):
                raise StatusError("operation_conflict", 409)
            result, operation_id = json.loads(receipt.result_json), receipt.operation_id
            db.session.rollback()
            return result, operation_id
        targets = list(db.session.scalars(db.select(User).where(User.id.in_(identities)).order_by(User.id)))
        if len(targets) != len(identities):
            raise StatusError("unknown_user", 404)
        changed = sum(bool(user.enabled) != enabled for user in targets)
        result = {"requested": len(identities), "changed": changed, "enabled": enabled}
        operation_id = uuid4().hex
        operation = StatusOperation(operation_id=operation_id, operation_key=operation_key,
            actor_id=actor.id, actor_identity=actor.audit_identity, actor_name=actor.username,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            request_ids=canonical_ids, enabled=enabled, requested=len(identities), changed=changed,
            result_json=json.dumps(result, sort_keys=True, separators=(",", ":")))
        db.session.add(operation)
        for user in targets:
            before = bool(user.enabled)
            db.session.add(StatusAudit(operation_id=operation_id, target_id=user.id,
                target_identity=user.audit_identity, target_name=user.username,
                before_enabled=before, after_enabled=enabled, changed=before != enabled))
            user.enabled = enabled
        db.session.commit()
        return result, operation_id
    except StatusError:
        db.session.rollback()
        raise
    except SQLAlchemyError:
        db.session.rollback()
        raise StatusError("storage_failure", 503)


def parse_audit_query(args):
    paging = parse_user_query(args)
    filters = {key: paging[key] for key in ("page", "per_page")}
    for name in ("actor_id", "target_id"):
        raw = args.get(name, "")
        if raw == "":
            filters[name] = None
        elif re.fullmatch(r"[0-9]{1,19}", raw) and 1 <= int(raw) <= MAX_SQLITE_ID:
            filters[name] = int(raw)
        else:
            raise StatusError("invalid_query")
    return filters


def query_audit(filters):
    conditions = []
    if filters["actor_id"] is not None:
        conditions.append(StatusOperation.actor_id == filters["actor_id"])
    if filters["target_id"] is not None:
        conditions.append(db.select(StatusAudit.id).where(
            StatusAudit.operation_id == StatusOperation.operation_id,
            StatusAudit.target_id == filters["target_id"]).exists())
    total = db.session.scalar(db.select(func.count()).select_from(StatusOperation).where(*conditions))
    operations = db.session.scalars(db.select(StatusOperation).where(*conditions)
        .order_by(StatusOperation.id).limit(filters["per_page"])
        .offset((filters["page"] - 1) * filters["per_page"]))
    items = []
    for operation in operations:
        targets = db.session.scalars(db.select(StatusAudit).where(
            StatusAudit.operation_id == operation.operation_id).order_by(StatusAudit.target_id))
        items.append({"operation_id": operation.operation_id, "actor_id": operation.actor_id,
            "actor_name": operation.actor_name, "created_at": operation.created_at,
            "requested": operation.requested, "changed": operation.changed, "enabled": bool(operation.enabled),
            "targets": [{"target_id": row.target_id, "target_name": row.target_name,
                "before_enabled": bool(row.before_enabled), "after_enabled": bool(row.after_enabled),
                "changed": bool(row.changed)} for row in targets]})
    return {**filters, "total": total, "pages": (total + filters["per_page"] - 1) // filters["per_page"], "items": items}


def install_bulk_routes(app, admin):
    @app.get("/admin/users/data/")
    @management_required
    def users_data():
        try:
            return jsonify(query_users(parse_user_query(request.args)))
        except StatusError as error:
            return jsonify(error=error.code), error.status

    @app.get("/admin/users/bulk/")
    @management_required
    def bulk_users():
        try:
            filters = parse_user_query(request.args)
            data = query_users(filters)
        except StatusError as error:
            return jsonify(error=error.code), error.status
        previous = url_for("bulk_users", **{**filters, "page": filters["page"] - 1}) if filters["page"] > 1 else None
        following = url_for("bulk_users", **{**filters, "page": filters["page"] + 1}) if filters["page"] < data["pages"] else None
        return admin.index_view.render("bulk_users.html", data=data, action=url_for("set_bulk_status", **filters), previous=previous, following=following, operation_key=uuid4().hex)

    @app.post("/admin/users/status/")
    @management_required
    def set_bulk_status():
        try:
            filters = parse_user_query(request.args)
            identities, enabled, operation_key = parse_bulk_request()
            result, operation_id = apply_bulk_status(identities, enabled, operation_key)
        except StatusError as error:
            return jsonify(error=error.code), error.status
        response = jsonify(result) if request.is_json else redirect(url_for("bulk_users", **filters))
        response.headers["X-Operation-ID"] = operation_id
        return response

    @app.get("/admin/users/audit/data/")
    @management_required
    def audit_data():
        try:
            return jsonify(query_audit(parse_audit_query(request.args)))
        except StatusError as error:
            return jsonify(error=error.code), error.status

    @app.get("/admin/users/audit/")
    @management_required
    def audit_page():
        try:
            filters = parse_audit_query(request.args)
            data = query_audit(filters)
        except StatusError as error:
            return jsonify(error=error.code), error.status
        previous = url_for("audit_page", **{**filters, "page": filters["page"] - 1}) if filters["page"] > 1 else None
        following = url_for("audit_page", **{**filters, "page": filters["page"] + 1}) if filters["page"] < data["pages"] else None
        return admin.index_view.render("status_audit.html", data=data, previous=previous, following=following)


def register_casefold(connection, record):
    connection.create_function("casefold", 1, lambda value: (value or "").casefold(), deterministic=True)


def migrate_database():
    """Add the status column without replacing existing records or authentication IDs."""
    db.create_all()
    with db.engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql('PRAGMA table_info("user")')}
        if "enabled" not in columns:
            connection.exec_driver_sql('ALTER TABLE "user" ADD COLUMN enabled BOOLEAN NOT NULL DEFAULT 1')
        if "audit_identity" not in columns:
            connection.exec_driver_sql('ALTER TABLE "user" ADD COLUMN audit_identity VARCHAR(32)')
        identities = connection.exec_driver_sql("SELECT id FROM user WHERE audit_identity IS NULL OR audit_identity = ''").fetchall()
        for (identity,) in identities:
            connection.exec_driver_sql('UPDATE "user" SET audit_identity = ? WHERE id = ?', (uuid4().hex, identity))
        connection.exec_driver_sql('CREATE UNIQUE INDEX IF NOT EXISTS ix_user_audit_identity ON "user" (audit_identity)')
        operation_columns = {row[1] for row in connection.exec_driver_sql('PRAGMA table_info("status_operation")')}
        if "actor_identity" not in operation_columns:
            connection.exec_driver_sql('ALTER TABLE status_operation ADD COLUMN actor_identity VARCHAR(32)')
        audit_columns = {row[1] for row in connection.exec_driver_sql('PRAGMA table_info("status_audit")')}
        if "target_identity" not in audit_columns:
            connection.exec_driver_sql('ALTER TABLE status_audit ADD COLUMN target_identity VARCHAR(32)')


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
    install_bulk_routes(app, admin)

    @app.get("/")
    def index():
        return render_template("index.html")

    with app.app_context():
        event.listen(db.engine, "connect", register_casefold)
        migrate_database()
    return app


def build_sample_db():
    """Retained safe initialization: migrate empty or existing tables; never seed/delete."""
    migrate_database()


if __name__ == "__main__":
    create_app().run(debug=False)
