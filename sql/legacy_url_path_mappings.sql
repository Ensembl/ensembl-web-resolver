-- TODO: remove all staging host and dev-2020 and replace them with the proper production Ensembl hosts once we're ready for the switch. 
-- This will require a new migration to update the existing mappings in the database.

CREATE TABLE IF NOT EXISTS legacy_url_path_mappings (
  source_host TEXT NOT NULL DEFAULT '',
  source_path TEXT NOT NULL,
  target_url TEXT NOT NULL,
  enabled BOOLEAN DEFAULT TRUE,
  PRIMARY KEY (source_host, source_path)
);

INSERT OR REPLACE INTO legacy_url_path_mappings (
  source_host,
  source_path,
  target_url,
  enabled
)
-- INFO: The lookup prefers exact source_host + source_path, then falls back to generic '' + source_path.
VALUES
  -- Biomart mappings
  (
    'staging.ensembl.org',
    '/biomart/martview',
    'https://jun2026.archive.ensembl.org/biomart/martview',
    TRUE
  ),
  (
    'staging-plants.ensembl.org',
    '/biomart/martview',
    'https://eg63-plants.archive.ensembl.org/biomart/martview',
    TRUE
  ),
  (
    'staging-fungi.ensembl.org',
    '/biomart/martview',
    'https://eg63-fungi.archive.ensembl.org/biomart/martview',
    TRUE
  ),
  (
    'staging-protists.ensembl.org',
    '/biomart/martview',
    'https://eg63-protists.archive.ensembl.org/biomart/martview',
    TRUE
  ),
  -- BLAST mappings
  (
    '',
    '/multi/tools/blast',
    'https://dev-2020.ensembl.org/tools/blast',
    TRUE
  ),
  -- VEP mappings
  (
    '',
    '/multi/tools/vep',
    'https://dev-2020.ensembl.org/tools/vep',
    TRUE
  ),
  (
    '',
    '/info/docs/tools/vep/index.html',
    'https://jun2026.archive.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    '',
    '/info/docs/tools/vep/script/index.html',
    'https://jun2026.archive.ensembl.org/info/docs/tools/vep/script/index.html',
    TRUE
  ),
  -- Search mappings
  (
    '',
    '/multi/search/results',
    'https://dev-2020.ensembl.org/genome-selector',
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
  -- Map all divisions to the new Ensembl
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
