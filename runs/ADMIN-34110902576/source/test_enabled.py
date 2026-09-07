"""Functional HTTP/SQLite checks for the actual enabled-user increment."""
import re
import secrets
import sqlite3
import tempfile
import unittest
from pathlib import Path
from main import create_app, db, User


class EnabledUserTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'app.sqlite'
        self.config = dict(TESTING=True, SECRET_KEY=secrets.token_hex(32),
                           SQLALCHEMY_DATABASE_URI='sqlite:///' + str(self.path))
        self.app = create_app(self.config)
        self.phrase = secrets.token_urlsafe(18)
        with self.app.app_context():
            for name in ('manager', 'fan'):
                user = User(username=name, enabled=True)
                user.password = self.phrase
                db.session.add(user)
            db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def csrf_value(self, client, url):
        response = client.get(url)
        self.assertEqual(response.status_code, 200, response.data[:300])
        match = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', response.data)
        self.assertIsNotNone(match, response.data[:1000])
        return match.group(1).decode()

    def login(self, client, name='manager'):
        csrf_value = self.csrf_value(client, '/admin/login/')
        return client.post('/admin/login/', data={'username': name, 'password': self.phrase, 'csrf_token': csrf_value})

    def set_enabled(self, name, value):
        with self.app.app_context():
            user = User.get(name, 'username'); user.enabled = value; db.session.commit()

    def test_normal_login_lists_and_password_is_not_plaintext(self):
        self.assertEqual(self.login(self.client).status_code, 302)
        response = self.client.get('/admin/user/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'manager', response.data)
        self.assertIn(b'Enabled', response.data)
        self.assertNotIn(self.phrase.encode(), response.data)
        with self.app.app_context():
            self.assertNotEqual(User.get('manager', 'username').password, self.phrase)

    def test_anonymous_access_is_rejected(self):
        for url in ('/admin/', '/admin/user/', '/admin/user/edit/?id=1'):
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_disabled_account_cannot_log_in(self):
        self.set_enabled('fan', False)
        response = self.login(self.client, 'fan')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid credentials or inactive account', response.data)
        self.assertEqual(self.client.get('/admin/user/').status_code, 302)

    def test_existing_cookie_revoked_and_not_resurrected(self):
        self.assertEqual(self.login(self.client, 'fan').status_code, 302)
        old = self.client.get_cookie('session').value
        manager = self.app.test_client(); self.assertEqual(self.login(manager).status_code, 302)
        self.set_enabled('fan', False)
        self.assertEqual(self.client.get('/admin/user/').status_code, 302)
        self.assertEqual(manager.get('/admin/user/').status_code, 200)
        self.set_enabled('fan', True)
        self.client.set_cookie('session', old)
        self.assertEqual(self.client.get('/admin/user/').status_code, 302)
        self.assertEqual(self.login(self.client, 'fan').status_code, 302)
        self.assertEqual(self.client.get('/admin/user/').status_code, 200)

    def test_admin_form_edit_and_filter_have_real_effects(self):
        self.assertEqual(self.login(self.client).status_code, 302)
        with self.app.app_context(): identity = User.get('fan', 'username').id
        url = '/admin/user/edit/?id=' + str(identity)
        csrf_value = self.csrf_value(self.client, url)
        response = self.client.post(url, data={'username': 'fan', 'password': '', 'csrf_token': csrf_value, '_continue_editing': '1'})
        self.assertEqual(response.status_code, 302, response.data[:1800])
        with self.app.app_context(): self.assertFalse(User.get('fan', 'username').enabled)
        response = self.client.get('/admin/user/?flt0_0=0')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'fan', response.data)
        self.assertNotIn(b'/admin/user/edit/?id=1', response.data)

    def test_csrf_absent_and_invalid_cannot_change_user(self):
        self.login(self.client)
        for value in ('', 'invalid'):
            response = self.client.post('/admin/user/edit/?id=2', data={'username': 'changed', 'csrf_token': value})
            self.assertEqual(response.status_code, 400)
        with self.app.app_context(): self.assertIsNotNone(User.get('fan', 'username'))

    def test_csrf_required_for_login_and_logout_is_post_only(self):
        response = self.client.post('/admin/login/', data={'username':'fan','password':self.phrase})
        self.assertEqual(response.status_code, 400)
        self.login(self.client)
        self.assertEqual(self.client.get('/admin/logout/').status_code, 405)
        self.assertEqual(self.client.post('/admin/logout/').status_code, 400)
        csrf_value = self.csrf_value(self.client, '/admin/user/')
        self.assertEqual(self.client.post('/admin/logout/', data={'csrf_token':csrf_value}).status_code, 302)
        self.assertEqual(self.client.get('/admin/user/').status_code, 302)

    def test_forged_session_is_not_authenticated(self):
        self.client.set_cookie('session', 'forged-session')
        self.assertEqual(self.client.get('/admin/user/').status_code, 302)

    def test_external_next_url_cannot_redirect_user_off_site(self):
        csrf_value = self.csrf_value(self.client, '/admin/login/')
        response = self.client.post('/admin/login/?next=https://example.invalid', data={'username':'fan','password':self.phrase,'csrf_token':csrf_value})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/admin/')

    def test_restart_preserves_state_and_migration_is_idempotent(self):
        self.set_enabled('fan', False)
        restarted = create_app(self.config)
        with restarted.app_context():
            self.assertFalse(User.get('fan','username').enabled)
            self.assertEqual(db.session.query(User).count(), 2)
        create_app(self.config)
        with self.app.app_context(): self.assertEqual(db.session.query(User).count(), 2)

    def test_legacy_database_additive_migration_keeps_existing_row(self):
        legacy = Path(self.directory.name) / 'legacy.sqlite'
        from contextlib import closing
        with closing(sqlite3.connect(legacy)) as c:
            c.execute('CREATE TABLE user (id INTEGER PRIMARY KEY, username VARCHAR(80), _password VARCHAR(256), alternative_id VARCHAR(32))')
            c.execute('INSERT INTO user (username,alternative_id) VALUES (?,?)', ('old-user','old-id'))
            c.commit()
        config={**self.config,'SQLALCHEMY_DATABASE_URI':'sqlite:///'+str(legacy)}
        upgraded=create_app(config);create_app(config)
        with upgraded.app_context():
            user=User.get('old-user','username')
            self.assertEqual(user.id,1);self.assertTrue(user.enabled)
            self.assertEqual(user.alternative_id,'old-id')

    def test_registration_duplicate_and_blank_are_rejected(self):
        csrf_value=self.csrf_value(self.client,'/admin/register/')
        for name in ('fan','   '):
            response=self.client.post('/admin/register/',data={'username':name,'password':self.phrase,'csrf_token':csrf_value})
            self.assertEqual(response.status_code,200)
        with self.app.app_context():self.assertEqual(db.session.query(User).count(),2)

    def test_disabled_transition_rotates_marker_once(self):
        with self.app.app_context():
            user=User.get('fan','username');original=user.alternative_id
            user.enabled=False;db.session.commit();revoked=user.alternative_id
            self.assertNotEqual(original,revoked)
            user.enabled=False;db.session.commit();self.assertEqual(user.alternative_id,revoked)
            user.enabled=True;db.session.commit();self.assertEqual(user.alternative_id,revoked)


if __name__ == '__main__':
    unittest.main(verbosity=2)
