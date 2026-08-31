"""SQLite persistence for bounded Campaign lifecycle state."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from performance_lab.domain import TERMINAL_CAMPAIGN_STATUSES, Campaign, load_json


class CampaignStoreError(RuntimeError):
    pass


class CampaignNotFoundError(CampaignStoreError):
    pass


class ImmutableCampaignConflictError(CampaignStoreError):
    pass


class SQLiteCampaignStore:
    """Persist mutable campaign progress and freeze terminal campaign snapshots."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS campaigns (
                    campaign_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_campaign_status
                    ON campaigns(status, updated_at);
                """
            )

    def save(self, campaign: Campaign) -> None:
        payload = campaign.canonical_json()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT status, payload_json FROM campaigns WHERE campaign_id = ?",
                (campaign.campaign_id,),
            ).fetchone()
            if existing is not None and existing[0] in {
                status.value for status in TERMINAL_CAMPAIGN_STATUSES
            }:
                if existing[1] != payload:
                    raise ImmutableCampaignConflictError(
                        f"terminal campaign cannot be replaced: {campaign.campaign_id}"
                    )
                connection.rollback()
                return
            connection.execute(
                """
                INSERT INTO campaigns(campaign_id, status, payload_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(campaign_id) DO UPDATE SET
                    status = excluded.status,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    campaign.campaign_id,
                    campaign.status.value,
                    payload,
                    campaign.updated_at.isoformat(),
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get(self, campaign_id: str) -> Campaign:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM campaigns WHERE campaign_id = ?",
                (campaign_id,),
            ).fetchone()
        if row is None:
            raise CampaignNotFoundError(campaign_id)
        return load_json(Campaign, str(row[0]))

    def list_all(self) -> tuple[Campaign, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM campaigns ORDER BY updated_at, campaign_id"
            ).fetchall()
        return tuple(load_json(Campaign, str(row[0])) for row in rows)

    def list_active(self) -> tuple[Campaign, ...]:
        terminal = tuple(status.value for status in TERMINAL_CAMPAIGN_STATUSES)
        placeholders = ",".join("?" for _ in terminal)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT payload_json FROM campaigns WHERE status NOT IN ({placeholders}) "
                "ORDER BY updated_at, campaign_id",
                terminal,
            ).fetchall()
        return tuple(load_json(Campaign, str(row[0])) for row in rows)
