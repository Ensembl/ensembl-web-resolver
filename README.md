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

### Stable ID index

`/id/{stable_id}` and `/rapid/id/{stable_id}` can use a local fast-match Redb
index. Set `FAST_MATCH_ENABLED=true` and configure `FAST_MATCH_DB_PATH` to use
it; set `FAST_MATCH_ENABLED=false` to retain the search-hub API lookup. The
index is expected to have stable and unversioned stable IDs as keys and values
in the `genome_id|doc_type` format, with multiple values delimited by `+`.

The `fm_py` dependency is published to the private GitLab package registry.
Install the resolver dependencies with a GitLab token that has
`read_package_registry` access:

```
export GITLAB_USER="your-gitlab-username"
export GITLAB_TOKEN="your-read-package-registry-token"

python -m pip install \
  --extra-index-url "https://${GITLAB_USER}:${GITLAB_TOKEN}@gitlab.ebi.ac.uk/api/v4/projects/6228/packages/pypi/simple" \
  -r requirements.txt
```

Do not store the GitLab token in `.env` or commit it to source control.

#### GitHub Actions

The test workflow installs `fm_py` from the private GitLab package registry.
Configure these GitHub repository secrets for CI:

```
GITLAB_USER    # GitLab username or token username
GITLAB_TOKEN   # GitLab token with read_api scope and access to project 6228
```

The GitHub Actions runner is Linux x86_64, so the registry must also contain a
compatible Linux x86_64 `abi3` wheel, for example
`fm_py-0.1.1-cp38-abi3-manylinux_2_28_x86_64.whl`.

### Apply legacy URL mapping SQL

If the legacy URL mapping tables need to be created or refreshed in the local DuckDB file, run:

```
duckdb resolver_mappings.db < sql/legacy_url_path_mappings.sql
```

### Run unit tests

```
python -m pip install -r requirements-dev.txt
pytest
```
