"""Transformación básica: convierte el JSON crudo de la API en registros limpios.

La respuesta de /pokemon/{id} trae ~20 campos anidados y muy pesados
(moves, game_indices, sprites en decenas de variantes, etc.). Solo se
conservan los campos útiles para análisis, aplanados en una estructura tabular.
"""


def clean_pokemon(raw: dict) -> dict:
    """Reduce y aplana un registro de Pokémon."""
    stats = {s["stat"]["name"].replace("-", "_"): s["base_stat"] for s in raw.get("stats", [])}
    types = [t["type"]["name"] for t in sorted(raw.get("types", []), key=lambda t: t["slot"])]

    return {
        "id": raw["id"],
        "name": raw["name"],
        "type_primary": types[0] if types else None,
        "type_secondary": types[1] if len(types) > 1 else None,
        "height_m": raw.get("height", 0) / 10,    # la API lo da en decímetros
        "weight_kg": raw.get("weight", 0) / 10,   # la API lo da en hectogramos
        "base_experience": raw.get("base_experience"),
        "hp": stats.get("hp"),
        "attack": stats.get("attack"),
        "defense": stats.get("defense"),
        "special_attack": stats.get("special_attack"),
        "special_defense": stats.get("special_defense"),
        "speed": stats.get("speed"),
        "total_stats": sum(stats.values()) if stats else None,
        "abilities": "|".join(a["ability"]["name"] for a in raw.get("abilities", [])),
        "sprite_url": (raw.get("sprites") or {}).get("front_default"),
    }


def transform(raw_records: list[dict]) -> list[dict]:
    """Limpia todos los registros, elimina duplicados por id y los ordena."""
    unique = {r["id"]: clean_pokemon(r) for r in raw_records}
    return [unique[k] for k in sorted(unique)]
