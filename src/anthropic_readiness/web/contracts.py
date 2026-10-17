"""HTTP schema declarations share the same packaged shapes as runtime checks."""

from __future__ import annotations

from copy import deepcopy

from fastapi import FastAPI

from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.schema import load_schema


def api_shape(kind: str) -> JsonObject:
    document = load_schema("web-api")
    for variant in objects(document["oneOf"]):
        properties = object_value(variant["properties"])
        if object_value(properties["kind"])["const"] == kind:
            return object_value(properties["data"])
    raise ValueError("unknown_api_contract")


def response_contract(kind: str, status: int = 200) -> dict[int | str, dict[str, object]]:
    return {
        status: {
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/" + kind}}}
        }
    }


def request_contract(kind: str) -> dict[str, object]:
    return {
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/" + kind}}},
        }
    }


def relocate(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return {
            key: (
                child.replace("#/$defs/", "#/components/schemas/contract_definitions/$defs/")
                if key == "$ref" and isinstance(child, str)
                else relocate(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [relocate(child) for child in value]
    return value


class ContractApplication(FastAPI):
    """Publish packaged contracts through the framework's OpenAPI extension point."""

    def openapi(self) -> dict[str, object]:
        document = object_value(super().openapi())
        components = object_value(document.get("components", {}))
        schemas = object_value(components.get("schemas", {}))
        source = load_schema("web-api")
        schemas["contract_definitions"] = {"$defs": relocate(deepcopy(source["$defs"]))}
        for variant in objects(source["oneOf"]):
            properties = object_value(variant["properties"])
            name = str(object_value(properties["kind"])["const"])
            schemas[name] = relocate(properties["data"])
        components["schemas"] = schemas
        document["components"] = components
        return dict(document)
