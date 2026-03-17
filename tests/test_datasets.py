"""Tests for Phase 18 — PTB-XL dataset integration and PhysioNet utilities."""

from __future__ import annotations

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# PTBXL_LABELS
# ---------------------------------------------------------------------------

class TestPTBXLLabels:
    """Test that PTBXL_LABELS contains common SCP codes."""

    def test_has_common_codes(self):
        from datasets.ptbxl import PTBXL_LABELS

        required_codes = ["NORM", "MI", "STTC", "CD", "HYP", "AFIB", "LBBB", "RBBB", "LVH", "SR"]
        for code in required_codes:
            assert code in PTBXL_LABELS, f"Missing label for SCP code: {code}"

    def test_labels_are_portuguese(self):
        from datasets.ptbxl import PTBXL_LABELS

        assert PTBXL_LABELS["NORM"] == "ECG normal"
        assert PTBXL_LABELS["MI"] == "Infarto do miocárdio"
        assert PTBXL_LABELS["STTC"] == "Alteração ST-T"

    def test_labels_are_nonempty_strings(self):
        from datasets.ptbxl import PTBXL_LABELS

        for code, desc in PTBXL_LABELS.items():
            assert isinstance(code, str) and len(code) > 0
            assert isinstance(desc, str) and len(desc) > 0


# ---------------------------------------------------------------------------
# PhysioNet DATASETS dict
# ---------------------------------------------------------------------------

class TestDatasetsDict:
    """Test that DATASETS dict has required entries and structure."""

    def test_has_required_entries(self):
        from datasets.physionet import DATASETS

        required_keys = ["ptb-xl", "mit-bih", "ptb", "incart", "european-st-t"]
        for key in required_keys:
            assert key in DATASETS, f"Missing dataset: {key}"

    def test_entry_structure(self):
        from datasets.physionet import DATASETS

        required_fields = ["name", "physionet_name", "description", "records", "leads", "sampling_rates", "url", "reference"]
        for key, info in DATASETS.items():
            for field in required_fields:
                assert field in info, f"Dataset '{key}' missing field: {field}"

    def test_ptbxl_entry(self):
        from datasets.physionet import DATASETS

        ptbxl = DATASETS["ptb-xl"]
        assert ptbxl["records"] == 21799
        assert ptbxl["leads"] == 12
        assert 500 in ptbxl["sampling_rates"]

    def test_mitbih_entry(self):
        from datasets.physionet import DATASETS

        mitbih = DATASETS["mit-bih"]
        assert mitbih["records"] == 48
        assert mitbih["leads"] == 2


# ---------------------------------------------------------------------------
# list_available_datasets
# ---------------------------------------------------------------------------

class TestListAvailableDatasets:
    """Test list_available_datasets returns expected structure."""

    def test_returns_list(self):
        from datasets.physionet import list_available_datasets

        result = list_available_datasets()
        assert isinstance(result, list)
        assert len(result) >= 5

    def test_entries_have_required_keys(self):
        from datasets.physionet import list_available_datasets

        result = list_available_datasets()
        required_keys = {"key", "name", "description", "records", "leads", "sampling_rates", "url", "reference"}
        for entry in result:
            assert required_keys.issubset(entry.keys()), (
                f"Entry '{entry.get('key', '?')}' missing keys: {required_keys - entry.keys()}"
            )

    def test_ptbxl_in_list(self):
        from datasets.physionet import list_available_datasets

        result = list_available_datasets()
        keys = [e["key"] for e in result]
        assert "ptb-xl" in keys


# ---------------------------------------------------------------------------
# filter_by_diagnosis with mock data
# ---------------------------------------------------------------------------

class TestFilterByDiagnosis:
    """Test filter_by_diagnosis with synthetic metadata."""

    @pytest.fixture
    def mock_metadata(self) -> pd.DataFrame:
        """Create a mock PTB-XL metadata DataFrame."""
        data = {
            "ecg_id": [1, 2, 3, 4, 5],
            "scp_codes": [
                {"NORM": 100.0},
                {"MI": 80.0, "STTC": 50.0},
                {"NORM": 100.0},
                {"AFIB": 90.0},
                {"MI": 70.0, "LVH": 60.0},
            ],
            "age": [45, 67, 32, 78, 55],
            "sex": [0, 1, 0, 1, 0],
        }
        df = pd.DataFrame(data)
        df = df.set_index("ecg_id")
        return df

    def test_filter_norm(self, mock_metadata):
        from datasets.ptbxl import filter_by_diagnosis

        result = filter_by_diagnosis(mock_metadata, "NORM")
        assert len(result) == 2
        assert list(result.index) == [1, 3]

    def test_filter_mi(self, mock_metadata):
        from datasets.ptbxl import filter_by_diagnosis

        result = filter_by_diagnosis(mock_metadata, "MI")
        assert len(result) == 2
        assert list(result.index) == [2, 5]

    def test_filter_afib(self, mock_metadata):
        from datasets.ptbxl import filter_by_diagnosis

        result = filter_by_diagnosis(mock_metadata, "AFIB")
        assert len(result) == 1
        assert result.index[0] == 4

    def test_filter_nonexistent_code(self, mock_metadata):
        from datasets.ptbxl import filter_by_diagnosis

        result = filter_by_diagnosis(mock_metadata, "XXXXX")
        assert len(result) == 0

    def test_filter_preserves_columns(self, mock_metadata):
        from datasets.ptbxl import filter_by_diagnosis

        result = filter_by_diagnosis(mock_metadata, "MI")
        assert "scp_codes" in result.columns
        assert "age" in result.columns
        assert "sex" in result.columns
