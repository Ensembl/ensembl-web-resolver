"""
See the NOTICE file distributed with this work for additional information
regarding copyright ownership.


Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import sys

from loguru import logger
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings

from .logging import InterceptHandler

VERSION = "0.0.0"
API_PREFIX = ""

config = Config(".env")

ENSEMBL_SEARCH_HUB_API: str = config(
    "ENSEMBL_SEARCH_HUB_API",
    cast=str,
    default="http://ensembl-search-hub-svc:8083/api/search/stable-id",
)
DEFAULT_APP = config("DEFAULT_APP", cast=str, default="entity-viewer")
ENSEMBL_URL = config("ENSEMBL_URL", cast=str, default="https://beta.ensembl.org")
RAPID_ARCHIVE_URL = config("RAPID_ARCHIVE_URL", cast=str, default="https://rapid-archive.ensembl.org")
NCBI_DATASETS_URL = config(
    "NCBI_DATASETS_URL", cast=str, default="https://api.ncbi.nlm.nih.gov/datasets/v2"
)

DEBUG: bool = config("DEBUG", cast=bool, default=False)
PROJECT_NAME: str = config("PROJECT_NAME", default="Ensembl Web Resolver")
ALLOWED_HOSTS: list[str] = config(
    "ALLOWED_HOSTS",
    cast=CommaSeparatedStrings,
    default="*",
)

# logging configuration
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOGGERS = ("uvicorn.asgi", "uvicorn.access")

log = logging.getLogger("gunicorn.access")

logging.getLogger().handlers = [InterceptHandler()]
for logger_name in LOGGERS:
    logging_logger = logging.getLogger(logger_name)
    logging_logger.handlers = [InterceptHandler(level=LOGGING_LEVEL)]

logger.configure(handlers=[{"sink": sys.stderr, "level": LOGGING_LEVEL}])
