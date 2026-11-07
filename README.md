# Movie-Suggestion — Frame

A completed local movie-discovery website replacing the original static concept with a real **content-based machine-learning recommender**. The original repository’s prop.html can remain as historical material; this implementation does not reuse fake testimonials, invented match percentages or nonexistent social matching.

## Product scope

- A curated 24-film catalog spanning English, Hindi, Japanese, French, Korean, Telugu and Tamil.
- Mood/story text, genre/language facets and runtime filters.
- Persistent 1–5 ratings and a local watchlist.
- Explainable TF-IDF/cosine recommendations with shared-signal terms.
- A designed responsive interface and original AI-generated cinema artwork; no fake movie posters or paid model service.

## Architecture and recommendation pipeline

```text
catalog.json → tokenize descriptive text → IDF statistics → normalized movie vectors
mood text + saved ratings → normalized preference vector
 → genre/language/runtime filter → exclude already rated movies
 → cosine similarity → ranked results + shared contributing terms
Python SQLite API → browser cards, rating controls and watchlist
```

### The ML model, precisely

The corpus combines each movie’s title, original short synopsis, genres and mood tags. Terms are lowercase alphanumeric tokens with a small stop-word list. Document frequency counts how many films contain a term. IDF is log((N+1)/(df+1))+1 and term frequency uses 1+log(count). Each movie vector is L2 normalized.

A query is vectorized with the same corpus IDF. A saved rating contributes (rating−3)×0.35 times its movie vector: likes add evidence and dislikes subtract it. The combined preference vector is normalized, candidates are filtered and already-rated titles are excluded. The ranking is the dot product of normalized vectors. Positive term contributions produce short explanations.

This is classical content-based ML, **not** LLM inference, neural semantic understanding, collaborative filtering or a guarantee of enjoyment. Unknown wording can produce no lexical signal. With ratings, a query with unknown words can still return preference-based matches. With no preference signal, the UI shows catalog discovery without invented affinity values. Similarity is shown as a decimal, not a misleading confidence percentage.

### State model

| Table | Key and invariant |
|---|---|
| ratings | movie_id primary key; integer rating 1–5; upsert replaces a rating |
| watchlist | movie_id primary key; save is idempotent |

The profile is shared by everyone using this local server. It is not an authenticated personal account. Rated films are excluded from future recommendation results, but remain visible in Discover and Watchlist so ratings can be edited.

## API examples

```json
{"action":"recommend","query":"space friendship hope","genre":"All","language":"All","max_runtime":180}
```

```json
{"action":"rate","movie_id":"interstellar","rating":5}
```

```json
{"action":"save","movie_id":"arrival","saved":true}
```

GET /api returns movies, ratings, saved IDs, genres and languages. recommend returns ranked movies with affinity/reason and an honest engine/limitation notice. Query text is limited to 300 characters; runtime must be 60–240 minutes; filters and movie IDs must exist in the catalog. Arbitrary provider URLs or prompts are not executed.

## Catalog and asset provenance

catalog.json includes concise project-authored descriptions of well-known films, not copied full plot summaries. Metadata is a finite curated sample, not a live licensed film database, content-rating guide or streaming-availability feed. Review facts and licensing before commercial expansion. cinema.webp is original AI-generated atmosphere artwork; it is not a still from a listed film or a real venue endorsement. No external font/poster/tracker request is required at runtime.

## Test matrix

Tests cover vector normalization, a known query match, language/runtime constraints, no-signal honesty, invalid ratings, persistence/upsert, seen-film exclusion, idempotent watchlist saves, unsupported filters/IDs/actions and five HTTP security guards. Browser flows cover a full catalog, empty watchlist, saving, rating-driven recommendations, populated watchlist, no-matching filter combinations and reload persistence on desktop/mobile.

## Known limits and extension roadmap

The small corpus limits novelty and recall. Token matching cannot infer all synonyms or nuanced preferences. Ratings are not debiased and diversity is not optimized. No social accounts, taste-twin network, subscriptions, streaming links, provider LLM or mobile app are implemented.

Future work, not current claims: a licensed metadata/poster provider, evaluated semantic embeddings, larger preference datasets, measurable diversity and relevance metrics, real user identity/authorization and privacy-aware account deletion. Keep explanations faithful to the actual ranking model.

## Local setup and file map

Requires Python 3.11+; no pip/npm dependencies, API keys or Docker are required for default local operation.

```bash
python server.py --port 8000
python -m unittest discover -s tests -v
```

Open http://127.0.0.1:8000. Do not open index.html directly: the browser calls the same-origin Python API. Use another --port if occupied. Tests use temporary SQLite files and synthetic data.

| File | Responsibility |
|---|---|
| index.html / styles.css | Responsive accessible website structure and presentation |
| app.js | Browser events, safe DOM text rendering, same-origin API client |
| core.py | Domain logic, validation and persistent state |
| server.py | Loopback HTTP transport and bounded JSON/static routing |
| tests/test_core.py | Domain algorithms, invalid input, persistence and mocked provider checks |
| tests/test_http.py | Origin/header/JSON/static-path guard checks |
| .github/workflows/tests.yml | Reviewable CI configuration; not proof it has run remotely |

## HTTP contract and safety

GET /health returns liveness JSON. GET /api returns the local catalog/configuration/history. POST /api accepts one JSON action and requires Content-Type: application/json and X-Local-Client: 1. Foreign Origin or untrusted Host is rejected. The server defaults to 127.0.0.1 and serves only explicit static paths; runtime .data files are never a static route.

This is a single-user **local reference app**, not a public authenticated service. Host/Origin checks do not replace login, authorization, TLS, rate limiting or CSRF/abuse review for a real internet deployment. No shell strings are executed. Frontend user/provider strings use textContent, not innerHTML.

Runtime data persists in .data/app.sqlite3 unless PROJECT_DB is set. Back up before resets. Do not commit databases, real user records, logs or environment files. SQLite concurrency is a local-machine design choice, not a cross-region scaling plan.

## Verification and deployment boundary

The domain and HTTP suite passed 20 tests locally on Python 3.13.15. Desktop 1440px and mobile 390px Chromium workflows verified successful, empty/error and persistence states. No public deployment or GitHub push was possible from the build sandbox; no remote Actions run is claimed. Python 3.11 is a compatibility target, not a locally executed version.

Use publish.sh only after review and restored network/GitHub access. It creates a separate completed-web-app branch rather than overwriting the existing main history. The website needs its Python backend; uploading only these HTML files to static hosting will not make the API work. No paid cloud service is configured or required by this package.

## Troubleshooting

- **API unavailable:** start server.py and visit its HTTP URL; file:// and static-only hosting do not provide /api.
- **Port occupied:** choose a different --port and open that address.
- **Old local data:** verify PROJECT_DB, stop the server, back up and deliberately reset only the intended .data folder.
- **Validation error:** read the inline message; a failed request is not a saved successful result.
- **Provider/network unavailable:** default offline functionality remains available and explicitly labeled; never treat a fixture as current external data.

## GitHub artwork packaging

The original cinema artwork is stored losslessly in numbered `cinema-parts/*.b64` source files because the publishing connection accepts UTF-8 text. `cinema_asset.py` joins and decodes them in memory, validates SHA-256, and the server serves the exact original WebP bytes at `/cinema.webp`. No network download, paid service, local extraction step or image-quality change is involved. Keep every part when copying the app.
