"""FINAL R2 additions to the byte-preserved earlier acceptance modules."""
import hashlib
from pathlib import Path
import unittest

import test_status_audit as frozen
from main import StatusAudit, StatusOperation, User, create_app, db


class FinalR2Tests(unittest.TestCase):
    def setUp(self):
        self.fixture = frozen.AuditTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_old_receipt_does_not_mutate_reused_target_id(self):
        f = self.fixture
        self.assertEqual(hashlib.sha256(Path('test_status_audit.py').read_bytes()).hexdigest(),
                         '2a9e642d5f02121205a7ce7a9ad548bc0accc854b9bffde74da7017635005766')
        first = f.post('target-reuse')
        self.assertEqual(first.status_code, 200)
        with f.app.app_context():
            old = db.session.get(User, f.ids['fan'])
            previous_identity, password = old.audit_identity, old.password
            db.session.delete(old)
            db.session.commit()
            replacement = User(id=f.ids['fan'], username='replacement-target', _password=password, enabled=True)
            db.session.add(replacement)
            db.session.commit()
            self.assertNotEqual(replacement.audit_identity, previous_identity)
        before = f.fixture.snapshot()
        replay = f.post('target-reuse')
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.get_json(), first.get_json())
        self.assertEqual(replay.headers['X-Operation-ID'], first.headers['X-Operation-ID'])
        self.assertEqual(f.fixture.snapshot(), before)
        self.assertEqual(f.audit()['items'][0]['targets'][0]['target_name'], 'fan')
        with f.app.app_context():
            self.assertEqual(db.session.scalar(db.select(StatusAudit)).target_identity, previous_identity)

    def test_legacy_receipt_without_stable_owner_stays_opaque_after_restarts(self):
        f = self.fixture
        first = f.post('legacy-owner')
        self.assertEqual(first.status_code, 200)
        before = f.fixture.snapshot()
        with f.app.app_context():
            db.session.remove()
            db.engine.dispose()
        connection = f.connection()
        try:
            connection.execute('ALTER TABLE status_operation DROP COLUMN actor_identity')
            connection.commit()
        finally:
            connection.close()
        for _ in range(2):
            restarted = create_app(dict(f.app.config))
            client = restarted.test_client()
            self.assertEqual(f.fixture.fixture.login(client).status_code, 302)
            token = f.fixture.fixture.csrf_value(client, '/admin/users/bulk/')
            replay = f.post('legacy-owner', client=client, token=token)
            self.assertEqual(replay.status_code, 409)
            self.assertEqual(replay.get_json(), {'error': 'operation_conflict'})
            self.assertNotIn('X-Operation-ID', replay.headers)
            self.assertEqual(f.fixture.snapshot(), before)
            with restarted.app_context():
                operation = db.session.scalar(db.select(StatusOperation))
                self.assertIsNone(operation.actor_identity)
                self.assertEqual(operation.operation_id, first.headers['X-Operation-ID'])
                db.session.remove()
                db.engine.dispose()
        self.assertEqual(f.post('new-owner-key').status_code, 200)
        self.assertEqual(f.audit()['total'], 2)
