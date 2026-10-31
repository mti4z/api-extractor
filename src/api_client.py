"""Cliente HTTP: realiza las peticiones GET a la API con manejo de errores.

Errores contemplados:
- 404 Not Found         -> el recurso no existe: se registra y se omite.
- 429 / 5xx             -> errores temporales: se reintenta con backoff exponencial.
- Timeout / ConnectionError -> la API no responde o no hay red: mensaje claro.
- Respuesta no JSON     -> se informa en lugar de romper el script.
"""
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Error irrecuperable al comunicarse con la API."""


class ResourceNotFoundError(APIError):
    """La API respondió 404 para el recurso pedido."""


def create_session(api_key: str | None, max_retries: int) -> requests.Session:
    """Crea una sesión HTTP reutilizable con reintentos automáticos."""
    session = requests.Session()
    retry = Retry(
        total=max_retries,
        backoff_factor=1,  # espera 1s, 2s, 4s... entre reintentos
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,  # devuelve la última respuesta para validarla nosotros
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))

    session.headers.update({"Accept": "application/json", "User-Agent": "api-extractor/1.0"})
    if api_key:
        session.headers["Authorization"] = f"Bearer {api_key}"
    return session


def fetch_json(session: requests.Session, url: str, timeout: int, params: dict | None = None) -> dict:
    """Hace un GET y devuelve el JSON, validando el status code."""
    try:
        response = session.get(url, params=params, timeout=timeout)
    except requests.exceptions.Timeout:
        raise APIError(f"La API no respondió en {timeout} segundos: {url}")
    except requests.exceptions.ConnectionError:
        raise APIError(f"No se pudo conectar con la API (¿sin internet o API caída?): {url}")
    except requests.exceptions.RequestException as exc:
        raise APIError(f"Error inesperado en la petición a {url}: {exc}")

    if response.status_code == 404:
        raise ResourceNotFoundError(f"Recurso no encontrado (404): {url}")
    if response.status_code >= 500:
        raise APIError(f"Error del servidor ({response.status_code}) tras varios reintentos: {url}")
    if response.status_code != 200:
        raise APIError(f"Respuesta inesperada ({response.status_code}): {url}")

    try:
        return response.json()
    except ValueError:
        raise APIError(f"La respuesta de {url} no es un JSON válido.")


def fetch_pokemon_list(session: requests.Session, base_url: str, limit: int,
                       offset: int, timeout: int) -> list[dict]:
    """Obtiene la lista paginada de Pokémon (nombre + URL de detalle)."""
    data = fetch_json(session, f"{base_url}/pokemon", timeout,
                      params={"limit": limit, "offset": offset})
    results = data.get("results", [])
    logger.info("Lista obtenida: %d Pokémon (de %s disponibles)", len(results), data.get("count", "?"))
    return results


def fetch_pokemon_details(session: requests.Session, items: list[dict], timeout: int) -> list[dict]:
    """Descarga el detalle de cada Pokémon. Los 404 se omiten sin cortar el proceso."""
    details, skipped = [], 0
    for i, item in enumerate(items, start=1):
        try:
            details.append(fetch_json(session, item["url"], timeout))
        except ResourceNotFoundError as exc:
            skipped += 1
            logger.warning("%s -> se omite.", exc)
        if i % 25 == 0 or i == len(items):
            logger.info("Progreso: %d/%d", i, len(items))
    if skipped:
        logger.warning("Se omitieron %d Pokémon por errores 404.", skipped)
    return details
