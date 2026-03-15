"""Dependency scanner: parses package managers and categorizes dependencies."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loom_context.scanners.base import BaseScanner

# Known package categorization database
KNOWN_PACKAGES: dict[str, tuple[str, str]] = {
    # UI Frameworks
    "react": ("ui-framework", "React UI library"),
    "react-dom": ("ui-framework", "React DOM renderer"),
    "react-native": ("ui-framework", "React Native mobile framework"),
    "vue": ("ui-framework", "Vue.js framework"),
    "svelte": ("ui-framework", "Svelte framework"),
    "angular": ("ui-framework", "Angular framework"),
    "@angular/core": ("ui-framework", "Angular core"),
    "next": ("ui-framework", "Next.js framework"),
    "nuxt": ("ui-framework", "Nuxt.js framework"),
    # Platform
    "expo": ("platform", "Expo development platform"),
    "electron": ("platform", "Electron desktop framework"),
    # State Management
    "zustand": ("state-management", "Lightweight state management"),
    "redux": ("state-management", "Redux state container"),
    "@reduxjs/toolkit": ("state-management", "Redux Toolkit"),
    "mobx": ("state-management", "MobX reactive state"),
    "recoil": ("state-management", "Recoil state management"),
    "jotai": ("state-management", "Jotai atomic state"),
    "immer": ("state-management", "Immutable state helper"),
    "pinia": ("state-management", "Pinia state for Vue"),
    # DI
    "tsyringe": ("dependency-injection", "TypeScript DI container"),
    "inversify": ("dependency-injection", "InversifyJS DI"),
    "reflect-metadata": ("dependency-injection", "Metadata reflection API"),
    # Database / ORM
    "drizzle-orm": ("database", "Drizzle TypeScript ORM"),
    "prisma": ("database", "Prisma ORM"),
    "@prisma/client": ("database", "Prisma client"),
    "typeorm": ("database", "TypeORM"),
    "sequelize": ("database", "Sequelize ORM"),
    "mongoose": ("database", "MongoDB ODM"),
    "knex": ("database", "SQL query builder"),
    "expo-sqlite": ("database", "SQLite for Expo"),
    "better-sqlite3": ("database", "SQLite for Node"),
    "pg": ("database", "PostgreSQL client"),
    "mysql2": ("database", "MySQL client"),
    "redis": ("database", "Redis client"),
    "ioredis": ("database", "Redis client"),
    # Validation
    "zod": ("validation", "Schema validation"),
    "yup": ("validation", "Schema validation"),
    "joi": ("validation", "Schema validation"),
    "class-validator": ("validation", "Class-based validation"),
    "ajv": ("validation", "JSON Schema validator"),
    # HTTP / API
    "axios": ("http", "HTTP client"),
    "node-fetch": ("http", "Fetch API for Node"),
    "express": ("http-server", "Express web framework"),
    "fastify": ("http-server", "Fastify web framework"),
    "koa": ("http-server", "Koa web framework"),
    "hono": ("http-server", "Hono web framework"),
    # Navigation / Routing
    "@react-navigation/native": ("navigation", "React Navigation"),
    "@react-navigation/native-stack": ("navigation", "Stack navigator"),
    "@react-navigation/bottom-tabs": ("navigation", "Tab navigator"),
    "react-router": ("navigation", "React Router"),
    "react-router-dom": ("navigation", "React Router DOM"),
    # i18n
    "i18next": ("i18n", "Internationalization framework"),
    "react-i18next": ("i18n", "React i18n bindings"),
    # TTS / Speech
    "expo-speech": ("tts", "Expo text-to-speech"),
    "react-native-tts": ("tts", "React Native TTS"),
    # Animation
    "lottie-react-native": ("animation", "Lottie animations"),
    "react-native-reanimated": ("animation", "React Native animations"),
    "framer-motion": ("animation", "Framer Motion"),
    # Storage
    "@react-native-async-storage/async-storage": ("storage", "Async storage"),
    "expo-file-system": ("storage", "File system access"),
    "expo-secure-store": ("storage", "Secure storage"),
    # Testing
    "jest": ("testing", "Jest test framework"),
    "@jest/core": ("testing", "Jest core"),
    "vitest": ("testing", "Vitest test framework"),
    "mocha": ("testing", "Mocha test framework"),
    "@testing-library/react": ("testing", "React Testing Library"),
    "@testing-library/react-native": ("testing", "React Native Testing Library"),
    "@playwright/test": ("testing", "Playwright E2E testing"),
    "cypress": ("testing", "Cypress E2E testing"),
    "supertest": ("testing", "HTTP assertion testing"),
    # Linting / Formatting
    "eslint": ("linting", "JavaScript/TypeScript linter"),
    "prettier": ("formatting", "Code formatter"),
    "biome": ("linting", "Biome linter/formatter"),
    # Build / Bundling
    "typescript": ("language", "TypeScript compiler"),
    "webpack": ("bundler", "Webpack bundler"),
    "vite": ("bundler", "Vite bundler"),
    "esbuild": ("bundler", "esbuild bundler"),
    "rollup": ("bundler", "Rollup bundler"),
    "babel": ("transpiler", "Babel transpiler"),
    "@babel/core": ("transpiler", "Babel core"),
    # Git / CI
    "husky": ("git-hooks", "Git hooks manager"),
    "lint-staged": ("git-hooks", "Lint staged files"),
    # Code Quality
    "knip": ("code-quality", "Unused code detector"),
    # SVG / Images
    "react-native-svg": ("ui-library", "SVG support for React Native"),
    "sharp": ("image-processing", "Image processing"),
    # Compression
    "jszip": ("compression", "ZIP file handling"),
    # Auth
    "jsonwebtoken": ("auth", "JWT handling"),
    "passport": ("auth", "Authentication middleware"),
    "bcrypt": ("auth", "Password hashing"),
    # Logging
    "winston": ("logging", "Winston logger"),
    "pino": ("logging", "Pino logger"),
    # Python packages
    "django": ("web-framework", "Django web framework"),
    "flask": ("web-framework", "Flask web framework"),
    "fastapi": ("web-framework", "FastAPI framework"),
    "sqlalchemy": ("database", "SQLAlchemy ORM"),
    "alembic": ("database", "Database migrations"),
    "pydantic": ("validation", "Pydantic data validation"),
    "pytest": ("testing", "Pytest framework"),
    "click": ("cli", "CLI framework"),
    "rich": ("cli", "Rich terminal output"),
    "celery": ("task-queue", "Distributed task queue"),
    "requests": ("http", "HTTP client"),
    "httpx": ("http", "Async HTTP client"),
}


def _infer_category(name: str) -> str:
    """Infer category from package name patterns."""
    lower = name.lower()
    if lower.startswith("@types/"):
        return "type-definitions"
    if "eslint" in lower or "lint" in lower:
        return "linting"
    if "prettier" in lower or "format" in lower:
        return "formatting"
    if "test" in lower or "jest" in lower or "mocha" in lower:
        return "testing"
    if "plugin" in lower:
        return "plugin"
    if "webpack" in lower or "babel" in lower or "rollup" in lower:
        return "build-tool"
    if lower.startswith("@react-navigation"):
        return "navigation"
    if lower.startswith("expo-"):
        return "expo-module"
    if lower.startswith("react-native-"):
        return "react-native-module"
    return "other"


class DependencyScanner(BaseScanner):
    """Scans dependency files and categorizes packages."""

    def scan(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "package_manager": "unknown",
            "dependency_files": [],
            "dependencies": [],
            "stack_summary": {},
        }

        # Try package.json (JS/TS)
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            self._scan_package_json(pkg_json, result)

        # Try pyproject.toml (Python)
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            self._scan_pyproject_toml(pyproject, result)

        # Try requirements.txt (Python)
        req_txt = self.root / "requirements.txt"
        if req_txt.exists():
            self._scan_requirements_txt(req_txt, result)

        # Build stack summary
        summary: dict[str, list[str]] = {}
        for dep in result["dependencies"]:
            cat = dep["category"]
            version_str = f"{dep['name']}@{dep['version']}" if dep["version"] else dep["name"]
            summary.setdefault(cat, []).append(version_str)
        result["stack_summary"] = summary

        return result

    def _scan_package_json(self, path: Path, result: dict[str, Any]) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                pkg = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        result["dependency_files"].append("package.json")

        # Detect package manager
        if (self.root / "pnpm-lock.yaml").exists():
            result["package_manager"] = "pnpm"
        elif (self.root / "yarn.lock").exists():
            result["package_manager"] = "yarn"
        elif (self.root / "bun.lockb").exists():
            result["package_manager"] = "bun"
        elif (self.root / "package-lock.json").exists():
            result["package_manager"] = "npm"

        for name, version in pkg.get("dependencies", {}).items():
            result["dependencies"].append(self._categorize(name, version, dev=False))

        for name, version in pkg.get("devDependencies", {}).items():
            result["dependencies"].append(self._categorize(name, version, dev=True))

    def _scan_pyproject_toml(self, path: Path, result: dict[str, Any]) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append("pyproject.toml")
        if result["package_manager"] == "unknown":
            if (self.root / "poetry.lock").exists():
                result["package_manager"] = "poetry"
            elif (self.root / "uv.lock").exists():
                result["package_manager"] = "uv"
            else:
                result["package_manager"] = "pip"

        # Simple TOML parsing for dependencies (avoid tomli dependency)
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "[project]":
                continue
            if stripped.startswith("["):
                in_deps = "dependencies" in stripped
                continue
            if in_deps and stripped and not stripped.startswith("#"):
                # Parse "package>=version" or "package"
                stripped = stripped.strip('"').strip("'").strip(",").strip('"').strip("'")
                if not stripped:
                    continue
                parts = stripped.split(">=")
                if len(parts) == 1:
                    parts = stripped.split("==")
                if len(parts) == 1:
                    parts = stripped.split("~=")
                name = parts[0].strip().strip('"').strip("'")
                version = parts[1].strip().strip('"').strip("'") if len(parts) > 1 else ""
                if name and not name.startswith("[") and not name.startswith("#"):
                    result["dependencies"].append(self._categorize(name, version, dev=False))

    def _scan_requirements_txt(self, path: Path, result: dict[str, Any]) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append("requirements.txt")
        if result["package_manager"] == "unknown":
            result["package_manager"] = "pip"

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            for sep in ["==", ">=", "~=", "<=", "!="]:
                if sep in line:
                    name, version = line.split(sep, 1)
                    result["dependencies"].append(
                        self._categorize(name.strip(), version.strip(), dev=False)
                    )
                    break
            else:
                result["dependencies"].append(self._categorize(line, "", dev=False))

    def _categorize(self, name: str, version: str, dev: bool) -> dict[str, Any]:
        """Categorize a dependency."""
        if name in KNOWN_PACKAGES:
            category, description = KNOWN_PACKAGES[name]
        else:
            category = _infer_category(name)
            description = ""

        return {
            "name": name,
            "version": version,
            "dev": dev,
            "category": category,
            "description": description,
        }
