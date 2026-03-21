"""Infrastructure scanner: detect services, check availability, suggest setup."""

from __future__ import annotations

import shutil
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from loom_context.knowledge import get_registry
from loom_context.knowledge.models import InfraServiceDef

_registry = get_registry()


@dataclass(frozen=True)
class ServiceDef:
    """Definition of an infrastructure service (backward-compatible wrapper)."""

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

    @classmethod
    def from_registry(cls, svc: InfraServiceDef) -> ServiceDef:
        """Create from Knowledge Registry InfraServiceDef."""
        return cls(
            name=svc.name,
            category=svc.category,
            default_port=svc.default_port,
            install_cmd=_registry.get_infra_install_cmd(svc),
            start_cmd=_registry.get_infra_start_cmd(svc),
            stop_cmd=_registry.get_infra_stop_cmd(svc),
            status_cmd=svc.status_cmd,
            docker_cmd=svc.docker_cmd,
            config_env=svc.config_env,
            config_hint=svc.config_hint,
        )


@dataclass
class ServiceStatus:
    """Runtime status of an infrastructure service."""

    service: ServiceDef
    installed: Optional[bool] = None
    running: Optional[bool] = None
    port_checked: int = 0


@dataclass
class InfraReport:
    """Result of infrastructure analysis."""

    services: list[ServiceStatus] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


def _resolve_service(dep_name: str) -> Optional[ServiceDef]:
    """Resolve a dependency name to a ServiceDef via Knowledge Registry."""
    infra_svc = _registry.get_infra_service(dep_name)
    if infra_svc is None:
        return None
    return ServiceDef.from_registry(infra_svc)


def scan_infrastructure(
    dependencies: list[str], check_ports: bool = True
) -> InfraReport:
    """Analyze project dependencies for infrastructure requirements."""
    report = InfraReport()
    seen: set[str] = set()

    for dep_name in dependencies:
        svc_def = _resolve_service(dep_name)
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
            report.warnings.append(
                f"{svc_def.name} not running on port {svc_def.default_port}"
            )
            if installed:
                report.suggestions.append(f"Start: {svc_def.start_cmd}")
            elif svc_def.install_cmd:
                report.suggestions.append(f"Install: {svc_def.install_cmd}")
            if svc_def.docker_cmd:
                report.suggestions.append(f"Or Docker: {svc_def.docker_cmd}")

    return report


def _check_port(
    port: int, host: str = "127.0.0.1", timeout: float = 0.3
) -> bool:
    """Check if a port is open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, port)) == 0
    except OSError:
        return False


def _check_installed(svc: ServiceDef) -> Optional[bool]:
    """Check if a service binary is available on PATH."""
    # Get binaries from registry
    infra_services = _registry.get_all_infra_services()
    for reg_svc in infra_services.values():
        if reg_svc.name == svc.name and reg_svc.binaries:
            return any(shutil.which(b) is not None for b in reg_svc.binaries)
    return None


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
