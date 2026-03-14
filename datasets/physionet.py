"""Generic PhysioNet dataset utilities for ECGiga.

Provides a catalogue of supported ECG datasets and a unified download
interface built on top of ``wfdb.dl_database()``.
"""

from __future__ import annotations

import pathlib
from typing import Optional


# ---------------------------------------------------------------------------
# Supported datasets catalogue
# ---------------------------------------------------------------------------

DATASETS: dict[str, dict] = {
    "ptb-xl": {
        "name": "PTB-XL",
        "physionet_name": "ptb-xl/1.0.3",
        "description": (
            "PTB-XL — maior dataset público de ECG 12-derivações com 21.799 registros "
            "de 18.869 pacientes, anotado por até dois cardiologistas."
        ),
        "records": 21799,
        "leads": 12,
        "sampling_rates": [100, 500],
        "url": "https://physionet.org/content/ptb-xl/1.0.3/",
        "reference": "Wagner et al., 2020",
    },
    "mit-bih": {
        "name": "MIT-BIH Arrhythmia Database",
        "physionet_name": "mitdb/1.0.0",
        "description": (
            "MIT-BIH Arrhythmia Database — 48 registros de ECG ambulatorial de "
            "2 derivações, referência clássica para detecção de arritmias."
        ),
        "records": 48,
        "leads": 2,
        "sampling_rates": [360],
        "url": "https://physionet.org/content/mitdb/1.0.0/",
        "reference": "Moody & Mark, 2001",
    },
    "ptb": {
        "name": "PTB Diagnostic ECG Database",
        "physionet_name": "ptbdb/1.0.0",
        "description": (
            "PTB Diagnostic ECG Database — 549 registros de 290 pacientes, "
            "15 derivações (12 padrão + 3 Frank), diversas patologias."
        ),
        "records": 549,
        "leads": 15,
        "sampling_rates": [1000],
        "url": "https://physionet.org/content/ptbdb/1.0.0/",
        "reference": "Bousseljot et al., 1995",
    },
    "incart": {
        "name": "St Petersburg INCART 12-lead Arrhythmia Database",
        "physionet_name": "incartdb/1.0.0",
        "description": (
            "INCART — 75 registros de ECG 12-derivações anotados com arritmias, "
            "gravados durante exames de rotina no Instituto de Cardiologia."
        ),
        "records": 75,
        "leads": 12,
        "sampling_rates": [257],
        "url": "https://physionet.org/content/incartdb/1.0.0/",
        "reference": "Tihonenko et al., 2008",
    },
    "european-st-t": {
        "name": "European ST-T Database",
        "physionet_name": "edb/1.0.0",
        "description": (
            "European ST-T Database — 90 registros de ECG ambulatorial de 2 horas, "
            "anotados com episódios de alteração ST e T."
        ),
        "records": 90,
        "leads": 2,
        "sampling_rates": [250],
        "url": "https://physionet.org/content/edb/1.0.0/",
        "reference": "Taddei et al., 1992",
    },
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def list_available_datasets() -> list[dict]:
    """Return a list of all supported PhysioNet ECG datasets.

    Returns
    -------
    list[dict]
        Each dict contains ``name``, ``description``, ``records``, ``leads``,
        ``sampling_rates``, ``url``, and ``reference``.
    """
    result = []
    for key, info in DATASETS.items():
        result.append({
            "key": key,
            "name": info["name"],
            "description": info["description"],
            "records": info["records"],
            "leads": info["leads"],
            "sampling_rates": info["sampling_rates"],
            "url": info["url"],
            "reference": info["reference"],
        })
    return result


def download_dataset(
    name: str,
    dest_dir: Optional[str] = None,
) -> pathlib.Path:
    """Download a PhysioNet dataset by its short key.

    Parameters
    ----------
    name : str
        Dataset key as listed in :data:`DATASETS`
        (e.g. ``"ptb-xl"``, ``"mit-bih"``).
    dest_dir : str, optional
        Destination directory. Defaults to ``datasets/<name>``.

    Returns
    -------
    pathlib.Path
        Path to the downloaded dataset.

    Raises
    ------
    ValueError
        If the dataset name is not recognised.
    """
    import wfdb

    if name not in DATASETS:
        available = ", ".join(sorted(DATASETS.keys()))
        raise ValueError(
            f"Dataset '{name}' não reconhecido. Disponíveis: {available}"
        )

    info = DATASETS[name]

    if dest_dir is None:
        dest_dir = f"datasets/{name}"

    dest = pathlib.Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    wfdb.dl_database(info["physionet_name"], dl_dir=str(dest))

    return dest
