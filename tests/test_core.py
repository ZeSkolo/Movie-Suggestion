import unittest, tempfile, json
from pathlib import Path
from core import run, CATALOG, VECTORS

class Tests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / 'app.db')

    def tearDown(self):
        self.tmp.cleanup()

    def test_catalog(self):
        self.assertEqual(len(run({})['movies']), 24)

    def test_lexical_signal(self):
        self.assertEqual(run({'action': 'recommend', 'query': 'wormhole relativity astronaut'})['movies'][0]['id'], 'interstellar')

    def test_real_vectors(self):
        self.assertTrue(all((abs(sum((v * v for v in vector.values())) - 1) < 1e-06 for vector in VECTORS.values())))

    def test_language(self):
        self.assertTrue(all((m['language'] == 'Hindi' for m in run({'action': 'recommend', 'language': 'Hindi'})['movies'])))

    def test_runtime(self):
        self.assertTrue(all((m['runtime'] <= 120 for m in run({'action': 'recommend', 'max_runtime': 120})['movies'])))

    def test_no_fake_matches(self):
        self.assertEqual(run({'action': 'recommend', 'query': 'unrecognizedzzzzxy'})['movies'], [])

    def test_no_fake_confidence(self):
        self.assertTrue(all((m['affinity'] is None for m in run({'action': 'recommend'})['movies'])))

    def test_invalid_rating(self):
        for rating in [0, 6, True, '5']:
            with self.assertRaises(ValueError):
                run({'action': 'rate', 'movie_id': 'interstellar', 'rating': rating}, self.db)

    def test_profile_persistence(self):
        run({'action': 'rate', 'movie_id': 'interstellar', 'rating': 5}, self.db)
        self.assertEqual(run({}, self.db)['ratings']['interstellar'], 5)

    def test_rating_update(self):
        for value in [2, 5]:
            run({'action': 'rate', 'movie_id': 'interstellar', 'rating': value}, self.db)
        self.assertEqual(run({}, self.db)['ratings'], {'interstellar': 5})

    def test_seen_excluded(self):
        run({'action': 'rate', 'movie_id': 'interstellar', 'rating': 5}, self.db)
        self.assertNotIn('interstellar', [m['id'] for m in run({'action': 'recommend'}, self.db)['movies']])

    def test_save_idempotent(self):
        for _ in range(2):
            run({'action': 'save', 'movie_id': 'arrival', 'saved': True}, self.db)
        self.assertEqual(run({}, self.db)['saved'], ['arrival'])
        run({'action': 'save', 'movie_id': 'arrival', 'saved': False}, self.db)
        self.assertEqual(run({}, self.db)['saved'], [])

    def test_bad_filter(self):
        with self.assertRaises(ValueError):
            run({'action': 'recommend', 'genre': 'invented'})

    def test_unknown_movie(self):
        with self.assertRaises(ValueError):
            run({'action': 'rate', 'movie_id': 'missing', 'rating': 5})

    def test_unknown_action(self):
        with self.assertRaises(ValueError):
            run({'action': 'invented'})
