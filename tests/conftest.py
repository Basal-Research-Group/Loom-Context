"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project structure for testing."""
    src = tmp_path / "src"
    src.mkdir()

    # Create domain layer
    domain = src / "domain"
    domain.mkdir()
    (domain / "entities").mkdir()
    (domain / "ports").mkdir()
    (src / "domain" / "entities" / "User.ts").write_text(
        "export interface IUser { id: string; name: string; }\n"
        "export class User implements IUser {\n"
        "  constructor(public id: string, public name: string) {}\n"
        "}\n"
    )
    (src / "domain" / "ports" / "IUserRepository.ts").write_text(
        'import { IUser } from "../entities/User";\n'
        'export interface IUserRepository { findById(id: string): Promise<IUser>; }\n'
    )

    # Create infrastructure layer
    infra = src / "infrastructure"
    infra.mkdir()
    (infra / "repositories").mkdir()
    (src / "infrastructure" / "repositories" / "UserRepository.ts").write_text(
        'import { IUserRepository } from "../../domain/ports/IUserRepository";\n'
        "export class UserRepository implements IUserRepository {\n"
        "  async findById(id: string) { return null as any; }\n"
        "}\n"
    )

    # Create presentation layer
    presentation = src / "presentation"
    presentation.mkdir()
    (presentation / "components").mkdir()
    (presentation / "hooks").mkdir()
    (src / "presentation" / "components" / "UserProfile.tsx").write_text(
        'import React from "react";\nexport const UserProfile = () => <div>Profile</div>;\n'
    )
    (src / "presentation" / "hooks" / "useUser.ts").write_text(
        'export function useUser(id: string) { return { id, name: "test" }; }\n'
    )

    # Create core layer
    core = src / "core"
    core.mkdir()
    (core / "services").mkdir()
    (src / "core" / "services" / "AuthService.ts").write_text(
        'export class AuthService { async login() { return true; } }\n'
    )

    # package.json
    pkg = {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {
            "react": "^19.0.0",
            "react-native": "^0.79.0",
            "zustand": "^5.0.0",
        },
        "devDependencies": {
            "typescript": "^5.8.0",
            "jest": "^29.0.0",
        },
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg, indent=2))

    # tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "strict": True,
            "paths": {
                "@domain/*": ["src/domain/*"],
                "@core/*": ["src/core/*"],
                "@infrastructure/*": ["src/infrastructure/*"],
                "@presentation/*": ["src/presentation/*"],
            },
        },
    }
    (tmp_path / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

    # AGENTS.md
    (tmp_path / "AGENTS.md").write_text("# Agent Guidelines\n\nFollow clean architecture.\n")

    # docs/
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "architecture.md").write_text(
        "# Architecture\n\n## Layers\n\nClean architecture with 4 layers.\n"
    )
    (docs / "plans").mkdir()
    (docs / "plans" / "roadmap.md").write_text(
        "# Roadmap\n\n- [x] Setup project\n- [ ] Add auth\n- [ ] Add payments\n"
    )

    # .gitignore
    (tmp_path / ".gitignore").write_text("node_modules/\ndist/\n.env\n")

    return tmp_path
