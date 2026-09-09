"""Current FINAL R1 additional Unicode/restart regression."""
import hashlib
from pathlib import Path
import unittest
from urllib.parse import urlencode
import test_bulk_status as frozen
from main import User, create_app, db


class FinalR1Tests(unittest.TestCase):
    setUp = frozen.BulkStatusTests.setUp

    def test_casefold_expansions_and_greek_survive_new_connections(self):
        self.assertEqual(hashlib.sha256(Path('test_bulk_status.py').read_bytes()).hexdigest(), '83fe257574e3d1a4b6890ba9f0c4d5dddc972ed80dee8b09b0583d4569172586')
        with self.app.app_context():
            db.session.add_all([User(username='Straße', enabled=True), User(username='ΟΣ', enabled=True)])
            db.session.commit()
        restarted = create_app(self.fixture.config)
        client = restarted.test_client()
        self.assertEqual(self.fixture.login(client).status_code, 302)
        for query, expected in [('STRASSE', 'Straße'), ('ος', 'ΟΣ')]:
            response = client.get('/admin/users/data/?' + urlencode({'q': query}))
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['total'], 1)
            self.assertEqual([item['username'] for item in data['items']], [expected])
        with restarted.app_context():
            db.session.remove(); db.engine.dispose()
