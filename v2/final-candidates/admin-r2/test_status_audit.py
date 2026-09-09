"""R2 actual HTTP and SQLite checks. Original R0/R1 modules remain unchanged."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
import re
import sqlite3
import threading
import unittest

import test_bulk_status as baseline
from main import StatusAudit, StatusOperation, User, build_sample_db, create_app, db


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.fixture = baseline.BulkStatusTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.app = self.fixture.app
        self.client = self.fixture.client
        self.ids = self.fixture.ids
        self.token = self.fixture.token

    def post(self, key='request-1', ids=None, enabled=False, client=None, token=None):
        body = {'ids': ids or [self.ids['fan']], 'enabled': enabled}
        if key is not ...:
            body['operation_key'] = key
        return self.fixture.post(body, client=client, token=token)

    def audit(self, query='', client=None):
        response = (client or self.client).get('/admin/users/audit/data/' + query)
        self.assertEqual(response.status_code, 200, response.data[:500])
        return response.get_json()

    def connection(self):
        with self.app.app_context():
            return sqlite3.connect(db.engine.url.database)

    def trigger(self, sql):
        connection = self.connection()
        try:
            connection.executescript(sql)
        finally:
            connection.close()

    def login_client(self, name='manager'):
        client = self.app.test_client()
        self.assertEqual(self.fixture.fixture.login(client, name).status_code, 302)
        return client, self.fixture.fixture.csrf_value(client, '/admin/users/bulk/')

    def test_snapshot_targets_deduplicated_noop_and_utc(self):
        before = self.fixture.snapshot()
        targets = [self.ids['fan'], self.ids['fan-two'], self.ids['fan']]
        response = self.post(ids=targets)
        self.assertEqual(response.status_code, 200)
        item = self.audit()['items'][0]
        self.assertEqual(item['operation_id'], response.headers['X-Operation-ID'])
        self.assertEqual((item['actor_id'], item['actor_name']), (self.ids['manager'], 'manager'))
        self.assertEqual(item['requested'], 2)
        self.assertEqual(item['changed'], 2)
        self.assertEqual(datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')).utcoffset().total_seconds(), 0)
        self.assertEqual([t['target_id'] for t in item['targets']], sorted(set(targets)))
        for target in item['targets']:
            self.assertTrue(target['before_enabled']); self.assertFalse(target['after_enabled']); self.assertTrue(target['changed'])
            self.assertNotEqual(before[target['target_id']][1], self.fixture.snapshot()[target['target_id']][1])
        self.assertEqual(self.post('noop', ids=targets).get_json()['changed'], 0)
        self.assertTrue(all(not t['changed'] for t in self.audit()['items'][1]['targets']))

    def test_canonical_replay_returns_original_without_reapplying(self):
        targets = [self.ids['fan'], self.ids['fan-two']]
        first = self.post(ids=targets)
        same = self.post(ids=list(reversed(targets)) + targets)
        self.assertEqual(first.get_json(), same.get_json())
        self.assertEqual(first.headers['X-Operation-ID'], same.headers['X-Operation-ID'])
        self.assertEqual(self.post('later-enable', ids=targets, enabled=True).status_code, 200)
        before = self.fixture.snapshot()
        replay = self.post(ids=targets)
        self.assertEqual(replay.get_json(), first.get_json())
        self.assertEqual(replay.headers['X-Operation-ID'], first.headers['X-Operation-ID'])
        self.assertEqual(before, self.fixture.snapshot())
        self.assertEqual(self.audit()['total'], 2)

    def test_same_key_different_payload_or_actor_conflicts_without_details(self):
        self.assertEqual(self.post().status_code, 200)
        before = self.fixture.snapshot()
        for kwargs in ({'enabled': True}, {'ids': [self.ids['other']]}):
            response = self.post(**kwargs)
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.get_json(), {'error': 'operation_conflict'})
            self.assertNotIn('X-Operation-ID', response.headers)
        other, token = self.login_client('other')
        response = self.post(client=other, token=token)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json(), {'error': 'operation_conflict'})
        self.assertEqual(self.audit()['total'], 1)
        self.assertEqual(before, self.fixture.snapshot())

    def test_invalid_keys_have_no_effect_or_receipt(self):
        before = self.fixture.snapshot()
        for key in ('', 'x' * 129, 'space key', '汉字', '\n', None, True, 17, [], {}):
            with self.subTest(key=key):
                self.assertEqual(self.post(key).status_code, 400)
                self.assertEqual(before, self.fixture.snapshot())
        self.assertEqual(self.audit()['total'], 0)
        self.assertEqual(self.post('A9._:-' + 'x' * 122).status_code, 200)

    def test_rejected_batch_has_no_success_audit(self):
        for ids, status in (([999999], 404), ([self.ids['fan'], 999999], 404),
                            ([self.ids['manager']], 409)):
            self.assertEqual(self.post(ids=ids).status_code, status)
            self.assertEqual(self.audit()['total'], 0)
        self.assertEqual(self.post().status_code, 200)

    def test_legacy_unkeyed_calls_keep_exact_json_and_independent_audit(self):
        first = self.post(...)
        second = self.post(...)
        self.assertEqual(first.get_json(), {'requested': 1, 'changed': 1, 'enabled': False})
        self.assertEqual(second.get_json(), {'requested': 1, 'changed': 0, 'enabled': False})
        self.assertNotEqual(first.headers['X-Operation-ID'], second.headers['X-Operation-ID'])
        self.assertEqual(self.audit()['total'], 2)

    def assert_atomic_failure(self, trigger):
        before = self.fixture.snapshot()
        self.trigger(trigger)
        response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {'error': 'storage_failure'})
        self.assertEqual(before, self.fixture.snapshot())
        self.assertEqual(self.audit()['total'], 0)
        with self.app.app_context():
            self.assertEqual(db.session.scalar(db.select(db.func.count()).select_from(StatusAudit)), 0)
        self.trigger('DROP TRIGGER r2_failure;')
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(self.audit()['total'], 1)

    def test_audit_insert_failure_rolls_back_state_session_and_key(self):
        self.assert_atomic_failure("CREATE TRIGGER r2_failure BEFORE INSERT ON status_audit BEGIN SELECT RAISE(ABORT, 'synthetic audit failure'); END;")

    def test_state_write_failure_rolls_back_receipt_and_audit(self):
        self.assert_atomic_failure("CREATE TRIGGER r2_failure BEFORE UPDATE OF enabled ON user BEGIN SELECT RAISE(ABORT, 'synthetic state failure'); END;")

    def test_concurrent_same_key_commits_once(self):
        clients = [self.login_client() for _ in range(8)]
        barrier = threading.Barrier(8)
        def invoke(pair):
            barrier.wait(timeout=15)
            response = self.post('parallel-key', client=pair[0], token=pair[1])
            return response.status_code, response.get_json(), response.headers.get('X-Operation-ID')
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(invoke, clients))
        self.assertTrue(all(r == results[0] for r in results), results)
        self.assertEqual(results[0][0], 200)
        self.assertEqual(results[0][1]['changed'], 1)
        self.assertEqual(self.audit()['total'], 1)
        self.assertEqual(len(self.audit()['items'][0]['targets']), 1)

    def test_concurrent_different_payload_has_one_winner(self):
        clients = [self.login_client() for _ in range(2)]
        barrier = threading.Barrier(2)
        def invoke(index):
            barrier.wait(timeout=15)
            client, token = clients[index]
            response = self.post('competing-key', enabled=bool(index), client=client, token=token)
            return index, response.status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(invoke, range(2)))
        self.assertEqual(sorted(status for _, status in results), [200, 409])
        winner = next(index for index, status in results if status == 200)
        self.assertEqual(self.fixture.snapshot()[self.ids['fan']][0], bool(winner))
        self.assertEqual(self.audit()['total'], 1)

    def test_query_exact_filters_stable_pages_and_total(self):
        self.post('one')
        self.post('two', ids=[self.ids['fan-two']])
        other, token = self.login_client('other')
        self.post('three', enabled=True, client=other, token=token)
        pages = [self.audit('?per_page=1&page=' + str(n)) for n in (1, 2, 3)]
        self.assertTrue(all(page['total'] == 3 and page['pages'] == 3 for page in pages))
        self.assertEqual([page['items'][0]['operation_id'] for page in pages],
                         [item['operation_id'] for item in self.audit()['items']])
        self.assertEqual(self.audit('?actor_id=' + str(self.ids['manager']))['total'], 2)
        self.assertEqual(self.audit('?target_id=' + str(self.ids['fan']))['total'], 2)
        self.assertEqual(self.audit('?actor_id=' + str(self.ids['manager']) + '&target_id=' + str(self.ids['fan']))['total'], 1)
        self.assertEqual(self.audit('?page=999')['items'], [])
        for query in ('?page=0', '?per_page=101', '?actor_id=-1', '?target_id=1.0', '?target_id=' + '9' * 5000):
            self.assertEqual(self.client.get('/admin/users/audit/data/' + query).status_code, 400)

    def test_audit_requires_live_enabled_session(self):
        anonymous = self.app.test_client()
        for endpoint in ('/admin/users/audit/', '/admin/users/audit/data/'):
            self.assertEqual(anonymous.get(endpoint).status_code, 401)
        other, token = self.login_client('other')
        self.assertEqual(self.post('disable-other', ids=[self.ids['other']]).status_code, 200)
        self.assertEqual(other.get('/admin/users/audit/data/').status_code, 401)
        self.assertEqual(self.post('enable-other', ids=[self.ids['other']], enabled=True).status_code, 200)
        self.assertEqual(other.get('/admin/users/audit/data/').status_code, 401)

    def test_deleted_actor_and_target_preserve_snapshots(self):
        self.post()
        other, token = self.login_client('other')
        with self.app.app_context():
            db.session.delete(db.session.get(User, self.ids['fan']))
            db.session.delete(db.session.get(User, self.ids['manager']))
            db.session.commit()
        item = self.audit(client=other)['items'][0]
        self.assertEqual((item['actor_id'], item['actor_name']), (self.ids['manager'], 'manager'))
        self.assertEqual((item['targets'][0]['target_id'], item['targets'][0]['target_name']), (self.ids['fan'], 'fan'))

    def test_replay_after_target_deleted_uses_original_receipt(self):
        first = self.post()
        with self.app.app_context():
            db.session.delete(db.session.get(User, self.ids['fan']))
            db.session.commit()
        replay = self.post()
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.get_json(), first.get_json())
        self.assertEqual(replay.headers['X-Operation-ID'], first.headers['X-Operation-ID'])
        self.assertEqual(self.audit()['total'], 1)

    def test_restart_repeated_migration_preserves_key_and_audit(self):
        first = self.post()
        with self.app.app_context():
            build_sample_db(); build_sample_db()
            db.session.remove(); db.engine.dispose()
        restarted = create_app(dict(self.app.config))
        client = restarted.test_client()
        self.assertEqual(self.fixture.fixture.login(client).status_code, 302)
        token = self.fixture.fixture.csrf_value(client, '/admin/users/bulk/')
        response = self.post(client=client, token=token)
        self.assertEqual(response.get_json(), first.get_json())
        self.assertEqual(response.headers['X-Operation-ID'], first.headers['X-Operation-ID'])
        self.assertEqual(client.get('/admin/users/audit/data/').get_json()['total'], 1)
        with restarted.app_context():
            db.session.remove(); db.engine.dispose()

    def test_html_key_csrf_redirect_and_replay(self):
        url = '/admin/users/bulk/?enabled=true&q=fan&page=2&per_page=1'
        page = self.client.get(url).data.decode()
        key = re.search(r'name="operation_key" type="hidden" value="([a-f0-9]+)"', page).group(1)
        next_key = re.search(r'name="operation_key" type="hidden" value="([a-f0-9]+)"', self.client.get(url).data.decode()).group(1)
        self.assertNotEqual(key, next_key)
        data = {'ids': [str(self.ids['fan'])], 'enabled': 'false', 'operation_key': key}
        self.assertEqual(self.client.post('/admin/users/status/', data=data).status_code, 400)
        data['csrf_token'] = self.token
        for _ in range(2):
            response = self.client.post('/admin/users/status/?enabled=true&q=fan&page=2&per_page=1', data=data)
            self.assertEqual(response.status_code, 302)
            for fragment in ('enabled=true', 'q=fan', 'page=2', 'per_page=1'):
                self.assertIn(fragment, response.location)
        self.assertEqual(self.audit()['total'], 1)

    def test_html_escapes_snapshots_and_audit_has_only_safe_fields(self):
        with self.app.app_context():
            db.session.get(User, self.ids['fan']).username = '<script>alert(1)</script>'
            db.session.commit()
        self.post()
        html = self.client.get('/admin/users/audit/').data.decode()
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        with self.app.app_context():
            forbidden = {'_password', 'password', 'alternative_id', 'session', 'cookie', 'token'}
            self.assertFalse(forbidden & set(StatusOperation.__table__.columns.keys()))
            self.assertFalse(forbidden & set(StatusAudit.__table__.columns.keys()))
            row = db.session.scalar(db.select(StatusOperation))
            raw = json.dumps({c.name: getattr(row, c.name) for c in StatusOperation.__table__.columns})
            for user in db.session.scalars(db.select(User)):
                self.assertNotIn(user.alternative_id, raw)
                self.assertNotIn(user.password, raw)


"""Independent Q2 acceptance additions; use real Flask requests and SQLite writes.
Only isolated fixture state is changed. The event hook only coordinates thread timing.
Run with this file and snapshot main/test dependencies on PYTHONPATH.
"""
from concurrent.futures import ThreadPoolExecutor
import threading
import unittest
from sqlalchemy import event
from main import User, db


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):
        self.fixture = AuditTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_waiting_request_rechecks_live_login_after_disable_reenable(self):
        f = self.fixture
        actor, token = f.login_client('other')
        reached, release = threading.Event(), threading.Event()
        worker_id = []
        def before_begin(conn, cursor, statement, parameters, context, executemany):
            if statement == 'BEGIN IMMEDIATE' and worker_id and threading.get_ident() == worker_id[0]:
                reached.set()
                if not release.wait(15):
                    raise RuntimeError('timing fixture release timeout')
        with f.app.app_context():
            engine = db.engine
        event.listen(engine, 'before_cursor_execute', before_begin)
        self.addCleanup(event.remove, engine, 'before_cursor_execute', before_begin)
        def waiting_request():
            worker_id.append(threading.get_ident())
            return f.post('waiting-request', client=actor, token=token)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(waiting_request)
            try:
                self.assertTrue(reached.wait(15))
                self.assertEqual(f.post('revoke-actor', ids=[f.ids['other']]).status_code, 200)
                self.assertEqual(f.post('restore-actor', ids=[f.ids['other']], enabled=True).status_code, 200)
            finally:
                release.set()
            response = future.result(timeout=15)
        self.assertEqual(response.status_code, 401, response.data)
        self.assertTrue(f.fixture.snapshot()[f.ids['fan']][0])
        audit = f.audit()
        self.assertEqual(audit['total'], 2)
        self.assertTrue(all(item['actor_id'] == f.ids['manager'] for item in audit['items']))

    def test_late_audit_failure_rolls_back_all_targets_and_keeps_sessions_live(self):
        f = self.fixture
        fan, _ = f.login_client('fan')
        other_fan, _ = f.login_client('fan-two')
        before = f.fixture.snapshot()
        second = f.ids['fan-two']
        f.trigger(f"CREATE TRIGGER fail_late_audit BEFORE INSERT ON status_audit WHEN NEW.target_id={second} BEGIN SELECT RAISE(ABORT, 'second audit insertion'); END;")
        response = f.post('late-audit', ids=[f.ids['fan'], second])
        self.assertEqual(response.status_code, 503)
        self.assertEqual(f.fixture.snapshot(), before)
        self.assertEqual(f.audit()['total'], 0)
        for client in (fan, other_fan):
            self.assertEqual(client.get('/admin/users/audit/data/').status_code, 200)
        f.trigger('DROP TRIGGER fail_late_audit;')
        self.assertEqual(f.post('late-audit', ids=[f.ids['fan'], second]).status_code, 200)
        for client in (fan, other_fan):
            self.assertEqual(client.get('/admin/users/audit/data/').status_code, 401)
        self.assertEqual(f.audit()['total'], 1)

    def test_concurrent_different_actor_same_key_is_single_opaque_conflict(self):
        f = self.fixture
        pairs = [f.login_client(name) for name in ('manager', 'other')]
        barrier = threading.Barrier(2)
        def invoke(pair):
            barrier.wait(timeout=15)
            return f.post('actor-race', client=pair[0], token=pair[1])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(invoke, pairs))
        self.assertEqual(sorted(r.status_code for r in results), [200, 409])
        loser = next(r for r in results if r.status_code == 409)
        self.assertEqual(loser.get_json(), {'error': 'operation_conflict'})
        self.assertNotIn('X-Operation-ID', loser.headers)
        audit = f.audit()
        self.assertEqual(audit['total'], 1)
        self.assertEqual(len(audit['items'][0]['targets']), 1)

    def test_deleted_actor_id_reuse_must_not_inherit_original_operation_key(self):
        f = self.fixture
        # Public registration creates the highest SQLite INTEGER PRIMARY KEY.
        original = f.app.test_client()
        csrf = f.fixture.fixture.csrf_value(original, '/admin/register/')
        response = original.post('/admin/register/', data={
            'username': 'departed-manager', 'password': f.fixture.fixture.phrase,
            'csrf_token': csrf})
        self.assertEqual(response.status_code, 302)
        token = f.fixture.fixture.csrf_value(original, '/admin/users/bulk/')
        with f.app.app_context():
            original_id = User.get('departed-manager', 'username').id
        first = f.post('departed-secret-key', client=original, token=token)
        self.assertEqual(first.status_code, 200)
        # Delete through the existing authenticated Flask-Admin route.
        csrf = f.fixture.fixture.csrf_value(f.client, '/admin/user/')
        deleted = f.client.post('/admin/user/delete/', data={'id': original_id, 'csrf_token': csrf})
        self.assertEqual(deleted.status_code, 302, deleted.data)
        with f.app.app_context():
            self.assertIsNone(db.session.get(User, original_id))
        replacement = f.app.test_client()
        csrf = f.fixture.fixture.csrf_value(replacement, '/admin/register/')
        response = replacement.post('/admin/register/', data={
            'username': 'replacement-manager', 'password': f.fixture.fixture.phrase,
            'csrf_token': csrf})
        self.assertEqual(response.status_code, 302)
        replacement_token = f.fixture.fixture.csrf_value(replacement, '/admin/users/bulk/')
        with f.app.app_context():
            replacement_id = User.get('replacement-manager', 'username').id
        # A fix that prevents ID reuse is valid; do not require reuse after repair.
        replay = f.post('departed-secret-key', client=replacement, token=replacement_token)
        self.assertEqual(replay.status_code, 409, {
            'actual_status': replay.status_code, 'actual_json': replay.get_json(),
            'original_operation_id': first.headers.get('X-Operation-ID'),
            'returned_operation_id': replay.headers.get('X-Operation-ID'),
            'deleted_actor_id': original_id, 'replacement_id': replacement_id})
        self.assertEqual(replay.get_json(), {'error': 'operation_conflict'})
        self.assertNotIn('X-Operation-ID', replay.headers)
        self.assertEqual(f.audit()['total'], 1)


class StableAuditIdentityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = AuditTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_same_account_rename_revoke_and_relogin_can_replay(self):
        f = self.fixture
        client, token = f.login_client('other')
        first = f.post('stable-owner', client=client, token=token)
        self.assertEqual(first.status_code, 200)
        with f.app.app_context():
            original_identity = db.session.get(User, f.ids['other']).audit_identity
            db.session.get(User, f.ids['other']).username = 'renamed-other'
            db.session.commit()
        self.assertEqual(f.post('disable-owner', ids=[f.ids['other']]).status_code, 200)
        self.assertEqual(f.post('enable-owner', ids=[f.ids['other']], enabled=True).status_code, 200)
        self.assertEqual(client.get('/admin/users/audit/data/').status_code, 401)
        renewed, new_token = f.login_client('renamed-other')
        replay = f.post('stable-owner', client=renewed, token=new_token)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.get_json(), first.get_json())
        self.assertEqual(replay.headers['X-Operation-ID'], first.headers['X-Operation-ID'])
        with f.app.app_context():
            self.assertEqual(db.session.get(User, f.ids['other']).audit_identity, original_identity)
        self.assertEqual(f.audit()['items'][0]['actor_name'], 'other')

    def test_additive_identity_migration_keeps_old_accounts_and_is_stable(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'legacy.sqlite'
            connection = sqlite3.connect(path)
            connection.executescript("CREATE TABLE user (id INTEGER PRIMARY KEY, username VARCHAR(80), _password VARCHAR(256), alternative_id VARCHAR(32)); INSERT INTO user VALUES(7, 'legacy', 'synthetic-hash', 'synthetic-login');")
            connection.close()
            app = create_app({'TESTING': True, 'SECRET_KEY': 'synthetic-migration',
                              'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(path)})
            with app.app_context():
                first = db.session.get(User, 7)
                identity = first.audit_identity
                self.assertRegex(identity, r'^[a-f0-9]{32}$')
                self.assertEqual((first.username, first.password, first.alternative_id, first.enabled),
                                 ('legacy', 'synthetic-hash', 'synthetic-login', True))
                db.session.remove()
                build_sample_db(); build_sample_db()
                self.assertEqual(db.session.get(User, 7).audit_identity, identity)
                db.session.remove(); db.engine.dispose()

    def test_admin_forms_cannot_edit_internal_audit_identity(self):
        f = self.fixture
        html = f.client.get('/admin/user/edit/?id=' + str(f.ids['other'])).data.decode()
        self.assertNotIn('name="audit_identity"', html)
        with f.app.app_context():
            before = db.session.get(User, f.ids['other']).audit_identity
        csrf = f.fixture.fixture.csrf_value(f.client, '/admin/user/edit/?id=' + str(f.ids['other']))
        response = f.client.post('/admin/user/edit/?id=' + str(f.ids['other']), data={
            'csrf_token': csrf, 'username': 'other', 'enabled': 'y', 'audit_identity': 'attacker-chosen'})
        self.assertEqual(response.status_code, 302)
        with f.app.app_context():
            self.assertEqual(db.session.get(User, f.ids['other']).audit_identity, before)
