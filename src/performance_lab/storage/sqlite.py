"""SQLite-backed local run evidence store with atomic immutable publication."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from performance_lab.domain import Run, RunStatus, SampleContentEvidence, load_json

_BUNDLE_VERSION = 1
_TERMINAL_STATUSES = {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED}


class RunStoreError(RuntimeError):
    pass


class RunNotFoundError(RunStoreError):
    pass


class ImmutableRunConflictError(RunStoreError):
    pass


class InvalidRunStateError(RunStoreError):
    pass


class InvalidRunBundleError(RunStoreError):
    pass


class SQLiteRunStore:
    """Keep mutable working state separate from immutable completed evidence.

    Potentially sensitive prompt/model-output content is stored in dedicated local tables and is
    deliberately excluded from canonical Run JSON and portable ``.plab.zip`` bundles.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS working_runs (
                    run_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS completed_runs (
                    run_id TEXT PRIMARY KEY,
                    fingerprint_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    published_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_completed_fingerprint
                    ON completed_runs(fingerprint_id);
                CREATE TABLE IF NOT EXISTS working_sample_content (
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    sample_id TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(run_id, task_id, sample_id, attempt)
                );
                CREATE TABLE IF NOT EXISTS completed_sample_content (
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    sample_id TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    PRIMARY KEY(run_id, task_id, sample_id, attempt),
                    FOREIGN KEY(run_id) REFERENCES completed_runs(run_id) ON DELETE CASCADE
                );
                """
            )

    def save_working(self, run: Run) -> None:
        if run.status in _TERMINAL_STATUSES:
            raise InvalidRunStateError(
                "terminal runs must be published, not saved as working state"
            )
        payload = run.canonical_json()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT 1 FROM completed_runs WHERE run_id = ?", (run.run_id,)
            ).fetchone()
            if existing is not None:
                raise ImmutableRunConflictError(f"run already published: {run.run_id}")
            connection.execute(
                """
                INSERT INTO working_runs(run_id, payload_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (run.run_id, payload, _now_iso()),
            )

    def save_working_sample_content(self, evidence: SampleContentEvidence) -> None:
        """Upsert sensitive content only while its owning run is still working."""

        with self._connect() as connection:
            completed = connection.execute(
                "SELECT 1 FROM completed_runs WHERE run_id = ?", (evidence.run_id,)
            ).fetchone()
            if completed is not None:
                raise ImmutableRunConflictError(f"run already published: {evidence.run_id}")
            working = connection.execute(
                "SELECT 1 FROM working_runs WHERE run_id = ?", (evidence.run_id,)
            ).fetchone()
            if working is None:
                raise InvalidRunStateError(
                    f"sample content requires an active working run: {evidence.run_id}"
                )
            connection.execute(
                """
                INSERT INTO working_sample_content(
                    run_id, task_id, sample_id, attempt, payload_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, task_id, sample_id, attempt) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    evidence.run_id,
                    evidence.task_id,
                    evidence.sample_id,
                    evidence.attempt,
                    evidence.model_dump_json(),
                    _now_iso(),
                ),
            )

    def publish(self, run: Run) -> None:
        if run.status not in _TERMINAL_STATUSES:
            raise InvalidRunStateError("only terminal runs can be published as immutable evidence")
        payload = run.canonical_json()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT payload_json FROM completed_runs WHERE run_id = ?", (run.run_id,)
            ).fetchone()
            if existing is not None:
                if existing[0] != payload:
                    raise ImmutableRunConflictError(
                        f"published run cannot be replaced: {run.run_id}"
                    )
                connection.rollback()
                return
            published_at = _now_iso()
            connection.execute(
                """
                INSERT INTO completed_runs(
                    run_id, fingerprint_id, status, payload_json, published_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.fingerprint.fingerprint_id,
                    run.status.value,
                    payload,
                    published_at,
                ),
            )
            connection.execute(
                """
                INSERT INTO completed_sample_content(
                    run_id, task_id, sample_id, attempt, payload_json, published_at
                )
                SELECT run_id, task_id, sample_id, attempt, payload_json, ?
                FROM working_sample_content
                WHERE run_id = ?
                """,
                (published_at, run.run_id),
            )
            connection.execute("DELETE FROM working_sample_content WHERE run_id = ?", (run.run_id,))
            connection.execute("DELETE FROM working_runs WHERE run_id = ?", (run.run_id,))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get(self, run_id: str) -> Run:
        completed = self.get_completed(run_id, required=False)
        if completed is not None:
            return completed
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM working_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            raise RunNotFoundError(run_id)
        return load_json(Run, str(row[0]))

    def get_completed(self, run_id: str, *, required: bool = True) -> Run | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM completed_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            if required:
                raise RunNotFoundError(run_id)
            return None
        return load_json(Run, str(row[0]))

    def get_sample_content(
        self,
        run_id: str,
        task_id: str,
        sample_id: str,
        attempt: int,
    ) -> SampleContentEvidence | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM completed_sample_content
                WHERE run_id = ? AND task_id = ? AND sample_id = ? AND attempt = ?
                """,
                (run_id, task_id, sample_id, attempt),
            ).fetchone()
        if row is None:
            return None
        return SampleContentEvidence.model_validate_json(str(row[0]))

    def list_completed(self) -> tuple[Run, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM completed_runs ORDER BY published_at, run_id"
            ).fetchall()
        return tuple(load_json(Run, str(row[0])) for row in rows)

    def list_working(self) -> tuple[Run, ...]:
        """Return retained non-terminal state for restart/recovery surfaces."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM working_runs ORDER BY updated_at, run_id"
            ).fetchall()
        return tuple(load_json(Run, str(row[0])) for row in rows)

    def delete_working(self, run_id: str) -> bool:
        with self._connect() as connection:
            connection.execute("DELETE FROM working_sample_content WHERE run_id = ?", (run_id,))
            cursor = connection.execute("DELETE FROM working_runs WHERE run_id = ?", (run_id,))
            return cursor.rowcount > 0

    def delete_working_sample_content(self, run_id: str) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM working_sample_content WHERE run_id = ?", (run_id,)
            )
            return cursor.rowcount

    def delete_completed_sample_content(self, run_id: str) -> int:
        """Delete only sensitive local content while preserving canonical completed Run evidence."""

        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM completed_sample_content WHERE run_id = ?", (run_id,)
            )
            return cursor.rowcount

    def export_bundle(self, run_id: str, destination: Path) -> Path:
        run = self.get_completed(run_id)
        assert run is not None
        run_json = run.canonical_json()
        manifest = {
            "bundle_version": _BUNDLE_VERSION,
            "run_schema_version": run.schema_version,
            "run_id": run.run_id,
            "run_sha256": sha256(run_json.encode("utf-8")).hexdigest(),
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, sort_keys=True))
            archive.writestr("run.json", run_json)
        return destination

    def import_bundle(self, source: Path) -> Run:
        try:
            with ZipFile(source, "r") as archive:
                names = set(archive.namelist())
                if names != {"manifest.json", "run.json"}:
                    raise InvalidRunBundleError(
                        "bundle must contain only manifest.json and run.json"
                    )
                manifest_raw: object = json.loads(archive.read("manifest.json"))
                run_json = archive.read("run.json").decode("utf-8")
        except (OSError, BadZipFile, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidRunBundleError("invalid run bundle") from exc
        if not isinstance(manifest_raw, dict):
            raise InvalidRunBundleError("bundle manifest is not an object")
        if manifest_raw.get("bundle_version") != _BUNDLE_VERSION:
            raise InvalidRunBundleError("unsupported bundle version")
        expected_digest = manifest_raw.get("run_sha256")
        actual_digest = sha256(run_json.encode("utf-8")).hexdigest()
        if expected_digest != actual_digest:
            raise InvalidRunBundleError("run payload digest does not match manifest")
        run = load_json(Run, run_json)
        if manifest_raw.get("run_id") != run.run_id:
            raise InvalidRunBundleError("manifest run_id does not match payload")
        self.publish(run)
        return run


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
