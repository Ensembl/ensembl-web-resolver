CREATE TABLE IF NOT EXISTS legacy_url_path_mappings (
  source_path TEXT PRIMARY KEY,
  target_url TEXT NOT NULL,
  enabled BOOLEAN DEFAULT TRUE
);

INSERT OR REPLACE INTO legacy_url_path_mappings (
  source_path,
  target_url,
  enabled
)
VALUES
  (
    '/multi/tools/blast',
    'https://dev-2020.ensembl.org/tools/blast',
    TRUE
  ),
  (
    '/multi/search/results',
    'https://dev-2020.ensembl.org/species-selector',
    TRUE
  );

CREATE TABLE IF NOT EXISTS legacy_url_host_mappings (
  source_host TEXT PRIMARY KEY,
  target_url TEXT NOT NULL,
  enabled BOOLEAN DEFAULT TRUE
);

INSERT OR REPLACE INTO legacy_url_host_mappings (
  source_host,
  target_url,
  enabled
)
VALUES
  (
    'staging-plants.ensembl.org',
    'https://dev-2020.ensembl.org',
    TRUE
  ),
  (
    'staging-metazoa.ensembl.org',
    'https://dev-2020.ensembl.org',
    TRUE
  ),
  (
    'staging-fungi.ensembl.org',
    'https://dev-2020.ensembl.org',
    TRUE
  ),
  (
    'staging-bacteria.ensembl.org',
    'https://dev-2020.ensembl.org',
    TRUE
  ),
  (
    'staging-protists.ensembl.org',
    'https://dev-2020.ensembl.org',
    TRUE
  );
