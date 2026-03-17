"""
mega.config — Gestão de configuração do projeto MEGA.

Lê e grava o ficheiro de configuração YAML do projecto (mega.yaml),
que define módulos, metadados e opções de publicação.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any

import yaml


DEFAULT_CONFIG_NAME = "mega.yaml"

# Estrutura padrão para um novo projecto MEGA
DEFAULT_CONFIG: dict[str, Any] = {
    "projeto": {
        "nome": "Curso ECG — Megaprojeto",
        "versao": "0.1.0",
        "idioma": "pt-BR",
        "descricao": (
            "Curso interativo de eletrocardiografia para profissionais de saúde. "
            "AVISO: conteúdo exclusivamente educacional — não substitui avaliação clínica."
        ),
    },
    "conteudo": {
        "diretorio_modulos": "content/modules",
        "formatos_aula": [".md"],
        "formatos_quiz": [".json"],
    },
    "publicacao": {
        "destino": "github-pages",
        "diretorio_saida": "_site",
        "base_url": "/",
    },
}


@dataclass
class MegaConfig:
    """Representação em memória da configuração do projecto."""

    projeto_nome: str = "Curso ECG — Megaprojeto"
    projeto_versao: str = "0.1.0"
    projeto_idioma: str = "pt-BR"
    projeto_descricao: str = ""

    diretorio_modulos: str = "content/modules"
    formatos_aula: list[str] = field(default_factory=lambda: [".md"])
    formatos_quiz: list[str] = field(default_factory=lambda: [".json"])

    destino_publicacao: str = "github-pages"
    diretorio_saida: str = "_site"
    base_url: str = "/"

    _path: pathlib.Path | None = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Serialização
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Converte a configuração para dicionário compatível com YAML."""
        return {
            "projeto": {
                "nome": self.projeto_nome,
                "versao": self.projeto_versao,
                "idioma": self.projeto_idioma,
                "descricao": self.projeto_descricao,
            },
            "conteudo": {
                "diretorio_modulos": self.diretorio_modulos,
                "formatos_aula": self.formatos_aula,
                "formatos_quiz": self.formatos_quiz,
            },
            "publicacao": {
                "destino": self.destino_publicacao,
                "diretorio_saida": self.diretorio_saida,
                "base_url": self.base_url,
            },
        }

    def save(self, path: pathlib.Path | None = None) -> pathlib.Path:
        """Grava a configuração em ficheiro YAML."""
        target = path or self._path
        if target is None:
            raise ValueError("Nenhum caminho de destino definido para salvar a configuração.")
        target = pathlib.Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            yaml.dump(
                self.to_dict(),
                fh,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        self._path = target
        return target

    # ------------------------------------------------------------------
    # Carregamento
    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict[str, Any], path: pathlib.Path | None = None) -> MegaConfig:
        """Cria MegaConfig a partir de dicionário (tipicamente vindo do YAML)."""
        proj = data.get("projeto", {})
        cont = data.get("conteudo", {})
        pub = data.get("publicacao", {})
        return cls(
            projeto_nome=proj.get("nome", cls.projeto_nome),
            projeto_versao=proj.get("versao", cls.projeto_versao),
            projeto_idioma=proj.get("idioma", cls.projeto_idioma),
            projeto_descricao=proj.get("descricao", ""),
            diretorio_modulos=cont.get("diretorio_modulos", cls.diretorio_modulos),
            formatos_aula=cont.get("formatos_aula", [".md"]),
            formatos_quiz=cont.get("formatos_quiz", [".json"]),
            destino_publicacao=pub.get("destino", cls.destino_publicacao),
            diretorio_saida=pub.get("diretorio_saida", cls.diretorio_saida),
            base_url=pub.get("base_url", cls.base_url),
            _path=path,
        )

    @classmethod
    def load(cls, path: pathlib.Path) -> MegaConfig:
        """Carrega a configuração a partir de um ficheiro YAML existente."""
        path = pathlib.Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Ficheiro de configuração não encontrado: {path}")
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls.from_dict(data, path=path)

    @classmethod
    def default(cls, root: pathlib.Path | None = None) -> MegaConfig:
        """Retorna configuração padrão, opcionalmente associada a um directório raiz."""
        cfg = cls.from_dict(DEFAULT_CONFIG)
        if root is not None:
            cfg._path = pathlib.Path(root) / DEFAULT_CONFIG_NAME
        return cfg


def find_config(start: pathlib.Path | None = None) -> pathlib.Path | None:
    """Procura mega.yaml subindo na árvore de directórios a partir de *start*."""
    current = pathlib.Path(start) if start else pathlib.Path.cwd()
    current = current.resolve()
    for parent in [current, *current.parents]:
        candidate = parent / DEFAULT_CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def load_or_default(root: pathlib.Path | None = None) -> MegaConfig:
    """Carrega configuração existente ou devolve a padrão."""
    cfg_path = find_config(root)
    if cfg_path is not None:
        return MegaConfig.load(cfg_path)
    return MegaConfig.default(root)
