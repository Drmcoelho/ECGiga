"""PTB-XL dataset integration for ECGiga.

Provides download, metadata loading, record browsing, and rendering
utilities for the PTB-XL 12-lead ECG dataset from PhysioNet.
"""

from __future__ import annotations

import ast
import pathlib
from typing import Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# SCP code -> Portuguese descriptions
# ---------------------------------------------------------------------------

PTBXL_LABELS: dict[str, str] = {
    # Normal
    "NORM": "ECG normal",
    # Myocardial infarction
    "MI": "Infarto do miocárdio",
    "IMI": "Infarto inferior do miocárdio",
    "AMI": "Infarto anterior do miocárdio",
    "ALMI": "Infarto anterolateral do miocárdio",
    "ILMI": "Infarto inferolateral do miocárdio",
    "PMI": "Infarto posterior do miocárdio",
    "LMI": "Infarto lateral do miocárdio",
    # ST-T changes
    "STTC": "Alteração ST-T",
    "STD_": "Infradesnivelamento de ST",
    "STE_": "Supradesnivelamento de ST",
    "NST_": "Alteração inespecífica de ST",
    "ISC_": "Isquemia",
    "ISCA": "Isquemia anterior",
    "ISCI": "Isquemia inferior",
    # Conduction disturbances
    "CD": "Distúrbio de condução",
    "LBBB": "Bloqueio de ramo esquerdo",
    "RBBB": "Bloqueio de ramo direito",
    "LAFB": "Bloqueio fascicular anterior esquerdo",
    "LPFB": "Bloqueio fascicular posterior esquerdo",
    "IRBBB": "Bloqueio incompleto de ramo direito",
    "1AVB": "Bloqueio atrioventricular de 1º grau",
    "2AVB": "Bloqueio atrioventricular de 2º grau",
    "3AVB": "Bloqueio atrioventricular de 3º grau (total)",
    "WPW": "Síndrome de Wolff-Parkinson-White",
    "CLBBB": "Bloqueio completo de ramo esquerdo",
    "CRBBB": "Bloqueio completo de ramo direito",
    # Hypertrophy
    "HYP": "Hipertrofia",
    "LVH": "Hipertrofia ventricular esquerda",
    "RVH": "Hipertrofia ventricular direita",
    "LAO/LAE": "Sobrecarga atrial esquerda",
    "RAO/RAE": "Sobrecarga atrial direita",
    # Rhythm
    "SR": "Ritmo sinusal",
    "AFIB": "Fibrilação atrial",
    "AFLT": "Flutter atrial",
    "SVTAC": "Taquicardia supraventricular",
    "PSVT": "Taquicardia supraventricular paroxística",
    "STACH": "Taquicardia sinusal",
    "SBRAD": "Bradicardia sinusal",
    "SARRH": "Arritmia sinusal",
    "PAC": "Contração atrial prematura",
    "PVC": "Contração ventricular prematura",
    "BIGU": "Bigeminismo",
    "TRIGU": "Trigeminismo",
}

# Lead names in standard 12-lead order
LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_ptbxl(
    dest_dir: str = "datasets/ptb-xl",
    version: str = "1.0.3",
) -> pathlib.Path:
    """Download PTB-XL dataset from PhysioNet using wfdb.

    Parameters
    ----------
    dest_dir : str
        Local directory where the dataset will be stored.
    version : str
        Dataset version on PhysioNet (default ``1.0.3``).

    Returns
    -------
    pathlib.Path
        Path to the downloaded dataset root.
    """
    import wfdb

    dest = pathlib.Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    db_name = f"ptb-xl/{version}"
    wfdb.dl_database(db_name, dl_dir=str(dest))

    return dest


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def load_ptbxl_metadata(base_dir: str = "datasets/ptb-xl") -> pd.DataFrame:
    """Load and parse the PTB-XL metadata CSV.

    Parameters
    ----------
    base_dir : str
        Root directory of the downloaded PTB-XL dataset.

    Returns
    -------
    pd.DataFrame
        Metadata with ``scp_codes`` parsed from string to dict.

    Raises
    ------
    FileNotFoundError
        If the metadata CSV is not found at expected location.
    """
    base = pathlib.Path(base_dir)

    # The CSV may be directly in base_dir or under a version subfolder
    candidates = [
        base / "ptbxl_database.csv",
        base / "ptb-xl" / "ptbxl_database.csv",
    ]
    # Also check version sub-directories
    for child in sorted(base.iterdir()) if base.exists() else []:
        if child.is_dir():
            candidates.append(child / "ptbxl_database.csv")

    csv_path: Optional[pathlib.Path] = None
    for c in candidates:
        if c.exists():
            csv_path = c
            break

    if csv_path is None:
        raise FileNotFoundError(
            f"ptbxl_database.csv não encontrado em {base}. "
            "Execute download_ptbxl() primeiro."
        )

    df = pd.read_csv(csv_path, index_col="ecg_id")
    # Parse the scp_codes column from string representation of dict
    df["scp_codes"] = df["scp_codes"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )
    return df


# ---------------------------------------------------------------------------
# Single record loading
# ---------------------------------------------------------------------------

def load_record(base_dir: str, record_id: str | int) -> dict:
    """Load a single WFDB record from the PTB-XL dataset.

    Parameters
    ----------
    base_dir : str
        Root directory of the downloaded PTB-XL dataset.
    record_id : str or int
        The record identifier (e.g. ``1`` or ``"00001"``).

    Returns
    -------
    dict
        ``{"signal": np.ndarray, "header": dict, "labels": list}``
    """
    import wfdb

    base = pathlib.Path(base_dir)

    # PTB-XL stores records under records100/ or records500/
    # Format record_id as 5-digit string
    if isinstance(record_id, int):
        rid = f"{record_id:05d}"
    else:
        rid = str(record_id).zfill(5)

    # Determine the subfolder: records are grouped in folders of 1000
    folder_num = (int(rid) - 1) // 1000 + 1
    folder = f"{folder_num:02d}000"

    # Try records100 first (lower resolution, faster), then records500
    for res_dir in ["records100", "records500"]:
        candidates = [
            base / res_dir / folder / f"{rid}_hr",
            base / res_dir / folder / f"{rid}_lr",
            base / res_dir / folder / rid,
        ]
        # Also search version sub-directories
        for child in sorted(base.iterdir()) if base.exists() else []:
            if child.is_dir():
                for suffix in [f"{rid}_hr", f"{rid}_lr", rid]:
                    candidates.append(child / res_dir / folder / suffix)

        for rec_path in candidates:
            hea_file = rec_path.with_suffix(".hea")
            if hea_file.exists():
                record = wfdb.rdrecord(str(rec_path))
                # Try to load labels from metadata
                labels = _get_labels_for_record(base, int(rid))
                header_dict = {
                    "record_name": record.record_name,
                    "n_sig": record.n_sig,
                    "fs": record.fs,
                    "sig_len": record.sig_len,
                    "sig_name": record.sig_name,
                    "units": record.units,
                }
                return {
                    "signal": record.p_signal,
                    "header": header_dict,
                    "labels": labels,
                }

    raise FileNotFoundError(
        f"Registro {rid} não encontrado em {base}. "
        "Verifique se o dataset foi baixado corretamente."
    )


def _get_labels_for_record(base_dir: pathlib.Path, ecg_id: int) -> list[str]:
    """Attempt to extract SCP labels for a given record ID."""
    try:
        df = load_ptbxl_metadata(str(base_dir))
        if ecg_id in df.index:
            codes = df.loc[ecg_id, "scp_codes"]
            if isinstance(codes, dict):
                return list(codes.keys())
    except (FileNotFoundError, Exception):
        pass
    return []


# ---------------------------------------------------------------------------
# Filtering & sampling
# ---------------------------------------------------------------------------

def filter_by_diagnosis(
    metadata_df: pd.DataFrame,
    diagnosis_code: str,
) -> pd.DataFrame:
    """Filter PTB-XL metadata records by a specific SCP diagnosis code.

    Parameters
    ----------
    metadata_df : pd.DataFrame
        Metadata DataFrame as returned by :func:`load_ptbxl_metadata`.
    diagnosis_code : str
        SCP code to filter by (e.g. ``"MI"``, ``"NORM"``).

    Returns
    -------
    pd.DataFrame
        Filtered subset of records containing the given diagnosis code.
    """
    mask = metadata_df["scp_codes"].apply(
        lambda codes: diagnosis_code in codes if isinstance(codes, dict) else False
    )
    return metadata_df[mask]


def get_sample_records(
    base_dir: str,
    n: int = 5,
    diagnosis: Optional[str] = None,
) -> list[dict]:
    """Get a sample of records, optionally filtered by diagnosis.

    Parameters
    ----------
    base_dir : str
        Root directory of the downloaded PTB-XL dataset.
    n : int
        Number of sample records to return.
    diagnosis : str, optional
        SCP code to filter by before sampling.

    Returns
    -------
    list[dict]
        List of record dicts as returned by :func:`load_record`.
    """
    df = load_ptbxl_metadata(base_dir)

    if diagnosis is not None:
        df = filter_by_diagnosis(df, diagnosis)

    if len(df) == 0:
        return []

    sample_ids = df.sample(n=min(n, len(df)), random_state=42).index.tolist()
    records = []
    for ecg_id in sample_ids:
        try:
            rec = load_record(base_dir, ecg_id)
            rec["ecg_id"] = ecg_id
            records.append(rec)
        except FileNotFoundError:
            continue

    return records


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def record_to_image(
    record: dict,
    lead: str = "II",
    figsize: tuple[int, int] = (12, 3),
):
    """Render a single lead from a WFDB record as a PIL Image.

    Parameters
    ----------
    record : dict
        Record dict as returned by :func:`load_record`.
    lead : str
        Lead name to render (default ``"II"``).
    figsize : tuple
        Matplotlib figure size.

    Returns
    -------
    PIL.Image.Image
        Rendered ECG strip as an image.
    """
    import io

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image

    sig_names = record["header"].get("sig_name", LEAD_NAMES)
    if lead not in sig_names:
        raise ValueError(
            f"Derivação '{lead}' não encontrada. Disponíveis: {sig_names}"
        )

    lead_idx = sig_names.index(lead)
    signal = record["signal"][:, lead_idx]
    fs = record["header"].get("fs", 500)
    t = np.arange(len(signal)) / fs

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.plot(t, signal, color="black", linewidth=0.8)
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("Amplitude (mV)")
    ax.set_title(f"Derivação {lead}")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)


# ---------------------------------------------------------------------------
# Paginated browser
# ---------------------------------------------------------------------------

def browse_records(
    base_dir: str,
    diagnosis: Optional[str] = None,
    page: int = 0,
    page_size: int = 10,
) -> dict:
    """Paginated browser for PTB-XL records.

    Parameters
    ----------
    base_dir : str
        Root directory of the downloaded PTB-XL dataset.
    diagnosis : str, optional
        SCP code to filter by.
    page : int
        Zero-indexed page number.
    page_size : int
        Records per page.

    Returns
    -------
    dict
        ``{"records": list[dict], "total": int, "page": int,
        "page_size": int, "total_pages": int}``
    """
    df = load_ptbxl_metadata(base_dir)

    if diagnosis is not None:
        df = filter_by_diagnosis(df, diagnosis)

    total = len(df)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))

    start = page * page_size
    end = min(start + page_size, total)
    page_df = df.iloc[start:end]

    records = []
    for ecg_id, row in page_df.iterrows():
        labels = (
            list(row["scp_codes"].keys())
            if isinstance(row.get("scp_codes"), dict)
            else []
        )
        label_descs = [
            PTBXL_LABELS.get(code, code) for code in labels
        ]
        records.append({
            "ecg_id": ecg_id,
            "labels": labels,
            "label_descriptions": label_descs,
            "patient_age": row.get("age", None),
            "sex": row.get("sex", None),
        })

    return {
        "records": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
