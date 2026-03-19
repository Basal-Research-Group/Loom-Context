"""Scan cache: tracks file hashes to skip unchanged scans."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional


class ScanCache:
    """Tracks file hashes to detect changes between scans."""

    def __init__(self, loom_dir: Path) -> None:
        self.cache_dir = loom_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hashes_path = self.cache_dir / "hashes.json"

    def compute_project_hash(self, files: list[Path]) -> str:
        """Compute a combined hash of all project files (by path + mtime + size).

        Also includes .context/loom.json so that config changes invalidate the cache.
        """
        hasher = hashlib.md5()  # noqa: S324 — not for security, just change detection

        # Include loom.json in hash so config changes trigger re-scan
        context_dir = self.cache_dir.parent.parent / ".context"
        loom_json = context_dir / "loom.json"
        if loom_json.exists():
            try:
                stat = loom_json.stat()
                hasher.update(f"{loom_json}:{stat.st_size}:{stat.st_mtime_ns}".encode())
            except OSError:
                pass

        for f in sorted(files):
            try:
                stat = f.stat()
                hasher.update(f"{f}:{stat.st_size}:{stat.st_mtime_ns}".encode())
            except OSError:
                continue
        return hasher.hexdigest()

    def is_fresh(self, current_hash: str) -> bool:
        """Check if the project hash matches the cached hash."""
        cached = self._read_cache()
        return cached.get("project_hash") == current_hash

    def save(self, project_hash: str, scan_result_dict: dict[str, Any]) -> None:
        """Save the current hash and scan result to cache."""
        cache_data = {
            "project_hash": project_hash,
            "scan_result": scan_result_dict,
        }
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with open(self.hashes_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False)

    def load_scan_result(self) -> Optional[dict[str, Any]]:
        """Load cached scan result if available."""
        cached = self._read_cache()
        return cached.get("scan_result")

    def invalidate(self) -> None:
        """Clear the cache."""
        if self.hashes_path.exists():
            self.hashes_path.unlink()

    def _read_cache(self) -> dict[str, Any]:
        """Read cache file."""
        if not self.hashes_path.exists():
            return {}
        try:
            with open(self.hashes_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError):
            return {}
