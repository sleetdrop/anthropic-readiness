"""Data-only diagnostic values. Adapters validate before constructing them."""

from dataclasses import dataclass

from anthropic_readiness.models import JsonObject


@dataclass(frozen=True)
class ImplementationIdentity:
    document: JsonObject


@dataclass(frozen=True)
class RetestRecipe:
    document: JsonObject


@dataclass(frozen=True)
class AssessmentContext:
    document: JsonObject


@dataclass(frozen=True)
class DiagnosticPackage:
    document: JsonObject


@dataclass(frozen=True)
class BaselineRecord:
    document: JsonObject


@dataclass(frozen=True)
class Comparison:
    document: JsonObject


@dataclass(frozen=True)
class WorkbenchView:
    document: JsonObject


@dataclass(frozen=True)
class DocumentView:
    document: JsonObject
