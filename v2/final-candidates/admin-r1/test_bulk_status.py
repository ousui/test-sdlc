"""R1 real Flask HTTP/SQLite behavior; original13 remain in their own module."""
import re
import sqlite3
from urllib.parse import urlencode
import unittest
import test_enabled as original
from main import User, create_app, db


class BulkStatusTests(unittest.TestCase):
    def setUp(self):
        self.fixture = original.EnabledUserTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.addCleanup(self.fixture.tearDown)
        self.app = self.fixture.app
        self.client = self.app.test_client()
        with self.app.app_context():
            password = User.get('fan', 'username').password
            for name in ('fan-two', 'other', 'fan%literal'):
                db.session.add(User(username=name, _password=password, enabled=True))
            db.session.commit()
            self.ids = {u.username: u.id for u in db.session.scalars(db.select(User))}
        self.assertEqual(self.fixture.login(self.client).status_code, 302)
        self.token = self.fixture.csrf_value(self.client, '/admin/users/bulk/')

    def snapshot(self):
        with self.app.app_context():
            return {u.id: (u.enabled, u.alternative_id) for u in db.session.scalars(db.select(User))}

    def post(self, body, client=None, token=None):
        return (client or self.client).post('/admin/users/status/', json=body,
            headers={'X-CSRFToken': self.token if token is None else token})

    def listing(self, query=''):
        response = self.client.get('/admin/users/data/' + query)
        self.assertEqual(response.status_code, 200, response.data[:500])
        return response.get_json()

    def test_valid_batch_deduplicates_and_changes_only_targets(self):
        before = self.snapshot()
        fan, second = self.ids['fan'], self.ids['fan-two']
        response = self.post({'ids': [fan, second, fan], 'enabled': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'requested': 2, 'changed': 2, 'enabled': False})
        after = self.snapshot()
        for identity in before:
            if identity in (fan, second):
                self.assertFalse(after[identity][0]); self.assertNotEqual(before[identity][1], after[identity][1])
            else:
                self.assertEqual(before[identity], after[identity])

    def test_invalid_payloads_are_atomic(self):
        before = self.snapshot(); fan = self.ids['fan']
        cases = [None, [], {}, {'ids': [], 'enabled': False}, {'ids': [fan], 'enabled': 'false'},
            {'ids': [fan], 'enabled': 0}, {'ids': [fan]}, {'ids': [fan, True], 'enabled': False},
            {'ids': [fan, 0], 'enabled': False}, {'ids': [fan, -2], 'enabled': False},
            {'ids': [str(fan)], 'enabled': False}, {'ids': [fan, 2.0], 'enabled': False},
            {'ids': [fan, 2**80], 'enabled': False}, {'ids': [fan]*101, 'enabled': False}]
        for body in cases:
            with self.subTest(body=body):
                self.assertEqual(self.post(body).status_code, 400)
                self.assertEqual(before, self.snapshot())

    def test_unknown_and_mixed_ids_reject_whole_batch(self):
        before = self.snapshot()
        for ids in ([99999], [self.ids['fan'], 99999]):
            self.assertEqual(self.post({'ids': ids, 'enabled': False}).status_code, 404)
            self.assertEqual(before, self.snapshot())

    def test_current_actor_is_protected_for_both_actions(self):
        before = self.snapshot()
        for enabled in (True, False):
            response = self.post({'ids': [self.ids['fan'], self.ids['manager']], 'enabled': enabled})
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.get_json()['error'], 'current_account_protected')
            self.assertEqual(before, self.snapshot())

    def test_repeated_state_does_not_rotate_again(self):
        body = {'ids': [self.ids['fan']], 'enabled': False}
        self.assertEqual(self.post(body).get_json()['changed'], 1)
        revoked = self.snapshot()
        self.assertEqual(self.post(body).get_json()['changed'], 0)
        self.assertEqual(revoked, self.snapshot())
        body['enabled'] = True
        self.assertEqual(self.post(body).get_json()['changed'], 1)
        self.assertEqual(self.snapshot()[self.ids['fan']][1], revoked[self.ids['fan']][1])
        self.assertEqual(self.post(body).get_json()['changed'], 0)

    def test_revoked_session_never_revives_after_enable(self):
        fan = self.app.test_client()
        self.assertEqual(self.fixture.login(fan, 'fan').status_code, 302)
        cookie = fan.get_cookie('session').value
        self.assertEqual(self.post({'ids': [self.ids['fan']], 'enabled': False}).status_code, 200)
        self.assertEqual(fan.get('/admin/users/data/').status_code, 401)
        self.assertEqual(self.post({'ids': [self.ids['fan']], 'enabled': True}).status_code, 200)
        fan.set_cookie('session', cookie)
        self.assertEqual(fan.get('/admin/users/data/').status_code, 401)
        self.assertEqual(self.fixture.login(fan, 'fan').status_code, 302)
        self.assertEqual(fan.get('/admin/users/data/').status_code, 200)
        self.assertEqual(self.client.get('/admin/users/data/').status_code, 200)

    def test_filter_total_and_stable_pages_match_database(self):
        self.post({'ids': [self.ids['fan']], 'enabled': False})
        all_fans = self.listing('?q=FAN&per_page=100')
        expected = sorted(self.ids[name] for name in ('fan', 'fan-two', 'fan%literal'))
        self.assertEqual([u['id'] for u in all_fans['items']], expected)
        self.assertEqual((all_fans['total'], all_fans['pages']), (3, 1))
        paged = [self.listing('?q=fan&per_page=1&page='+str(n)) for n in range(1, 4)]
        self.assertEqual([p['items'][0]['id'] for p in paged], expected)
        self.assertTrue(all((p['total'], p['pages']) == (3, 3) for p in paged))
        self.assertEqual(self.listing('?q=fan&enabled=false')['total'], 1)
        self.assertEqual(self.listing('?q=fan&enabled=true')['total'], 2)
        self.assertEqual(self.listing('?q=fan&per_page=1&page=4')['items'], [])
        self.assertEqual(self.listing('?q=nobody')['total'], 0)

    def test_query_metacharacters_are_literal(self):
        data = self.listing('?q=%25')
        self.assertEqual([u['username'] for u in data['items']], ['fan%literal'])
        self.assertEqual(self.listing('?q=_')['items'], [])

    def test_invalid_pagination_and_filters_are_rejected(self):
        for query in ('page=0', 'page=-1', 'page=no', 'page=1.0', 'per_page=0', 'per_page=101',
                      'per_page=no', 'enabled=FALSE', 'page=999999999999999999999'):
            with self.subTest(query=query):
                for path in ('/admin/users/data/', '/admin/users/bulk/'):
                    self.assertEqual(self.client.get(path+'?'+query).status_code, 400)
        self.assertEqual(self.listing('?page=999999999&per_page=100')['items'], [])

    def test_html_form_and_filtered_page_share_real_state(self):
        page = self.client.get('/admin/users/bulk/?q=fan&per_page=1')
        self.assertEqual(page.status_code, 200)
        for text in (b'Total: 3', b'Page: 1', b'Enable selected', b'Disable selected', b'rel="next"'):
            self.assertIn(text, page.data)
        response = self.client.post('/admin/users/status/?q=fan&enabled=false&per_page=1',
            data={'ids': [str(self.ids['fan']), str(self.ids['fan-two'])], 'enabled': 'false', 'csrf_token': self.token})
        self.assertEqual(response.status_code, 302)
        page = self.client.get(response.location)
        self.assertEqual(page.status_code, 200); self.assertIn(b'Total: 2', page.data)
        data = self.listing('?q=fan&enabled=false&per_page=1')
        self.assertEqual(data['total'], 2)
        self.assertIn(('value="'+str(data['items'][0]['id'])+'"').encode(), page.data)
        before = self.snapshot()
        bad = self.client.post('/admin/users/status/', data={'ids': ['bad', str(self.ids['other'])], 'enabled': 'false', 'csrf_token': self.token})
        self.assertEqual(bad.status_code, 400); self.assertEqual(before, self.snapshot())

    def test_authentication_csrf_and_method_boundaries(self):
        anonymous = self.app.test_client()
        for path in ('/admin/users/data/', '/admin/users/bulk/'):
            self.assertEqual(anonymous.get(path).status_code, 401)
        anonymous_token = self.fixture.csrf_value(anonymous, '/admin/login/')
        before = self.snapshot()
        body = {'ids': [self.ids['fan']], 'enabled': False}
        self.assertEqual(self.post(body, anonymous, anonymous_token).status_code, 401)
        for token in ('', 'invalid'):
            self.assertEqual(self.post(body, token=token).status_code, 400)
        self.assertEqual(self.client.get('/admin/users/status/').status_code, 405)
        self.assertEqual(before, self.snapshot())

    def test_restart_retains_bulk_state_and_query_total(self):
        self.assertEqual(self.post({'ids': [self.ids['fan'], self.ids['fan-two']], 'enabled': False}).status_code, 200)
        before = self.snapshot()
        restarted = create_app(self.fixture.config)
        client = restarted.test_client()
        self.assertEqual(self.fixture.login(client).status_code, 302)
        response = client.get('/admin/users/data/?enabled=false')
        self.assertEqual(response.status_code, 200); self.assertEqual(response.get_json()['total'], 2)
        self.assertEqual(before, self.snapshot())
        with restarted.app_context():
            db.session.remove(); db.engine.dispose()


    def test_storage_failure_rolls_back_all_users_and_revocation_markers(self):
        before = self.snapshot()
        fan, second = self.ids['fan'], self.ids['fan-two']
        with sqlite3.connect(self.fixture.path) as connection:
            connection.execute(f'CREATE TRIGGER reject_second BEFORE UPDATE ON user WHEN NEW.id={second} BEGIN SELECT RAISE(ABORT, "synthetic storage failure"); END')
        response = self.post({'ids': [fan, second], 'enabled': False})
        self.assertEqual(response.status_code, 503, response.data)
        self.assertEqual(response.get_json(), {'error': 'storage_failure'})
        self.assertEqual(before, self.snapshot(), 'Earlier row or alternative_id leaked despite later-row failure')

    def test_html_form_accepts_same_existing_64bit_id_as_json(self):
        identity = 1000000000000000000
        with self.app.app_context():
            db.session.add(User(id=identity, username='legacy-large-id', enabled=True))
            db.session.commit()
        page = self.client.get('/admin/users/bulk/?q=legacy-large-id')
        self.assertEqual(page.status_code, 200)
        self.assertIn(('value="'+str(identity)+'"').encode(), page.data)
        response = self.post({'ids': [identity], 'enabled': False})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.post({'ids': [identity], 'enabled': True}).status_code, 200)
        response = self.client.post('/admin/users/status/', data={
            'ids': [str(identity)], 'enabled': 'false', 'csrf_token': self.token})
        self.assertEqual(response.status_code, 302, 'Rendered checkbox ID is accepted in JSON but rejected by its own HTML form: '+response.data.decode())

    def test_unicode_username_search_is_case_insensitive(self):
        with self.app.app_context():
            db.session.add(User(username='ÁLICE', enabled=True))
            db.session.commit()
        exact = self.listing('?'+urlencode({'q':'ÁL'}))
        self.assertEqual([u['username'] for u in exact['items']], ['ÁLICE'])
        lowercase = self.listing('?'+urlencode({'q':'ál'}))
        self.assertEqual([u['username'] for u in lowercase['items']], ['ÁLICE'], lowercase)


if __name__ == '__main__':
    unittest.main(verbosity=2)
