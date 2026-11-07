"""Content-based machine-learning recommendations with TF-IDF and cosine similarity."""
import collections, json, math, re, sqlite3
from pathlib import Path
CATALOG = json.loads((Path(__file__).parent / 'catalog.json').read_text())
BY_ID = {m['id']: m for m in CATALOG}
STOP = set('a an the and or to of in on for with is as its his her their while into from this that by at it be'.split())

def tokens(text):
    return [x for x in re.findall('[a-z0-9]+', text.lower()) if len(x) > 1 and x not in STOP]
CORPUS = [tokens(' '.join([m['title'], m['synopsis'], *m['genres'], *m['tags']])) for m in CATALOG]
DF = collections.Counter((t for terms in CORPUS for t in set(terms)))
IDF = {t: math.log((len(CATALOG) + 1) / (n + 1)) + 1 for t, n in DF.items()}

def vector(terms):
    counts = collections.Counter(terms)
    v = {t: (1 + math.log(n)) * IDF[t] for t, n in counts.items() if t in IDF}
    norm = math.sqrt(sum((x * x for x in v.values())))
    return {t: x / norm for t, x in v.items()} if norm else {}
VECTORS = {m['id']: vector(terms) for m, terms in zip(CATALOG, CORPUS)}

def connect(path):
    if path != ':memory:':
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.executescript('CREATE TABLE IF NOT EXISTS ratings(movie_id TEXT PRIMARY KEY,rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5));CREATE TABLE IF NOT EXISTS watchlist(movie_id TEXT PRIMARY KEY);')
    return db

def recommend(payload, ratings):
    query = payload.get('query', '')
    if not isinstance(query, str) or len(query) > 300:
        raise ValueError('Describe your mood in at most 300 characters')
    genre = payload.get('genre', 'All')
    language = payload.get('language', 'All')
    runtime = payload.get('max_runtime', 240)
    if genre not in ['All'] + sorted({g for m in CATALOG for g in m['genres']}):
        raise ValueError('Unknown genre')
    if language not in ['All'] + sorted({m['language'] for m in CATALOG}):
        raise ValueError('Unknown language')
    if type(runtime) != int or not 60 <= runtime <= 240:
        raise ValueError('Runtime must be 60–240 minutes')
    query_terms = tokens(query)
    q = vector(query_terms)
    positive = any((r >= 4 for r in ratings.values()))
    for mid, rating in ratings.items():
        weight = (rating - 3) * 0.35
        for term, value in VECTORS[mid].items():
            q[term] = q.get(term, 0) + weight * value
    norm = math.sqrt(sum((x * x for x in q.values())))
    q = {t: x / norm for t, x in q.items()} if norm else {}
    personalized = bool(query_terms or positive or ratings)
    result = []
    for m in CATALOG:
        if m['id'] in ratings or (genre != 'All' and genre not in m['genres']) or (language != 'All' and language != m['language']) or (m['runtime'] > runtime):
            continue
        contributions = {t: q.get(t, 0) * v for t, v in VECTORS[m['id']].items() if q.get(t, 0) * v > 0}
        score = sum((q.get(t, 0) * v for t, v in VECTORS[m['id']].items()))
        if personalized and score <= 0:
            continue
        terms = sorted(contributions, key=contributions.get, reverse=True)[:3]
        result.append(dict(m, affinity=round(max(0, min(1, score)), 4) if personalized else None, reason='Shared signals: ' + ', '.join(terms) if terms else 'Catalog discovery — add a mood or ratings to personalize.'))
    result.sort(key=lambda x: (-(x['affinity'] or 0), x['title']))
    return {'movies': result[:12], 'engine': 'TF-IDF + cosine similarity', 'personalized': personalized, 'notice': 'Affinity is a similarity score, not a probability or guaranteed enjoyment. The catalog is curated and finite; availability and age ratings are not verified.'}

def run(payload, db_path=None):
    action = payload.get('action', 'list')
    db = connect(db_path or ':memory:')
    try:
        if action in ['rate', 'save']:
            mid = payload.get('movie_id')
            if mid not in BY_ID:
                raise ValueError('Unknown movie ID')
            if action == 'rate':
                rating = payload.get('rating')
                if type(rating) != int or not 1 <= rating <= 5:
                    raise ValueError('Rating must be an integer 1–5')
                with db:
                    db.execute('INSERT INTO ratings VALUES(?,?) ON CONFLICT(movie_id) DO UPDATE SET rating=excluded.rating', (mid, rating))
            else:
                if type(payload.get('saved')) != bool:
                    raise ValueError('saved must be a boolean')
                with db:
                    if payload['saved']:
                        db.execute('INSERT OR IGNORE INTO watchlist VALUES(?)', (mid,))
                    else:
                        db.execute('DELETE FROM watchlist WHERE movie_id=?', (mid,))
        ratings = {r['movie_id']: r['rating'] for r in db.execute('SELECT * FROM ratings')}
        saved = [r[0] for r in db.execute('SELECT movie_id FROM watchlist ORDER BY movie_id')]
        if action == 'recommend':
            return dict(recommend(payload, ratings), ratings=ratings, saved=saved)
        if action not in ['list', 'rate', 'save']:
            raise ValueError('Unknown action')
        return {'movies': CATALOG, 'ratings': ratings, 'saved': saved, 'genres': sorted({g for m in CATALOG for g in m['genres']}), 'languages': sorted({m['language'] for m in CATALOG}), 'engine': 'TF-IDF + cosine similarity'}
    finally:
        db.close()
