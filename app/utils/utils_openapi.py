import json
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import os


def generate_openapi_json(app: FastAPI, output_path: str = "openapi.json"):
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version if hasattr(app, 'version') else "1.0.0",
        description=app.description if hasattr(app, 'description') else None,
        routes=app.routes,
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
