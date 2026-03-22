"""Database scanner: parse Prisma schema and extract model structure."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class FieldInfo:
    """A single field in a model."""

    name: str
    type: str
    is_optional: bool = False
    is_list: bool = False
    is_id: bool = False
    is_unique: bool = False
    is_relation: bool = False
    map_to: Optional[str] = None
    db_type: Optional[str] = None
    default: Optional[str] = None


@dataclass
class ModelInfo:
    """A parsed Prisma model."""

    name: str
    table_name: str  # from @@map or lowercase name
    fields: list[FieldInfo] = field(default_factory=list)
    relations: list[str] = field(default_factory=list)
    indices: list[str] = field(default_factory=list)
    has_tenant_id: bool = False
    has_created_at: bool = False
    has_updated_at: bool = False
    has_deleted_at: bool = False


@dataclass
class EnumInfo:
    """A parsed Prisma enum."""

    name: str
    values: list[str] = field(default_factory=list)


@dataclass
class DatabaseScanResult:
    """Complete database scan output."""

    models: list[ModelInfo] = field(default_factory=list)
    enums: list[EnumInfo] = field(default_factory=list)
    extensions: list[str] = field(default_factory=list)
    provider: str = "unknown"
    model_count: int = 0
    enum_count: int = 0
    relation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DatabaseScanner:
    """Scans Prisma schema files and extracts structured database information."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def scan(self, schema_path: Optional[str] = None) -> DatabaseScanResult:
        """Parse a Prisma schema file and return structured results."""
        path = self._resolve_schema_path(schema_path)
        if not path or not path.exists():
            return DatabaseScanResult()

        content = path.read_text(encoding="utf-8")

        models = self._parse_models(content)
        enums = self._parse_enums(content)
        extensions = self._parse_extensions(content)
        provider = self._parse_provider(content)

        total_relations = sum(len(m.relations) for m in models)

        return DatabaseScanResult(
            models=models,
            enums=enums,
            extensions=extensions,
            provider=provider,
            model_count=len(models),
            enum_count=len(enums),
            relation_count=total_relations,
        )

    def _resolve_schema_path(self, explicit: Optional[str] = None) -> Optional[Path]:
        """Find the schema.prisma file."""
        if explicit:
            p = Path(explicit)
            return p if p.is_absolute() else self.root / p

        # Read from loom.json
        loom_json = self.root / ".context" / "loom.json"
        if loom_json.exists():
            try:
                data = json.loads(loom_json.read_text(encoding="utf-8"))
                sp = data.get("database", {}).get("schema_path")
                if sp:
                    return self.root / sp
            except (json.JSONDecodeError, OSError):
                pass

        # Common locations
        for candidate in [
            "prisma/schema.prisma",
            "packages/core/database/prisma/schema.prisma",
            "src/prisma/schema.prisma",
        ]:
            p = self.root / candidate
            if p.exists():
                return p

        return None

    def _parse_models(self, content: str) -> list[ModelInfo]:
        """Extract all model definitions."""
        models: list[ModelInfo] = []
        pattern = re.compile(r"model\s+(\w+)\s*\{([^}]+)\}", re.DOTALL)

        for match in pattern.finditer(content):
            name = match.group(1)
            body = match.group(2)

            # Parse table name from @@map
            table_map = re.search(r'@@map\("(\w+)"\)', body)
            table_name = table_map.group(1) if table_map else name.lower()

            fields = self._parse_fields(body)
            relations = [f.name for f in fields if f.is_relation]
            indices = re.findall(r"@@index\(\[([^\]]+)\]\)", body)

            model = ModelInfo(
                name=name,
                table_name=table_name,
                fields=fields,
                relations=relations,
                indices=[idx.strip() for idx in indices],
                has_tenant_id=any(f.name == "tenantId" for f in fields),
                has_created_at=any(f.name == "createdAt" for f in fields),
                has_updated_at=any(f.name == "updatedAt" for f in fields),
                has_deleted_at=any(f.name == "deletedAt" for f in fields),
            )
            models.append(model)

        return models

    def _parse_fields(self, body: str) -> list[FieldInfo]:
        """Extract fields from a model body."""
        fields: list[FieldInfo] = []
        for line in body.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("@@"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            name = parts[0]
            raw_type = parts[1]

            # Skip relation-only syntax like @relation(...)
            if name.startswith("@"):
                continue

            is_optional = raw_type.endswith("?")
            is_list = raw_type.endswith("[]")
            clean_type = raw_type.rstrip("?").rstrip("[]")

            # Check if it's a relation (type starts with uppercase and isn't a known scalar)
            scalar_types = {
                "String", "Int", "Float", "Boolean", "DateTime", "Json",
                "BigInt", "Decimal", "Bytes",
            }
            is_relation = (
                clean_type[0].isupper() and clean_type not in scalar_types
                if clean_type
                else False
            )

            # Parse decorators
            rest = " ".join(parts[2:]) if len(parts) > 2 else ""
            map_match = re.search(r'@map\("(\w+)"\)', rest)
            db_match = re.search(r"@db\.(\w+)", rest)
            is_id = "@id" in rest
            is_unique = "@unique" in rest
            default_match = re.search(r"@default\(([^)]+)\)", rest)

            fields.append(FieldInfo(
                name=name,
                type=clean_type,
                is_optional=is_optional,
                is_list=is_list,
                is_id=is_id,
                is_unique=is_unique,
                is_relation=is_relation,
                map_to=map_match.group(1) if map_match else None,
                db_type=db_match.group(1) if db_match else None,
                default=default_match.group(1) if default_match else None,
            ))

        return fields

    def _parse_enums(self, content: str) -> list[EnumInfo]:
        """Extract all enum definitions."""
        enums: list[EnumInfo] = []
        pattern = re.compile(r"enum\s+(\w+)\s*\{([^}]+)\}", re.DOTALL)

        for match in pattern.finditer(content):
            name = match.group(1)
            body = match.group(2)
            values = [
                line.strip()
                for line in body.strip().split("\n")
                if line.strip() and not line.strip().startswith("//")
            ]
            enums.append(EnumInfo(name=name, values=values))

        return enums

    def _parse_extensions(self, content: str) -> list[str]:
        """Extract PostgreSQL extensions."""
        extensions: list[str] = []
        for match in re.finditer(r"extensions\s*=\s*\[([^\]]+)\]", content):
            raw = match.group(1)
            for ext in re.findall(r"(\w+)", raw):
                if ext not in {"map"}:
                    extensions.append(ext)
        return extensions

    def _parse_provider(self, content: str) -> str:
        """Extract database provider."""
        match = re.search(r'provider\s*=\s*"(\w+)"', content)
        if match and match.group(1) in {"postgresql", "mysql", "sqlite", "mongodb", "sqlserver"}:
            return match.group(1)
        return "unknown"
