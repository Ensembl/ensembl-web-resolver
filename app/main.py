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

import os.path

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html

from app.api.resources.routes import router
from app.core.config import (
    PROJECT_NAME,
    DEBUG,
    VERSION,
    ALLOWED_HOSTS,
    STATIC_PATH,
    APP_PREFIX,
)


def _fastapi_prefix(prefix: str) -> str:
    return "" if prefix == "/" else prefix


def _prefixed_path(prefix: str, path: str) -> str:
    if prefix == "/":
        return path

    return f"{prefix}{path}"


def get_application(app_prefix: str = APP_PREFIX) -> FastAPI:
    application = FastAPI(
        title=PROJECT_NAME,
        debug=DEBUG,
        version=VERSION,
        openapi_url=None,  # Disable the default OpenAPI spec generation
        docs_url=None,  # Disable the default Swagger UI docs
        redoc_url=None,  # Disable the default ReDoc UI
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    application.include_router(router, prefix=_fastapi_prefix(app_prefix))

    @application.get(_prefixed_path(app_prefix, "/"), include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=f"{STATIC_PATH}/APISpecification.yaml", title="API Docs"
        )

    Instrumentator(excluded_handlers=["/metrics"]).instrument(
        application,
        latency_lowr_buckets=(
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1,
            1.25,
            1.5,
            1.75,
            2,
            2.5,
            5,
            10,
            30,
        ),
    ).expose(application, endpoint="/metrics", include_in_schema=False)

    return application


app = get_application()
static_files_path = os.path.join(os.path.dirname(__file__), "static")

app.mount(STATIC_PATH, StaticFiles(directory=static_files_path), name="static_files")
