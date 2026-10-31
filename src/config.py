"""Carga y validación de la configuración desde variables de entorno (.env).

Ningún valor sensible ni de configuración está escrito "a mano" en el código:
todo se lee de variables de entorno, que python-dotenv carga desde el
archivo .env (excluido del repositorio mediante .gitignore).
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga el archivo .env (si existe) en las variables de entorno del proceso.
load_dotenv(BASE_DIR / ".env")


class ConfigError(Exception):
    """Error de configuración (variable faltante o con formato inválido)."""


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str | None
    limit: int
    offset: int
    timeout: int
    max_retries: int
    output_dir: Path


def _get_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"La variable {name} debe ser un número entero (valor actual: '{raw}').")
    if value < minimum:
        raise ConfigError(f"La variable {name} debe ser >= {minimum} (valor actual: {value}).")
    return value


def load_settings() -> Settings:
    """Lee las variables de entorno y devuelve la configuración validada."""
    base_url = os.getenv("POKEAPI_BASE_URL", "").strip().rstrip("/")
    if not base_url:
        raise ConfigError(
            "Falta la variable POKEAPI_BASE_URL. Copiá .env.example como .env y completala."
        )

    return Settings(
        base_url=base_url,
        # PokeAPI no requiere API key. Si se usa una API que sí la pida,
        # se define API_KEY en .env y el cliente la envía en los headers.
        api_key=os.getenv("API_KEY", "").strip() or None,
        limit=_get_int("POKEMON_LIMIT", 151, minimum=1),
        offset=_get_int("POKEMON_OFFSET", 0),
        timeout=_get_int("REQUEST_TIMEOUT", 10, minimum=1),
        max_retries=_get_int("MAX_RETRIES", 3),
        output_dir=BASE_DIR / os.getenv("OUTPUT_DIR", ".").strip(),
    )
