# Ensembl Web Resolver

The resolver service generates new Ensembl website urls for different features based on their stable ids, as well as other optional parameters.

### Deploy the app and run docker-compose

```
git clone https://github.com/Ensembl/ensembl-web-resolver.git
cd ensembl-web-resolver
mv sample-env .env
docker-compose -f docker-compose.yml up
```

Some urls that are available after deployment on your local machine:

- http://localhost:8001/id/ENSG00000127720
- http://localhost:8001/id/ENSG00000127720.3

### Running application locally

From the project root directory run:

```
mv sample-env .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --port 8001 --reload
```

`APP_PREFIX` defaults to `/`. Set it only when the app should be served under a path prefix, for example `/api/resolver`.

### Apply legacy URL mapping SQL

If the legacy URL mapping tables need to be created or refreshed in the local DuckDB file, run:

```
duckdb resolver_mappings.db < sql/legacy_url_path_mappings.sql
```

### Run unit tests

```
python -m unittest tests.test_resolver
python -m unittest tests.test_rapid
```
