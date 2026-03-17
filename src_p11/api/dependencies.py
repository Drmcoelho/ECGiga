"""
Dependências e gerenciamento de configuração da API.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Configurações da aplicação via variáveis de ambiente."""

    # Configuração de armazenamento
    ecg_storage_root: str = "storage/"

    # Limites de upload de arquivo
    max_file_mb: int = 8

    # Formatos de imagem suportados
    supported_formats: list = ["image/png", "image/jpeg", "image/jpg"]

    model_config = {"env_file": ".env"}

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Retorna singleton de configurações da aplicação."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def get_storage_root() -> Path:
    """Retorna o diretório raiz de armazenamento como objeto Path."""
    settings = get_settings()
    storage_path = Path(settings.ecg_storage_root)
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path

def validate_file_size(content_length: int) -> bool:
    """Valida tamanho do arquivo contra o máximo configurado."""
    settings = get_settings()
    max_bytes = settings.max_file_mb * 1024 * 1024
    return content_length <= max_bytes

def validate_content_type(content_type: str) -> bool:
    """Valida tipo de conteúdo do arquivo contra formatos suportados."""
    settings = get_settings()
    return content_type.lower() in [fmt.lower() for fmt in settings.supported_formats]