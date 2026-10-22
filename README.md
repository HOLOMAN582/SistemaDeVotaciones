# Sistema de Votaciones - API REST

API RESTful para gestionar votantes, candidatos, votos y estadísticas electorales. El proyecto fue desarrollado como prueba técnica con Python, FastAPI, SQLAlchemy 2 y SQL Server.

> Con el debido permiso, me tomé la libertad de agregar un frontend breve al proyecto para facilitar la demostración visual de la API. Espero que sea de utilidad y les guste.

## Resumen funcional

La API permite:

- Registrar y consultar votantes.
- Registrar y consultar candidatos.
- Emitir un único voto por votante.
- Consultar los votos emitidos.
- Obtener estadísticas por candidato y porcentajes.
- Evitar que una misma persona sea registrada como votante y candidato.
- Filtrar y paginar listados.
- Rechazar eliminaciones que comprometan la integridad de la votación.

## Tecnologías

| Tecnología     | Uso                              |
| -------------- | -------------------------------- |
| Python 3.11+   | Lenguaje principal               |
| FastAPI        | API REST y documentación OpenAPI |
| SQLAlchemy 2.x | Modelado y acceso a datos        |
| pyodbc         | Conexión con SQL Server          |
| SQL Server     | Base de datos relacional         |
| Pydantic 2     | Validación y serialización       |
| pytest         | Pruebas automatizadas            |
| python-jose    | Tokens JWT |

## Requisitos previos

1. Python 3.11 o superior.
2. PowerShell.
3. SQL Server y ODBC Driver 18 únicamente si se desea usar el modo SQL Server.

## Instalación en Windows

Desde la carpeta raíz del proyecto, ejecuta el instalador reproducible:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup_windows.ps1
```

El script crea un entorno virtual propio, instala las dependencias y genera
`.env`. No es necesario copiar el `venv` desde otra máquina.

La instalación manual equivalente es:

```powershell
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Configuración de la base de datos

### Opción recomendada para ejecutar en cualquier máquina: SQLite

`.env.example` usa SQLite por defecto:

```env
DATABASE_URL=sqlite:///./votaciones.db
```

No requiere instalar SQL Server. Las tablas se crean automáticamente al iniciar
la aplicación y `votaciones.db` se genera localmente.

### Opción SQL Server

Si se desea conservar SQL Server, instala SQL Server y ODBC Driver 18, y crea:

```sql
CREATE DATABASE VotacionesDB;
GO
```

Reemplaza `DATABASE_URL` en `.env` con una cadena válida para esa máquina:

```env
DATABASE_URL=mssql+pyodbc://@localhost/VotacionesDB?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes
JWT_SECRET_KEY=change-this-development-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_EXPIRE_MINUTES=60
```

No publicar `.env`. El archivo `.env.example` sirve como plantilla y `.gitignore` excluye las credenciales y el entorno virtual.

Las tablas se crean automáticamente al iniciar la aplicación mediante
`Base.metadata.create_all`. La guía completa está en
[Instalación local](docs/INSTALACION_LOCAL.md).

## Ejecutar la aplicación

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Direcciones disponibles:

- API: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

Swagger permite ejecutar y revisar cada endpoint sin instalar Postman.

## Endpoints

### Votantes

| Método | Ruta                 | Respuesta principal       |
| ------ | -------------------- | ------------------------- |
| POST   | `/voters`            | `201` y votante creado    |
| GET    | `/voters`            | `200` y lista de votantes |
| GET    | `/voters/{voter_id}` | `200` o `404`             |
| DELETE | `/voters/{voter_id}` | `204`, `404` o `409`      |

`GET /voters` acepta:

- `skip`: cantidad de registros a omitir; por defecto `0`.
- `limit`: máximo de registros; por defecto `100`, máximo `100`.
- `name`: filtro parcial por nombre.

### Candidatos

| Método | Ruta                         | Respuesta principal         |
| ------ | ---------------------------- | --------------------------- |
| POST   | `/candidates`                | `201` y candidato creado    |
| GET    | `/candidates`                | `200` y lista de candidatos |
| GET    | `/candidates/{candidate_id}` | `200` o `404`               |
| DELETE | `/candidates/{candidate_id}` | `204`, `404` o `409`        |

`GET /candidates` acepta los mismos parámetros `skip`, `limit` y `name`.

### Votos y estadísticas

| Método | Ruta                | Respuesta principal    |
| ------ | ------------------- | ---------------------- |
| POST   | `/votes`            | `201` y voto creado    |
| GET    | `/votes`            | `200` y lista de votos |
| GET    | `/votes/statistics` | `200` y estadísticas   |

## Ejemplos con curl

Registrar un votante:

```powershell
curl.exe -X POST http://127.0.0.1:8000/voters `
  -H "Content-Type: application/json" `
  -d '{"name":"Ana Gómez","email":"ana@mail.com"}'
```

Registrar un candidato:

```powershell
curl.exe -X POST http://127.0.0.1:8000/candidates `
  -H "Content-Type: application/json" `
  -d '{"name":"Carlos Ruiz","party":"Partido Verde"}'
```

Emitir un voto:

```powershell
curl.exe -X POST http://127.0.0.1:8000/votes `
  -H "Content-Type: application/json" `
  -d '{"voter_id":1,"candidate_id":1}'
```

Consultar estadísticas:

```powershell
curl.exe http://127.0.0.1:8000/votes/statistics
```

Consultar con filtro y paginación:

```powershell
curl.exe "http://127.0.0.1:8000/voters?name=Ana&skip=0&limit=10"
curl.exe "http://127.0.0.1:8000/candidates?skip=0&limit=10"
```

## Reglas de negocio

- `email` es obligatorio y único para cada votante.
- El nombre se normaliza eliminando espacios sobrantes y se compara sin distinguir mayúsculas/minúsculas.
- Un nombre registrado como votante no puede registrarse como candidato, ni al contrario.
- Un votante inexistente o un candidato inexistente impiden registrar el voto.
- Un votante que ya votó recibe `409 Conflict` si intenta votar de nuevo.
- La base de datos también impone `UNIQUE(voter_id)` como protección ante solicitudes simultáneas.
- Emitir un voto actualiza en una sola transacción el registro de `Vote`, `Voter.has_voted` y `Candidate.votes`.
- No se puede eliminar un votante que ya votó ni un candidato que tiene votos.
- Los porcentajes se calculan sobre el total de votos y son `0.0` cuando no hay votos.

## Códigos HTTP

| Código | Significado                      |
| -----: | -------------------------------- |
|  `200` | Consulta exitosa                 |
|  `201` | Recurso creado                   |
|  `204` | Recurso eliminado                |
|  `404` | Votante o candidato inexistente  |
|  `409` | Conflicto de negocio o duplicado |
|  `422` | Datos de entrada inválidos       |

## Ejecutar pruebas

Las pruebas utilizan una base SQLite temporal y no modifican SQL Server:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

Las pruebas cubren el voto exitoso, el voto duplicado, entidades inexistentes, email duplicado, cruce votante/candidato y estadísticas sin votos.

## Capturas para la entrega

Las evidencias del proyecto están en `docs/ScreenShotsPostman/`:

```text
docs/ScreenShotsPostman/ContrasteEstadisticaWeb.png
docs/ScreenShotsPostman/Ejm1.png
docs/ScreenShotsPostman/Ejm2.png
docs/ScreenShotsPostman/Ejm2_1.png
docs/ScreenShotsPostman/Ejm3.png
docs/ScreenShotsPostman/Ejm4.png
docs/ScreenShotsPostman/Estadisticas.png
```

La captura principal es
[Estadisticas.png](docs/ScreenShotsPostman/Estadisticas.png), con la respuesta
de `GET /votes/statistics`.

## Estructura

```text
app/
├── main.py                  # Configuración de FastAPI y routers
├── config.py                # Lectura de variables de entorno
├── database.py              # Engine, sesiones y dependencia get_db
├── models.py                # Modelos Voter, Candidate y Vote
├── schemas.py               # Schemas de entrada y salida
├── routers/
│   ├── voters.py            # Endpoints de votantes
│   ├── candidates.py        # Endpoints de candidatos
│   └── votes.py             # Endpoints de votos y estadísticas
└── services/
    └── vote_service.py      # Transacción atómica de emisión de voto
tests/
├── conftest.py              # Base de pruebas y dependency override
└── test_votes.py            # Casos críticos
docs/
├── GUIA_PROYECTO.md         # Documentación detallada
├── INSTALACION_LOCAL.md      # Guía reproducible para otra máquina
└── SQL_VERIFICACION.md      # Consultas de comprobación en SQL Server
scripts/
├── setup_windows.ps1         # Crea entorno e instala dependencias
├── start_backend.ps1         # Inicia FastAPI
└── start_frontend.ps1        # Inicia el servidor web
frontend/
├── index.html                # Interfaz del sistema
├── css/styles.css            # Estilos responsive
├── js/api.js                 # Cliente HTTP de la API
├── js/app.js                 # Lógica de la interfaz
└── README.md                 # Instrucciones del frontend
```

## Documentación complementaria

> **Nota para la revisión:** las guías, anexos, consultas de verificación y
> evidencias de la prueba se encuentran organizados en la carpeta `docs/`.
> Allí también está disponible el material de instalación, ejecución y
> comprobación del sistema. Las pruebas automatizadas del backend se encuentran
> en `tests/` y pueden ejecutarse con `pytest`.

- [Guía detallada del proyecto](docs/GUIA_PROYECTO.md)
- [Instalación y ejecución local](docs/INSTALACION_LOCAL.md)
- [Consultas de verificación SQL Server](docs/SQL_VERIFICACION.md)
- [Evidencias de Postman y estadísticas](docs/ScreenShotsPostman/)
- [Especificación y plan de trabajo](SPEC_Y_PLAN.md)
- [Documentación del frontend](frontend/README.md)

## Autenticación JWT

El sistema maneja dos roles:

- **Administrador:** inicia sesión con `username` y `password`; administra votantes y candidatos.
- **Votante:** inicia sesión con su email y contraseña; únicamente puede emitir su propio voto.

Las consultas `GET` permanecen públicas. Las operaciones de escritura requieren un token JWT:

- `POST /voters`
- `DELETE /voters/{voter_id}`
- `POST /candidates`
- `DELETE /candidates/{candidate_id}`
- `POST /votes`

### Login de administrador

```powershell
curl.exe -X POST http://127.0.0.1:8000/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"admin123"}'
```

### Login de votante

El administrador debe registrar al votante con una contraseña de mínimo 8 caracteres. Luego el votante obtiene su token:

```powershell
curl.exe -X POST http://127.0.0.1:8000/auth/voter-login `
  -H "Content-Type: application/json" `
  -d '{"email":"ana@mail.com","password":"votante123"}'
```

El endpoint `POST /votes` valida que el `voter_id` enviado coincida con el votante incluido en el token. Un votante no puede votar en nombre de otra persona.

### Registrar un votante como administrador

Usar el token de administrador recibido:

```powershell
curl.exe -X POST http://127.0.0.1:8000/voters `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer TU_TOKEN" `
  -d '{"name":"Ana Gómez","email":"ana@mail.com","password":"votante123"}'
```

En un entorno real se deben cambiar `JWT_SECRET_KEY`, `ADMIN_USERNAME` y `ADMIN_PASSWORD` en `.env`. El frontend muestra primero una pantalla de login y no carga información del sistema hasta autenticar al usuario. Después presenta una vista distinta según el rol: administración completa para `admin` y participación electoral limitada para `voter`. El token se conserva solo en `sessionStorage`.

## Ejecutar el backend y el frontend

El frontend está separado del backend, pero ambos se entregan en el mismo repositorio. Se deben ejecutar en dos terminales.

### Terminal 1: backend FastAPI

Abre una primera terminal de PowerShell y ejecuta:

```powershell
.\scripts\start_backend.ps1
```

Backend disponible en `http://127.0.0.1:8000`.

También puede ejecutarse sin activar manualmente el entorno:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2: frontend

Abre una segunda terminal de PowerShell y ejecuta:

```powershell
.\scripts\start_frontend.ps1
```

Frontend disponible en `http://127.0.0.1:5500`.

El frontend consume la API mediante HTTP y nunca accede directamente a SQL Server.

### Detener los servicios

En cada terminal presiona `Ctrl + C`. Si una terminal ya se cerró, identifica y detén el proceso que ocupa el puerto:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
Get-NetTCPConnection -LocalPort 5500 -State Listen
Stop-Process -Id <PID>
```

### Verificación rápida

Con ambos servicios iniciados:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/openapi.json
Invoke-WebRequest http://127.0.0.1:5500
```

Luego abre `http://127.0.0.1:5500` en el navegador y verifica que aparezca el estado `API conectada`.

## Entrega

Antes de publicar:

1. Ejecutar las pruebas.
2. Probar el flujo completo desde Swagger.
3. Probar el flujo completo desde el frontend.
4. Validar estadísticas.
5. Revisar las capturas de `docs/ScreenShotsPostman/`.
6. Confirmar que `.env`, `venv/`, archivos `*.db` y cachés no se incluyan.
7. Inicializar Git y publicar el repositorio público.

La autenticación JWT y la separación de roles `admin`/`voter` están
implementadas. La paginación y el filtro también están incluidos.
