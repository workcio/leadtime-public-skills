#!/usr/bin/env python3
"""Query the cached Leadtime OpenAPI spec.

Usage:
    openapi-helper.py search <keyword>
    openapi-helper.py operation <METHOD> <PATH>
    openapi-helper.py schema <SchemaName>
"""

import json
import sys
from pathlib import Path

OPENAPI_JSON = Path("/tmp/leadtime-openapi.json")


def load_spec() -> dict:
    if not OPENAPI_JSON.exists():
        raise SystemExit(
            f"Missing {OPENAPI_JSON}. Fetch it first:\n"
            f'  curl -fsS -o {OPENAPI_JSON} https://leadtime.app/api/public/docs/json'
        )
    with OPENAPI_JSON.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_ref(spec: dict, node):
    if isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return node
        current = spec
        for part in ref[2:].split("/"):
            current = current[part]
        return current
    return node


def schema_summary(spec: dict, schema, depth=0):
    schema = resolve_ref(spec, schema)
    if not isinstance(schema, dict):
        return schema

    result = {}
    for key in ("$ref", "type", "required", "enum", "description", "format"):
        if key in schema:
            result[key] = schema[key]

    if depth >= 2:
        return result

    if schema.get("type") == "object" and "properties" in schema:
        result["properties"] = {}
        required = set(schema.get("required", []))
        for name, prop in schema["properties"].items():
            prop_summary = schema_summary(spec, prop, depth + 1)
            if isinstance(prop_summary, dict) and name in required:
                prop_summary = {"required": True, **prop_summary}
            result["properties"][name] = prop_summary
    elif schema.get("type") == "array" and "items" in schema:
        result["items"] = schema_summary(spec, schema["items"], depth + 1)

    return result


def cmd_search(spec: dict, keyword: str):
    keyword_lower = keyword.lower()
    matches = []
    for path, methods in spec.get("paths", {}).items():
        method_hits = []
        matched_fields: set[str] = set()
        if keyword_lower in path.lower():
            matched_fields.add("path")

        for method, op in methods.items():
            if not isinstance(op, dict):
                continue
            summary = (op.get("summary") or "").lower()
            operation_id = (op.get("operationId") or "").lower()
            tags = " ".join(op.get("tags", [])).lower()
            if any(keyword_lower in field for field in (summary, operation_id, tags)):
                method_hits.append(method.upper())
                if keyword_lower in summary:
                    matched_fields.add("summary")
                if keyword_lower in operation_id:
                    matched_fields.add("operationId")
                if keyword_lower in tags:
                    matched_fields.add("tags")

        if matched_fields or method_hits:
            matches.append(
                {
                    "path": path,
                    "methods": sorted(m.upper() for m in methods if isinstance(methods[m], dict)),
                    "matchedMethods": sorted(set(method_hits)),
                    "matchedFields": sorted(matched_fields),
                }
            )
    print(json.dumps(matches, indent=2, ensure_ascii=False))


def cmd_operation(spec: dict, method: str, path: str):
    path_obj = spec.get("paths", {}).get(path)
    if not path_obj:
        raise SystemExit(f"Path not found: {path}")
    op = path_obj.get(method.lower())
    if not op:
        raise SystemExit(f"Method {method.upper()} not found on {path}")

    result = {
        "path": path,
        "method": method.upper(),
        "summary": op.get("summary"),
        "description": op.get("description"),
        "tags": op.get("tags", []),
        "operationId": op.get("operationId"),
        "parameters": op.get("parameters", []),
        "security": op.get("security", []),
        "requestBody": None,
        "responses": {},
    }

    request_body = op.get("requestBody")
    if request_body:
        app_json = request_body.get("content", {}).get("application/json")
        result["requestBody"] = {
            "required": request_body.get("required", False),
            "schema": schema_summary(spec, app_json.get("schema", {})) if app_json else None,
        }

    for code, response in op.get("responses", {}).items():
        content = response.get("content", {}).get("application/json")
        result["responses"][code] = {
            "description": response.get("description"),
            "schema": schema_summary(spec, content.get("schema", {})) if content else None,
        }

    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_schema(spec: dict, name: str):
    schemas = spec.get("components", {}).get("schemas", {})
    if name not in schemas:
        available = ", ".join(sorted(schemas.keys())[:20])
        raise SystemExit(f"Schema '{name}' not found. Some available: {available}")
    print(json.dumps(schema_summary(spec, schemas[name]), indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) < 3:
        raise SystemExit(
            "Usage:\n"
            "  openapi-helper.py search <keyword>\n"
            "  openapi-helper.py operation <METHOD> <PATH>\n"
            "  openapi-helper.py schema <SchemaName>"
        )

    command = sys.argv[1]
    spec = load_spec()

    if command == "search":
        cmd_search(spec, sys.argv[2])
    elif command == "operation":
        if len(sys.argv) != 4:
            raise SystemExit("Usage: openapi-helper.py operation <METHOD> <PATH>")
        cmd_operation(spec, sys.argv[2], sys.argv[3])
    elif command == "schema":
        cmd_schema(spec, sys.argv[2])
    else:
        raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
