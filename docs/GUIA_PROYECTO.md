# Guía técnica y de entrega

## 1. Propósito

Este documento explica cómo instalar, ejecutar, probar, revisar y presentar el Sistema de Votaciones. Está pensado para que otra persona pueda clonar el proyecto, configurarlo localmente y verificar que cumple la prueba técnica sin depender de explicaciones externas.

## 2. Alcance funcional

El sistema administra tres recursos:

### Voter

Representa a una persona habilitada para votar.

| Campo | Tipo lógico | Reglas |
|---|---|---|
| `id` | Entero | Identificador autogenerado |
| `name` | Texto | Obligatorio, entre 1 y 120 caracteres |
| `email` | Email | Obligatorio y único |
| `has_voted` | Booleano | Inicia en `false`; cambia a `true` al votar |

### Candidate

Representa a una persona que recibe votos.

| Campo | Tipo lógico | Reglas |
|---|---|---|
| `id` | Entero | Identificador autogenerado |
| `name` | Texto | Obligatorio, entre 1 y 120 caracteres |
| `party` | Texto | Opcional, máximo 120 caracteres |
| `votes` | Entero | Inicia en `0` y aumenta al recibir votos |

### Vote

Registra la selección de un candidato por un votante.

| Campo | Tipo lógico | Reglas |
|---|---|---|
| `id` | Entero | Identificador autogenerado |
| `voter_id` | Entero | Clave foránea a `voters.id` y único |
| `candidate_id` | Entero | Clave foránea a `candidates.id` |

## 3. Arquitectura

La aplicación está separada por responsabilidades:

- `main.py`: crea la aplicación FastAPI y registra los routers.
- `config.py`: carga `DATABASE_URL` desde `.env`.
- `database.py`: configura SQLAlchemy, el engine, las sesiones y `get_db`.
- `models.py`: define las tablas y relaciones.
- `schemas.py`: valida solicitudes y define respuestas.
- `routers/`: expone los endpoints HTTP.
- `services/vote_service.py`: concentra la lógica transaccional del voto.
- `tests/`: valida los escenarios críticos sin tocar la base de datos real.
- `frontend/`: interfaz independiente en HTML, CSS y JavaScript que consume la API por HTTP.

Al iniciar FastAPI, el evento `lifespan` ejecuta `Base.metadata.create_all(bind=engine)` para asegurar que las tablas existan.

## 3.1. Arquitectura del frontend

El frontend y el backend están en el mismo repositorio, pero son aplicaciones separadas:

```text
Navegador -> frontend (puerto 5500) -> API FastAPI (puerto 8000) -> SQLite o SQL Server
```

El frontend no contiene credenciales ni conexión directa a SQL Server. Su cliente HTTP está en `frontend/js/api.js` y la lógica de la interfaz en `frontend/js/app.js`.

Para permitir el consumo desde el navegador, FastAPI restringe CORS a `localhost:5500` y `127.0.0.1:5500`.

La configuración predeterminada usa SQLite (`sqlite:///./votaciones.db`) para
que una copia nueva funcione sin instalar un servidor de base de datos. SQL
Server sigue soportado mediante `DATABASE_URL` en `.env`; los requisitos y
pasos están en [INSTALACION_LOCAL.md](INSTALACION_LOCAL.md).

## 3.2. Autenticación JWT y roles

La API utiliza JSON Web Tokens para proteger las operaciones de escritura. Existen dos roles:

- `admin`: gestiona votantes y candidatos.
- `voter`: emite únicamente su propio voto.

El endpoint `POST /auth/login` autentica al administrador con las credenciales configuradas en `.env`. El endpoint `POST /auth/voter-login` autentica al votante mediante el email y la contraseña almacenada como hash en `voters.password_hash`.

Las consultas de lectura permanecen públicas:

- `GET /voters`
- `GET /voters/{voter_id}`
- `GET /candidates`
- `GET /candidates/{candidate_id}`
- `GET /votes`
- `GET /votes/statistics`

Requieren `Authorization: Bearer <token>`:

- `POST` y `DELETE` de votantes.
- `POST` y `DELETE` de candidatos.
- `POST /votes`, validando además que el `voter_id` coincida con el token del votante.

El token expira según `JWT_EXPIRE_MINUTES`. En el frontend se conserva en `sessionStorage`, no en SQL Server. Las contraseñas no se guardan en texto plano: se almacenan mediante PBKDF2-HMAC-SHA256 con salt aleatorio.

El frontend aplica además una barrera de navegación: sin una sesión válida solo se muestra el login. El administrador ve gestión y consultas; el votante ve únicamente su flujo de participación y no recibe controles de edición.

## 4. Flujo de emisión de voto

Cuando llega `POST /votes`:

1. Se busca el votante.
2. Se busca el candidato.
3. Se verifica que el votante no haya votado.
4. Se crea el registro `Vote`.
5. Se actualiza `Voter.has_voted`.
6. Se incrementa `Candidate.votes`.
7. Se confirma una sola transacción con `commit`.
8. Si hay un error, se ejecuta `rollback` y no se deja un estado parcial.

La restricción única de `votes.voter_id` complementa la validación del código y protege contra solicitudes concurrentes.

## 5. Validación de nombres

La API no agrega un campo email al candidato. Para cumplir la regla de que una persona no puede aparecer en ambos roles:

- Se compactan los espacios del nombre.
- Se compara sin distinguir mayúsculas y minúsculas.
- La comparación se realiza al registrar votantes y candidatos.

Por ejemplo, `Ana Gómez`, ` ana   gómez ` y `ANA GÓMEZ` representan el mismo nombre para esta validación.

## 6. Instalación reproducible

### Crear entorno

```powershell
py -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Crear base de datos

```sql
CREATE DATABASE VotacionesDB;
GO
```

### Configurar conexión

Copiar `.env.example` a `.env` y revisar:

```env
DATABASE_URL=mssql+pyodbc://@localhost/VotacionesDB?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes
```

Para validar conectividad:

```powershell
sqlcmd -S localhost -E -C -d VotacionesDB -Q "SELECT DB_NAME() AS database_name"
```

El parámetro `-C` indica que se confía en el certificado local. En un entorno productivo debe utilizarse un certificado válido y una configuración de seguridad apropiada.

## 7. Guion recomendado de demostración

1. Iniciar el backend en el puerto `8000`.
2. Iniciar el frontend en el puerto `5500`.
3. Abrir `http://127.0.0.1:5500`.
4. Crear dos candidatos.
5. Crear dos o más votantes con emails distintos.
6. Emitir un voto por votante.
7. Actualizar el dashboard y revisar las estadísticas.
8. Intentar votar nuevamente con el primer votante y mostrar el `409`.
9. Intentar registrar como candidato el nombre de un votante y mostrar el `409`.
10. Abrir `http://127.0.0.1:8000/docs` para mostrar Swagger.
11. Consultar directamente SQL Server usando [SQL_VERIFICACION.md](SQL_VERIFICACION.md).
12. Capturar la respuesta de estadísticas para incluirla en la entrega.

## 8. Respuesta esperada de estadísticas

Ejemplo conceptual:

```json
{
  "total_votes": 2,
  "voters_who_voted": 2,
  "candidates": [
    {
      "candidate_id": 1,
      "candidate_name": "Carlos Ruiz",
      "votes": 1,
      "percentage": 50.0
    },
    {
      "candidate_id": 2,
      "candidate_name": "Laura Pérez",
      "votes": 1,
      "percentage": 50.0
    }
  ]
}
```

Si no existen votos, `total_votes` y `voters_who_voted` son `0`, y el porcentaje de cada candidato es `0.0`.

## 9. Matriz de errores

| Escenario | Código | Mensaje esperado |
|---|---:|---|
| Email repetido | `409` | `El email ya está registrado` |
| Nombre ya registrado como candidato | `409` | `El nombre ya está registrado como candidato` |
| Nombre ya registrado como votante | `409` | `El nombre ya está registrado como votante` |
| Votante inexistente al votar | `404` | `El votante no existe` |
| Candidato inexistente al votar | `404` | `El candidato no existe` |
| Segundo voto | `409` | `El votante ya emitió su voto` |
| Borrar votante que ya votó | `409` | No se puede eliminar un votante que ya votó |
| Borrar candidato con votos | `409` | No se puede eliminar un candidato con votos |
| ID inválido o campos incompletos | `422` | Error de validación de FastAPI |

## 10. Pruebas automatizadas

Ejecutar:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

La fixture de pruebas:

- Crea una base SQLite en memoria.
- Usa `StaticPool` para compartir la misma conexión entre solicitudes.
- Sobrescribe temporalmente `get_db`.
- Crea y elimina las tablas de prueba.
- No utiliza los datos de SQL Server.

Los escenarios cubiertos están en `tests/test_votes.py`.

## 11. Verificación directa en SQL Server

Las consultas detalladas están en [SQL_VERIFICACION.md](SQL_VERIFICACION.md). Las comprobaciones más importantes son:

- Tablas esperadas.
- Columnas y tipos.
- Claves foráneas.
- Unicidad de `voters.email`.
- Unicidad de `votes.voter_id`.
- Votos huérfanos.
- Votantes duplicados en la tabla de votos.
- Consistencia entre `has_voted` y `votes`.
- Consistencia entre `Candidate.votes` y el conteo real.
- Estadísticas calculadas directamente en SQL Server.

## 12. Seguridad y archivos excluidos

- Nunca escribir credenciales directamente en el código.
- No publicar `.env`.
- No publicar `venv/`.
- No incluir bases locales temporales ni archivos de caché.
- Usar `TrustServerCertificate=yes` solo para desarrollo local con SQL Server.
- Para producción, configurar certificados y secretos mediante el mecanismo seguro del entorno.

## 13. Checklist antes de entregar

- [ ] `pip install -r requirements.txt` funciona desde un entorno limpio.
- [ ] La base `VotacionesDB` existe y la conexión funciona.
- [ ] `uvicorn app.main:app --reload` inicia sin errores.
- [ ] El frontend inicia con `py -m http.server 5500`.
- [ ] El dashboard muestra el estado `API conectada`.
- [ ] El login JWT funciona con credenciales de desarrollo.
- [ ] Swagger muestra los endpoints.
- [ ] Las pruebas pasan.
- [ ] Se verifica un voto exitoso.
- [ ] Se verifica el rechazo del segundo voto.
- [ ] Se verifica la respuesta de estadísticas.
- [ ] Se verifica el rechazo del cruce votante/candidato.
- [x] Se agregan capturas de estadísticas en `docs/ScreenShotsPostman/`.
- [ ] `.env` y `venv/` quedan excluidos de Git.
- [ ] Se revisa el README.
- [x] Se inicializa Git y se publica el repositorio público: [SistemaDeVotaciones](https://github.com/HOLOMAN582/SistemaDeVotaciones).

## 14. Limitaciones conocidas

- La autenticación JWT con roles `admin` y `voter` está implementada.
- La identificación cruzada entre votante y candidato se basa en el nombre normalizado porque el modelo solicitado no define email para candidatos.
- `Base.metadata.create_all` crea tablas, pero no reemplaza un sistema de migraciones para cambios estructurales futuros.
- La eliminación de recursos con votos está bloqueada para conservar la trazabilidad histórica.

## 15. Revisión de orden del código

Durante la revisión se conservaron únicamente componentes con una responsabilidad clara:

- Los archivos `__init__.py` vacíos se mantienen porque identifican los paquetes Python.
- `app/auth.py` centraliza hash de contraseñas, JWT y autorización por rol.
- `app/routers/auth.py` concentra los dos flujos de login.
- `app/services/vote_service.py` conserva la transacción atómica del voto.
- `frontend/js/api.js` se limita a comunicación HTTP y sesión.
- `frontend/js/app.js` gestiona renderizado, eventos y vistas por rol.
- `tests/` mantiene una base aislada para no alterar SQL Server.

Los archivos generados localmente (`venv/`, `.pytest_cache/`, `__pycache__/`, `*.db` y `.env`) están excluidos mediante `.gitignore` y no deben formar parte del repositorio.
