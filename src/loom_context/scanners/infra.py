"""Infrastructure scanner: detect services, check availability, suggest setup."""

from __future__ import annotations

import platform
import shutil
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_IS_MAC = platform.system() == "Darwin"


def _brew_or_apt(brew: str, apt: str) -> str:
    """Return brew command on macOS, apt on Linux."""
    return brew if _IS_MAC else apt


@dataclass(frozen=True)
class ServiceDef:
    """Definition of an infrastructure service."""

    name: str
    category: str
    default_port: int = 0
    install_cmd: str = ""
    start_cmd: str = ""
    stop_cmd: str = ""
    status_cmd: str = ""
    docker_cmd: str = ""
    config_env: str = ""
    config_hint: str = ""


@dataclass
class ServiceStatus:
    """Runtime status of an infrastructure service."""

    service: ServiceDef
    installed: Optional[bool] = None
    running: Optional[bool] = None
    port_checked: int = 0


# --- Service Definitions ---

_REDIS = ServiceDef(
    name="Redis",
    category="cache",
    default_port=6379,
    install_cmd=_brew_or_apt("brew install redis", "sudo apt install redis-server"),
    start_cmd=_brew_or_apt("brew services start redis", "sudo systemctl start redis"),
    stop_cmd=_brew_or_apt("brew services stop redis", "sudo systemctl stop redis"),
    status_cmd="redis-cli ping",
    docker_cmd="docker run -d --name redis -p 6379:6379 redis:alpine",
    config_env="REDIS_URL",
    config_hint="redis://localhost:6379",
)

_POSTGRES = ServiceDef(
    name="PostgreSQL",
    category="database",
    default_port=5432,
    install_cmd=_brew_or_apt("brew install postgresql@16", "sudo apt install postgresql"),
    start_cmd=_brew_or_apt("brew services start postgresql@16", "sudo systemctl start postgresql"),
    stop_cmd=_brew_or_apt("brew services stop postgresql@16", "sudo systemctl stop postgresql"),
    status_cmd="pg_isready",
    docker_cmd=(
        "docker run -d --name postgres -p 5432:5432 "
        "-e POSTGRES_PASSWORD=postgres postgres:16-alpine"
    ),
    config_env="DATABASE_URL",
    config_hint="postgresql://user:pass@localhost:5432/dbname",
)

_MYSQL = ServiceDef(
    name="MySQL",
    category="database",
    default_port=3306,
    install_cmd=_brew_or_apt("brew install mysql", "sudo apt install mysql-server"),
    start_cmd=_brew_or_apt("brew services start mysql", "sudo systemctl start mysql"),
    stop_cmd=_brew_or_apt("brew services stop mysql", "sudo systemctl stop mysql"),
    status_cmd="mysqladmin ping",
    docker_cmd=("docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql:8"),
    config_env="MYSQL_URL",
    config_hint="mysql://user:pass@localhost:3306/dbname",
)

_MONGODB = ServiceDef(
    name="MongoDB",
    category="database",
    default_port=27017,
    install_cmd=_brew_or_apt("brew install mongodb-community", "sudo apt install mongodb"),
    start_cmd=_brew_or_apt("brew services start mongodb-community", "sudo systemctl start mongod"),
    docker_cmd="docker run -d --name mongo -p 27017:27017 mongo:7",
    config_env="MONGODB_URI",
    config_hint="mongodb://localhost:27017/dbname",
)

_ELASTICSEARCH = ServiceDef(
    name="Elasticsearch",
    category="search",
    default_port=9200,
    docker_cmd=(
        "docker run -d --name es -p 9200:9200 -e discovery.type=single-node elasticsearch:8.12.0"
    ),
    config_env="ELASTICSEARCH_URL",
    config_hint="http://localhost:9200",
)

_RABBITMQ = ServiceDef(
    name="RabbitMQ",
    category="queue",
    default_port=5672,
    install_cmd=_brew_or_apt("brew install rabbitmq", "sudo apt install rabbitmq-server"),
    start_cmd=_brew_or_apt("brew services start rabbitmq", "sudo systemctl start rabbitmq-server"),
    docker_cmd=("docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management"),
    config_env="AMQP_URL",
    config_hint="amqp://localhost:5672",
)

_MEILISEARCH = ServiceDef(
    name="Meilisearch",
    category="search",
    default_port=7700,
    install_cmd="brew install meilisearch" if _IS_MAC else "",
    docker_cmd="docker run -d --name meili -p 7700:7700 getmeili/meilisearch:latest",
    config_env="MEILI_URL",
    config_hint="http://localhost:7700",
)

_KAFKA = ServiceDef(
    name="Kafka",
    category="queue",
    default_port=9092,
    docker_cmd="docker compose up -d  # (needs docker-compose.yml)",
    config_env="KAFKA_BROKERS",
    config_hint="localhost:9092",
)

_MINIO = ServiceDef(
    name="MinIO",
    category="storage",
    default_port=9000,
    install_cmd="brew install minio" if _IS_MAC else "",
    docker_cmd=(
        "docker run -d --name minio -p 9000:9000 -p 9001:9001 "
        "minio/minio server /data --console-address :9001"
    ),
    config_env="MINIO_ENDPOINT",
    config_hint="http://localhost:9000",
)

_SQLITE = ServiceDef(name="SQLite", category="database")

# Package name → service definition
INFRA_SERVICES: dict[str, ServiceDef] = {
    "pg": _POSTGRES,
    "@prisma/client": _POSTGRES,
    "prisma": _POSTGRES,
    "sqlalchemy": _POSTGRES,
    "alembic": _POSTGRES,
    "mysql2": _MYSQL,
    "mongoose": _MONGODB,
    "sqlite3": _SQLITE,
    "better-sqlite3": _SQLITE,
    "expo-sqlite": _SQLITE,
    "redis": _REDIS,
    "ioredis": _REDIS,
    "bull": _REDIS,
    "bullmq": _REDIS,
    "celery": _REDIS,
    "elasticsearch": _ELASTICSEARCH,
    "@elastic/elasticsearch": _ELASTICSEARCH,
    "meilisearch": _MEILISEARCH,
    "amqplib": _RABBITMQ,
    "kafkajs": _KAFKA,
    "minio": _MINIO,
}


@dataclass
class InfraReport:
    """Result of infrastructure analysis."""

    services: list[ServiceStatus] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


def scan_infrastructure(dependencies: list[str], check_ports: bool = True) -> InfraReport:
    """Analyze project dependencies for infrastructure requirements."""
    report = InfraReport()
    seen: set[str] = set()

    for dep_name in dependencies:
        svc_def = INFRA_SERVICES.get(dep_name)
        if svc_def is None or svc_def.name in seen:
            continue
        seen.add(svc_def.name)

        if svc_def.default_port == 0:
            continue

        running = None
        if check_ports:
            running = _check_port(svc_def.default_port)

        installed = _check_installed(svc_def)

        status = ServiceStatus(
            service=svc_def,
            installed=installed,
            running=running,
            port_checked=svc_def.default_port,
        )
        report.services.append(status)

        if running is False:
            report.warnings.append(f"{svc_def.name} not running on port {svc_def.default_port}")
            if installed:
                report.suggestions.append(f"Start: {svc_def.start_cmd}")
            elif svc_def.install_cmd:
                report.suggestions.append(f"Install: {svc_def.install_cmd}")
            if svc_def.docker_cmd:
                report.suggestions.append(f"Or Docker: {svc_def.docker_cmd}")

    return report


def _check_port(port: int, host: str = "127.0.0.1", timeout: float = 0.3) -> bool:
    """Check if a port is open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, port)) == 0
    except OSError:
        return False


def _check_installed(svc: ServiceDef) -> Optional[bool]:
    """Check if a service binary is available on PATH."""
    binaries: dict[str, list[str]] = {
        "Redis": ["redis-server", "redis-cli"],
        "PostgreSQL": ["psql", "pg_isready"],
        "MySQL": ["mysql", "mysqld"],
        "MongoDB": ["mongod", "mongosh"],
        "Elasticsearch": ["elasticsearch"],
        "RabbitMQ": ["rabbitmq-server"],
        "Meilisearch": ["meilisearch"],
    }
    candidates = binaries.get(svc.name)
    if not candidates:
        return None
    return any(shutil.which(b) is not None for b in candidates)


def detect_terraform(root: Path) -> Optional[dict[str, list[str]]]:
    """Detect Terraform project structure."""
    tf_files = list(root.glob("*.tf"))
    if not tf_files:
        tf_files = list(root.glob("**/*.tf"))
        if not tf_files:
            return None

    modules: list[str] = []
    providers: list[str] = []
    backends: list[str] = []

    for tf_file in tf_files:
        try:
            content = tf_file.read_text(encoding="utf-8")
        except OSError:
            continue

        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("module "):
                name = stripped.split('"')[1] if '"' in stripped else ""
                if name:
                    modules.append(name)
            elif stripped.startswith("provider "):
                name = stripped.split('"')[1] if '"' in stripped else ""
                if name and name not in providers:
                    providers.append(name)
            elif stripped.startswith("backend "):
                name = stripped.split('"')[1] if '"' in stripped else ""
                if name and name not in backends:
                    backends.append(name)

    return {
        "tf_files": [str(f.relative_to(root)) for f in tf_files[:20]],
        "modules": modules,
        "providers": providers,
        "backends": backends,
    }
