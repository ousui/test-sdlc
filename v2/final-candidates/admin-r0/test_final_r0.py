"""New FINAL checks, authored after the implementation task started."""
import hashlib
import os
import secrets
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from main import User, create_app, db


class FinalR0Tests(unittest.TestCase):
    def test_frozen_legacy_acceptance_and_missing_secret(self):
        self.assertEqual(hashlib.sha256(Path('test_enabled.py').read_bytes()).hexdigest(), 'a8cbb1f808742e82c1dccf30839cd6e3141b8b63eb68eb684f07832ce3081afb')
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'SECRET'):
                create_app()

    def test_unique_markers_and_blank_password_preserve_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app({'TESTING': True, 'SECRET_KEY': secrets.token_hex(32), 'SQLALCHEMY_DATABASE_URI': 'sqlite:///'+str(Path(directory)/'new.sqlite')})
            with app.app_context():
                first, second = User(username='one'), User(username='two')
                first.password = 'synthetic-password-one'; second.password = 'synthetic-password-two'
                db.session.add_all([first, second]); db.session.commit()
                self.assertNotEqual(first.alternative_id, second.alternative_id)
                marker, hashed = first.alternative_id, first.password
                first.password = ''; db.session.commit()
                self.assertEqual((first.alternative_id, first.password), (marker, hashed))
                self.assertTrue(first.check_password('synthetic-password-one'))
                self.assertTrue(first.enabled)
                db.session.remove(); db.engine.dispose()


class ExpiredStatusSessionTests(unittest.TestCase):
    # Reuse setup helpers without inheriting and duplicating the original 13 methods.
    import test_enabled as _baseline
    setUp = _baseline.EnabledUserTests.setUp
    tearDown = _baseline.EnabledUserTests.tearDown
    csrf_value = _baseline.EnabledUserTests.csrf_value
    login = _baseline.EnabledUserTests.login

    def test_expired_orm_deactivation_permanently_revokes_old_cookie(self):
        self.assertEqual(self.login(self.client, 'fan').status_code, 302)
        old_cookie = self.client.get_cookie('session').value
        with self.app.app_context():
            user = User.get('fan', 'username')
            original = user.alternative_id
            db.session.commit()
            user.enabled = False
            db.session.commit()
            revoked = user.alternative_id
            self.assertNotEqual(original, revoked)
            db.session.commit()
            user.enabled = False
            db.session.commit()
            self.assertEqual(user.alternative_id, revoked)
        self.assertEqual(self.client.get('/admin/user/').status_code, 302)
        with self.app.app_context():
            user = User.get('fan', 'username')
            db.session.commit()
            user.enabled = True
            db.session.commit()
            self.assertEqual(user.alternative_id, revoked)
        self.client.set_cookie('session', old_cookie)
        self.assertEqual(self.client.get('/admin/user/').status_code, 302)
        self.assertEqual(self.login(self.client, 'fan').status_code, 302)
