"""Flask-Admin auth_flask_login example with durable enabled-user revocation.

Upstream: pallets-eco/flask-admin@7fee0246b05476fb6bc38e44bcfb7cc87b978853.
This remains a local teaching example: all enabled authenticated users are managers.
"""
import os
from datetime import timedelta
from uuid import uuid4
from urllib.parse import urlsplit

import flask_login
from flask import Flask, abort, current_app, flash, redirect, render_template, request, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect, FlaskForm
from sqlalchemy import Boolean, Integer, String, event, inspect, text
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import fields, validators, PasswordField

db = SQLAlchemy()
login_manager = flask_login.LoginManager()
csrf = CSRFProtect()


class User(db.Model, flask_login.UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    _password: Mapped[str] = mapped_column(String(256), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text('1'))
    alternative_id: Mapped[str] = mapped_column(String(32), default=lambda: uuid4().hex, index=True)

    @property
    def is_active(self):
        return bool(self.enabled)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        if not value:
            return
        if self._password is None or not self.check_password(value):
            self._password = generate_password_hash(value, method='pbkdf2:sha256:600000')
            self.alternative_id = uuid4().hex

    def check_password(self, value):
        return bool(self._password and value is not None and check_password_hash(self._password, value))

    def get_id(self):
        return self.alternative_id

    def __repr__(self):
        return self.username

    @staticmethod
    def get(value, field):
        if field not in {'username', 'alternative_id', 'id'}:
            raise ValueError('Unsupported user lookup')
        return db.session.execute(db.select(User).where(getattr(User, field) == value)).scalar_one_or_none()


@event.listens_for(User, 'before_update')
def revoke_disabled_sessions(mapper, connection, target):
    """The status and revocation marker persist in the same SQL transaction."""
    history = inspect(target).attrs.enabled.history
    if history.has_changes() and target.enabled is False:
        target.alternative_id = uuid4().hex


@login_manager.user_loader
def load_user(alternative_id):
    user = User.get(alternative_id, 'alternative_id')
    return user if user is not None and user.enabled else None


class LoginForm(FlaskForm):
    username = fields.StringField(validators=[validators.InputRequired(), validators.Length(max=80)])
    password = fields.PasswordField(validators=[validators.InputRequired(), validators.Length(max=256)])
    user = None

    def validate_password(self, field):
        self.user = User.get(self.username.data, 'username')
        if not self.user or not self.user.enabled or not self.user.check_password(field.data):
            raise validators.ValidationError('Invalid credentials or inactive account')


class RegistrationForm(FlaskForm):
    username = fields.StringField(validators=[validators.InputRequired(), validators.Length(min=1, max=80)])
    password = fields.PasswordField(validators=[validators.InputRequired(), validators.Length(min=10, max=256)])

    def validate_username(self, field):
        if User.get(field.data.strip(), 'username'):
            raise validators.ValidationError('Username already taken')
        if not field.data.strip():
            raise validators.ValidationError('Username is required')
        field.data = field.data.strip()


class AdminFlaskForm(FlaskForm):
    """Keep Flask-Admin's object identity while using Flask-WTF CSRF tokens."""
    def __init__(self, formdata=None, obj=None, prefix="", **kwargs):
        self._obj = obj
        super().__init__(formdata=formdata, obj=obj, prefix=prefix, **kwargs)


class MyModelView(ModelView):
    form_base_class = AdminFlaskForm
    column_list = ('username', 'enabled')
    column_filters = ('enabled',)
    column_exclude_list = ('_password', 'alternative_id')
    column_editable_list = ('username',)
    form_columns = ('username', 'enabled', 'password')
    form_extra_fields = {'password': PasswordField('Password')}
    form_args = {'username': {'validators': [validators.InputRequired(), validators.Length(max=80)]}}

    def is_accessible(self):
        return flask_login.current_user.is_authenticated and flask_login.current_user.is_active

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not flask_login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super().index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        if flask_login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        form = LoginForm()
        if form.validate_on_submit():
            flask_login.login_user(form.user)
            target = request.args.get('next', '')
            parsed = urlsplit(target)
            if target.startswith('/') and not target.startswith('//') and not parsed.netloc and not parsed.scheme and '\\' not in target:
                return redirect(target)
            return redirect(url_for('.index'))
        return self.render('auth.html', form=form, title='Log in', alternate='admin.register_view')

    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        if not current_app.config['ALLOW_REGISTRATION']:
            abort(404)
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, password=form.password.data, enabled=True)
            try:
                db.session.add(user)
                db.session.commit()
            except Exception:
                db.session.rollback()
                form.username.errors.append('Unable to create this account')
            else:
                flask_login.login_user(user)
                return redirect(url_for('.index'))
        return self.render('auth.html', form=form, title='Register', alternate='admin.login_view')

    @expose('/logout/', methods=('POST',))
    def logout_view(self):
        flask_login.logout_user()
        return redirect(url_for('.login_view'))


def migrate_database():
    """Idempotent additive SQLite migration. Never drops or reseeds existing data."""
    if db.engine.dialect.name != 'sqlite':
        raise RuntimeError('This example supports only a local SQLite database')
    with db.engine.begin() as connection:
        inspector = inspect(connection)
        if 'user' in inspector.get_table_names():
            names = {column['name'] for column in inspector.get_columns('user')}
            if 'enabled' not in names:
                connection.exec_driver_sql('ALTER TABLE user ADD COLUMN enabled BOOLEAN NOT NULL DEFAULT 1')
    db.create_all()


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get('ADMIN_DEMO_SECRET'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('ADMIN_DEMO_DATABASE', 'sqlite:///admin.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=False,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        WTF_CSRF_TIME_LIMIT=3600,
        MAX_CONTENT_LENGTH=64 * 1024,
        ALLOW_REGISTRATION=True,
    )
    if config:
        app.config.update(config)
    if not app.config.get('SECRET_KEY') or len(app.config['SECRET_KEY']) < 32:
        raise RuntimeError('Provide an instance-specific secret of at least 32 characters')
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    admin = Admin(app, name='Enabled-user demonstration', index_view=MyAdminIndexView(),
                  theme=Bootstrap4Theme(base_template='my_master.html', fluid=True))
    admin.add_view(MyModelView(User, db.session))
    app.add_url_rule('/', 'index', lambda: render_template('index.html'))
    with app.app_context():
        migrate_database()
    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
