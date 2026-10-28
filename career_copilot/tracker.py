"""CSV trackers with dedupe, timestamped backups and status updates."""
from __future__ import annotations
import csv
import os
import shutil
from datetime import date

JOB_FIELDS = ["date_discovered", "company", "title", "url", "score", "decision", "status", "next_action"]
NETWORK_FIELDS = ["date", "contact_role", "kind", "draft", "status"]  # kind: comment | connection_note
VALID_STATUSES = {"drafted", "approved", "sent-by-human", "skipped", "applied", "closed", "awaiting-human"}


class CsvTracker:
    def __init__(self, path: str, fields: list[str], key: str):
        self.path, self.fields, self.key = path, fields, key

    def read(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def _write(self, rows: list[dict]) -> None:
        if os.path.exists(self.path):
            shutil.copy(self.path, f"{self.path}.bak-{date.today().isoformat()}")
        with open(self.path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=self.fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    def upsert(self, new_rows: list[dict]) -> int:
        """Add rows whose key is new. Returns number added."""
        rows = self.read()
        seen = {r[self.key] for r in rows}
        added = [r for r in new_rows if r[self.key] not in seen]
        if added:
            self._write(rows + added)
        return len(added)

    def set_status(self, key_value: str, status: str) -> bool:
        if status not in VALID_STATUSES:
            raise ValueError(f"unknown status: {status}")
        rows = self.read()
        hit = False
        for r in rows:
            if r[self.key] == key_value:
                r["status"], hit = status, True
        if hit:
            self._write(rows)
        return hit
