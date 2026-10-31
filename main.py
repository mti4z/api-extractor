"""Extractor de datos de la PokeAPI.

Flujo: configuración (.env) -> extracción (GET) -> transformación -> persistencia.

Uso:
    python main.py
"""
import logging
import sys

from src.api_client import APIError, create_session, fetch_pokemon_details, fetch_pokemon_list
from src.config import ConfigError, load_settings
from src.storage import save_csv, save_json
from src.transform import transform

logger = logging.getLogger("extractor")


def run() -> None:
    settings = load_settings()
    logger.info("API: %s | Pokémon a extraer: %d (offset %d)",
                settings.base_url, settings.limit, settings.offset)

    with create_session(settings.api_key, settings.max_retries) as session:
        items = fetch_pokemon_list(session, settings.base_url, settings.limit,
                                   settings.offset, settings.timeout)
        raw = fetch_pokemon_details(session, items, settings.timeout)

    records = transform(raw)
    if not records:
        raise APIError("La API no devolvió datos para guardar.")

    save_json(records, settings.output_dir / "data_extracted.json")
    save_csv(records, settings.output_dir / "data_extracted.csv")
    logger.info("Extracción finalizada: %d Pokémon guardados.", len(records))


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s | %(levelname)-7s | %(message)s",
                        datefmt="%H:%M:%S")
    try:
        run()
    except ConfigError as exc:
        logger.error("Error de configuración: %s", exc)
        return 1
    except APIError as exc:
        logger.error("Error al consultar la API: %s", exc)
        return 1
    except KeyboardInterrupt:
        logger.warning("Ejecución cancelada por el usuario.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
