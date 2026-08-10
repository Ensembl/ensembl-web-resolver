-- Support both staging and production legacy Ensembl hosts.

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
    'www.ensembl.org',
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
    'plants.ensembl.org',
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
    'fungi.ensembl.org',
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
  (
    'protists.ensembl.org',
    '/biomart/martview',
    'https://eg63-protists.archive.ensembl.org/biomart/martview',
    TRUE
  ),
  -- BLAST mappings
  (
    '',
    '/multi/tools/blast',
    'https://www.ensembl.org/tools/blast',
    TRUE
  ),
  -- VEP mappings
  (
    '',
    '/multi/tools/vep',
    'https://www.ensembl.org/tools/vep',
    TRUE
  ),
  (
    '',
    '/vep',
    'https://jun2026.archive.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  -- Division VEP documentation is only available on its matching archive.
  (
    'staging-plants.ensembl.org',
    '/vep',
    'https://eg63-plants.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    'plants.ensembl.org',
    '/vep',
    'https://eg63-plants.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    'staging-metazoa.ensembl.org',
    '/vep',
    'https://eg63-metazoa.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    'metazoa.ensembl.org',
    '/vep',
    'https://eg63-metazoa.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    'staging-fungi.ensembl.org',
    '/vep',
    'https://eg63-fungi.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    'fungi.ensembl.org',
    '/vep',
    'https://eg63-fungi.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    'staging-protists.ensembl.org',
    '/vep',
    'https://eg63-protists.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    'protists.ensembl.org',
    '/vep',
    'https://eg63-protists.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    'staging-bacteria.ensembl.org',
    '/vep',
    'https://eg63-bacteria.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    'bacteria.ensembl.org',
    '/vep',
    'https://eg63-bacteria.ensembl.org/info/docs/tools/vep/index.html',
    TRUE
  ),
  (
    '',
    '/tools/vep',
    'https://www.ensembl.org/tools/vep',
    TRUE
  ),
  -- Search mappings
  (
    '',
    '/multi/search/results',
    'https://www.ensembl.org/genome-selector',
    TRUE
  ),
  -- Legacy division landing pages now share the new Ensembl homepage.
  (
    '',
    '/index.html',
    'https://www.ensembl.org/',
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
  -- Map divisions to the new Ensembl.
  (
    'staging-plants.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  ),
  (
    'plants.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  ),
  (
    'staging-metazoa.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  ),
  (
    'metazoa.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  ),
  (
    'staging-fungi.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  ),
  (
    'fungi.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  ),
  (
    'staging-bacteria.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  ),
  (
    'bacteria.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  ),
  (
    'staging-protists.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  ),
  (
    'protists.ensembl.org',
    'https://www.ensembl.org',
    TRUE
  );
