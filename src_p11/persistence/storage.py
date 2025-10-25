"""
JSON-based persistence layer for ECG reports.

Provides simple storage with directory structure:
- storage/reports/YYYY-MM/ for reports
- index/reports.idx.json for lightweight metadata
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class ReportMetadata:
    """Lightweight report metadata for indexing."""

    id: str
    created_at: str
    capabilities: List[str]
    fc_bpm: Optional[float] = None


class Storage:
    """JSON-based storage manager."""

    def __init__(self, storage_root: Path):
        self.storage_root = Path(storage_root)
        self.reports_dir = self.storage_root / "reports"
        self.index_dir = self.storage_root / "index"
        self.index_file = self.index_dir / "reports.idx.json"

        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Initialize index if it doesn't exist
        if not self.index_file.exists():
            self._write_index({"reports": []})

    def _generate_report_id(self) -> str:
        """Generate unique report ID."""
        return uuid.uuid4().hex

    def _get_month_dir(self, timestamp: Optional[str] = None) -> Path:
        """Get directory for storing reports by month."""
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            dt = datetime.now()

        month_dir = self.reports_dir / f"{dt.year:04d}-{dt.month:02d}"
        month_dir.mkdir(parents=True, exist_ok=True)
        return month_dir

    def _read_index(self) -> Dict:
        """Read the reports index."""
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"reports": []}

    def _write_index(self, index_data: Dict) -> None:
        """Write the reports index.

        Note: This implementation assumes single-writer access for simplicity.
        In production, proper file locking would be needed for concurrent access.
        """
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    def save_report(self, report_obj: Dict) -> str:
        """Save report and return report_id.

        Args:
            report_obj: Complete report object with all processing results

        Returns:
            report_id: Unique identifier for the saved report
        """
        report_id = self._generate_report_id()

        # Add report_id to report object
        report_obj = report_obj.copy()
        report_obj["report_id"] = report_id

        # Ensure created_at timestamp
        if "meta" not in report_obj:
            report_obj["meta"] = {}
        if "created_at" not in report_obj["meta"]:
            report_obj["meta"]["created_at"] = datetime.now().isoformat()

        created_at = report_obj["meta"]["created_at"]

        # Save report to monthly directory
        month_dir = self._get_month_dir(created_at)
        report_file = month_dir / f"{report_id}.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_obj, f, ensure_ascii=False, indent=2)

        # Update index
        self._update_index(report_id, report_obj)

        return report_id

    def _update_index(self, report_id: str, report_obj: Dict) -> None:
        """Update the reports index with new report metadata."""
        index_data = self._read_index()

        # Extract metadata from report
        meta = report_obj.get("meta", {})
        measures = report_obj.get("measures", {})
        capabilities = []

        # Determine capabilities based on report content
        if report_obj.get("segmentation"):
            capabilities.append("segmentation")
        if report_obj.get("rpeaks"):
            capabilities.append("rpeaks")
        if report_obj.get("intervals"):
            capabilities.append("intervals")
        if report_obj.get("axis"):
            capabilities.append("axis")

        metadata = {
            "id": report_id,
            "created_at": meta.get("created_at", datetime.now().isoformat()),
            "capabilities": capabilities,
            "fc_bpm": measures.get("fc_bpm"),
        }

        # Add to index (newest first)
        index_data["reports"].insert(0, metadata)

        # Write updated index
        self._write_index(index_data)

    def get_report(self, report_id: str) -> Optional[Dict]:
        """Retrieve a report by ID.

        Args:
            report_id: Unique report identifier

        Returns:
            Report object or None if not found
        """
        # Find report in index to get creation date for directory lookup
        index_data = self._read_index()
        report_metadata = None

        for meta in index_data["reports"]:
            if meta["id"] == report_id:
                report_metadata = meta
                break

        if not report_metadata:
            return None

        # Get the appropriate month directory
        month_dir = self._get_month_dir(report_metadata["created_at"])
        report_file = month_dir / f"{report_id}.json"

        try:
            with open(report_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def list_reports(self, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
        """List reports with pagination.

        Args:
            limit: Maximum number of reports to return
            offset: Number of reports to skip

        Returns:
            Tuple of (report_metadata_list, total_count)
        """
        index_data = self._read_index()
        all_reports = index_data["reports"]

        total_count = len(all_reports)

        # Apply pagination
        paginated_reports = all_reports[offset : offset + limit]

        return paginated_reports, total_count


# Global storage instance
_storage: Optional[Storage] = None


def get_storage(storage_root: Path) -> Storage:
    """Get or create global storage instance."""
    global _storage
    if _storage is None or _storage.storage_root != storage_root:
        _storage = Storage(storage_root)
    return _storage
