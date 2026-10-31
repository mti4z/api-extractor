# Extractor de datos vía API: PokeAPI

Script en Python que consulta la [PokeAPI](https://pokeapi.co/) mediante peticiones `GET`, limpia la respuesta JSON y guarda los datos en **`data_extracted.csv`** y **`data_extracted.json`**. La configuración se maneja con variables de entorno (`.env`) y los errores de red y HTTP se controlan para que el script nunca se rompa de forma abrupta.

## Estructura del proyecto

```
api-extractor/
├── main.py                 # Punto de entrada: orquesta el flujo y captura errores
├── src/
│   ├── config.py           # Carga y valida las variables de entorno (.env)
│   ├── api_client.py       # Peticiones GET, reintentos y manejo de errores HTTP
│   ├── transform.py        # Limpieza: elimina campos innecesarios y aplana el JSON
│   └── storage.py          # Exportación a CSV y JSON
├── data_extracted.csv      # Salida: 151 Pokémon (formato tabular)
├── data_extracted.json     # Salida: 151 Pokémon (formato JSON)
├── .env.example            # Plantilla de configuración (sin datos sensibles)
├── .gitignore              # Excluye .env, entornos virtuales y cachés
├── requirements.txt
└── README.md
```

## Instalación

Requisitos: **Python 3.10 o superior**.

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/api-extractor.git
cd api-extractor

# 2. Crear y activar un entorno virtual
python -m venv .venv
.venv\Scripts\activate           # Windows (PowerShell)
source .venv/bin/activate        # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt
```

## Configuración (`.env`)

Copiá la plantilla y, si querés, ajustá los valores:

```bash
copy .env.example .env           # Windows
cp .env.example .env             # Linux / macOS
```

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `POKEAPI_BASE_URL` | `https://pokeapi.co/api/v2` | URL base de la API (**obligatoria**) |
| `API_KEY` | *(vacío)* | Token de acceso. PokeAPI no lo requiere; si se usa otra API que sí lo pida, se envía como header `Authorization: Bearer ...` |
| `POKEMON_LIMIT` | `151` | Cantidad de Pokémon a extraer |
| `POKEMON_OFFSET` | `0` | Desde qué posición empezar |
| `REQUEST_TIMEOUT` | `10` | Segundos máximos de espera por petición |
| `MAX_RETRIES` | `3` | Reintentos ante errores temporales (429, 5xx) |
| `OUTPUT_DIR` | `.` | Carpeta donde se guardan los archivos de salida |

> **Seguridad:** el archivo `.env` está incluido en `.gitignore`, así que nunca se sube a GitHub. En el repositorio solo está `.env.example`, sin valores sensibles. El código no tiene ninguna credencial escrita a mano (*hardcodeada*).

## Ejecución

```bash
python main.py
```

Salida esperada:

```
INFO    | API: https://pokeapi.co/api/v2 | Pokémon a extraer: 151 (offset 0)
INFO    | Lista obtenida: 151 Pokémon (de 1302 disponibles)
INFO    | Progreso: 25/151
...
INFO    | JSON guardado: data_extracted.json (151 registros)
INFO    | CSV guardado: data_extracted.csv (151 registros)
INFO    | Extracción finalizada: 151 Pokémon guardados.
```

## Cómo funciona

### 1. Configuración (`src/config.py`)
`python-dotenv` carga el archivo `.env` y cada variable se valida: si falta `POKEAPI_BASE_URL`, o si un número tiene un formato inválido, el script lo informa con un mensaje claro y termina sin errores técnicos.

### 2. Extracción (`src/api_client.py`)
- `GET /pokemon?limit=151&offset=0` devuelve la lista de Pokémon con la URL de detalle de cada uno.
- `GET /pokemon/{id}/` devuelve el detalle de cada Pokémon.
- Se usa una `requests.Session` reutilizable, más eficiente que abrir una conexión nueva por petición.

### 3. Transformación (`src/transform.py`)
La respuesta de cada Pokémon tiene más de 20 campos anidados (movimientos, índices de juegos, decenas de variantes de imágenes) y pesa alrededor de **400 KB**. Se conservan solo los 16 campos útiles para análisis, aplanados en formato tabular:

| Campo | Descripción |
|---|---|
| `id`, `name` | Identificador y nombre |
| `type_primary`, `type_secondary` | Tipos del Pokémon (el secundario puede ser nulo) |
| `height_m`, `weight_kg` | Altura y peso, convertidos a metros y kilogramos (la API los da en decímetros y hectogramos) |
| `base_experience` | Experiencia base |
| `hp`, `attack`, `defense`, `special_attack`, `special_defense`, `speed` | Estadísticas base |
| `total_stats` | Suma de las 6 estadísticas (campo calculado) |
| `abilities` | Habilidades separadas por `\|` |
| `sprite_url` | URL de la imagen oficial |

Además se eliminan duplicados por `id` y los registros se ordenan. En total, unos 60 MB de respuestas crudas quedan reducidos a un JSON de ~70 KB.

### 4. Persistencia (`src/storage.py`)
Los datos se guardan en dos formatos dentro del repositorio:
- **`data_extracted.csv`**: listo para abrir en Excel o cargar con `pandas.read_csv()`.
- **`data_extracted.json`**: conserva los tipos de datos (por ejemplo, `null` en `type_secondary`) y es fácil de consumir desde otras aplicaciones.

## Manejo de errores

| Situación | Comportamiento |
|---|---|
| **404 Not Found** en un Pokémon | Se registra una advertencia, se omite ese registro y el proceso continúa |
| **429 / 500 / 502 / 503 / 504** | Se reintenta automáticamente con espera exponencial (1 s, 2 s, 4 s...). Si el error persiste, se informa con un mensaje claro |
| **API caída o sin internet** (`ConnectionError`) | Mensaje: *"No se pudo conectar con la API (¿sin internet o API caída?)"* |
| **La API tarda demasiado** (`Timeout`) | Mensaje indicando que no respondió en el tiempo configurado |
| **Respuesta que no es JSON** | Se informa en lugar de romper el script |
| **`.env` faltante o con valores inválidos** | Mensaje que indica qué variable corregir |
| **Cancelación con Ctrl+C** | Termina de forma ordenada |

En todos los casos de error, el script termina con código de salida `1` y un mensaje legible, sin mostrar un *traceback*.

**Para probarlo**, cambiá en `.env` la URL por una inexistente y ejecutá el script:

```
POKEAPI_BASE_URL=https://pokeapi.co/api/v2-no-existe
```
```
ERROR   | Error al consultar la API: Recurso no encontrado (404): https://pokeapi.co/api/v2-no-existe/pokemon
```

## Tecnologías

Python 3.10+ · requests · python-dotenv · urllib3 (reintentos)
