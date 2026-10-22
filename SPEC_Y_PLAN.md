# Prueba Técnica: Sistema de Votaciones (API RESTful)

> Documento de especificación y seguimiento del proyecto. Las guías, anexos y
> evidencias se encuentran organizados en `docs/`.

**Stack elegido:** Python 3.11+ · FastAPI · SQLAlchemy 2.x · SQLite/SQL Server · pyodbc · Pydantic · pytest
**Repositorio:** se publica una sola vez, al final

---

## 1. Enunciado original de la prueba

### Descripción del proyecto
Crear un API RESTful para gestionar un sistema de votaciones. El sistema debe manejar a los votantes y los candidatos, asegurar que cada votante pueda emitir un único voto, y proporcionar estadísticas sobre los resultados de la votación.

**Tiempo para entrega:** 1 día.

### Requisitos técnicos
1. **Lenguajes permitidos:** Python, Java, Node.js, PHP → *usaremos Python*.
2. **Base de datos:** SQL (MySQL, PostgreSQL) o NoSQL (MongoDB) → *usaremos SQLite por defecto para facilitar la ejecución local y SQL Server como opción compatible*.
3. **Modelo de datos:**

**Voter (Votante)**
- `id`: ID único (autogenerado).
- `name`: nombre del votante (cadena, obligatorio).
- `email`: correo electrónico único (cadena, obligatorio).
- `has_voted`: booleano que indica si ya ha votado (por defecto: `false`).

**Candidate (Candidato)**
- `id`: ID único (autogenerado).
- `name`: nombre del candidato (cadena, obligatorio).
- `party`: partido político del candidato (cadena, opcional).
- `votes`: número de votos recibidos (por defecto: `0`).

**Vote (Voto)**
- `id`: ID único (autogenerado).
- `voter_id`: ID del votante (relación).
- `candidate_id`: ID del candidato seleccionado (relación).

4. **Restricciones:**
   - Un votante no puede ser registrado como candidato y viceversa.
   - Cada votante puede emitir un único voto.
   - Los votos deben ser contados correctamente en las estadísticas.

### Endpoints

**Votantes**
- `POST /voters`: registrar un nuevo votante.
- `GET /voters`: obtener la lista de votantes.
- `GET /voters/{id}`: obtener detalles de un votante por ID.
- `DELETE /voters/{id}`: eliminar un votante.

**Candidatos**
- `POST /candidates`: registrar un nuevo candidato.
- `GET /candidates`: obtener la lista de candidatos.
- `GET /candidates/{id}`: obtener detalles de un candidato por ID.
- `DELETE /candidates/{id}`: eliminar un candidato.

**Votos**
- `POST /votes`: emitir un voto (se debe registrar el `voter_id` y el `candidate_id`).
- `GET /votes`: obtener todos los votos emitidos.
- `GET /votes/statistics`: obtener estadísticas de la votación:
  - Total de votos por candidato.
  - Porcentaje de votos por candidato.
  - Total de votantes que han votado.

### Validaciones
1. **Votantes y candidatos:** verificar que un votante no sea candidato y viceversa.
2. **Emisión de votos:**
   - Comprobar que el votante no haya votado previamente.
   - Validar que el `candidate_id` sea válido.
3. **Integridad de los datos:**
   - Actualizar automáticamente el campo `has_voted` del votante al emitir un voto.
   - Incrementar el conteo de votos del candidato seleccionado.

### Extras opcionales
1. Autenticación básica o con JWT para proteger los endpoints.
2. Filtrado y paginación en las listas de votantes y candidatos.

### Criterios de evaluación
1. Correcto funcionamiento de los endpoints.
2. Uso de validaciones y manejo de errores.
3. Estructura y organización del código.
4. Uso de patrones RESTful.
5. Documentación básica de la API (Swagger o README).

### Entrega
- Subir el código a un **repositorio público en GitHub** *(lo haremos al final, Fase 10)*.
- Incluir un `README.md` con:
  - Instrucciones para ejecutar el proyecto localmente.
  - Ejemplos de uso del API (Postman o curl).
  - **Capturas de las estadísticas generadas.**

---

## 2. Decisiones de diseño

| # | Decisión | Detalle |
|---|---|---|
| 1 | **Un voto por votante garantizado por la BD** | `UNIQUE` en `votes.voter_id`. Además del chequeo en código, para soportar peticiones simultáneas. |
| 2 | **Voto atómico** | Una sola transacción: validar votante → validar candidato → insertar `Vote` → `has_voted = True` → `candidate.votes += 1`. Si algo falla, `rollback`. |
| 3 | **Votante ≠ candidato** | `Candidate` no tiene `email`. Se comparan nombres normalizados (minúsculas y espacios compactados), tanto al registrar votantes como candidatos. |
| 4 | **Estadísticas** | Total por candidato, porcentaje sobre el total de votos y total de votantes que han votado. Evitar división por cero si aún no hay votos. |
| 5 | **Códigos HTTP** | `201` creación · `200` consulta · `204` borrado · `404` no existe · `409` conflicto (email duplicado, ya votó, cruce votante/candidato, borrado con votos) · `422` validación. |
| 6 | **Borrado** | Si un votante o candidato ya tiene votos, responder `409` y no permitir el borrado (documentarlo). |
| 7 | **Secretos** | Cadena de conexión en `.env`; incluir `.env.example` y agregar `.env` al `.gitignore`. |

---

## 3. Estructura del proyecto

```
votaciones-api/
├── app/
│   ├── main.py
│   ├── database.py          # engine, SessionLocal, Base, get_db
│   ├── config.py            # lectura de .env
│   ├── models.py            # Voter, Candidate, Vote
│   ├── schemas.py           # Pydantic (entrada/salida)
│   ├── routers/
│   │   ├── voters.py
│   │   ├── candidates.py
│   │   └── votes.py
│   └── services/
│       └── vote_service.py  # lógica transaccional del voto
├── tests/
│   ├── conftest.py
│   └── test_votes.py
├── docs/
│   ├── GUIA_PROYECTO.md
│   ├── INSTALACION_LOCAL.md
│   ├── SQL_VERIFICACION.md
│   └── ScreenShotsPostman/ # capturas y evidencias
├── .env.example
├── .gitignore
├── requirements.txt
├── scripts/
│   ├── setup_windows.ps1
│   ├── start_backend.ps1
│   └── start_frontend.ps1
└── README.md
```

**Dependencias (`requirements.txt`):**
```
fastapi
uvicorn[standard]
sqlalchemy>=2.0
pyodbc
pydantic[email]
python-dotenv
pytest
httpx
```

> Para una instalación nueva, la configuración recomendada es
> `DATABASE_URL=sqlite:///./votaciones.db`. La cadena SQL Server que aparece
> como referencia a continuación solo aplica si el equipo tiene SQL Server y
> ODBC Driver 18 instalados. Consulta `docs/INSTALACION_LOCAL.md`.

**Cadena de conexión (`.env`):**
```
DATABASE_URL=sqlite:///./votaciones.db
```
Con autenticación de Windows: `mssql+pyodbc://@localhost/VotacionesDB?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes`

---

## 4. Plan de trabajo por fases

Regla: el desarrollo y las validaciones se realizan localmente. La publicación
del repositorio se realiza al finalizar la preparación del proyecto.

### Fase 0: Setup y portabilidad 
- [x] Crear la carpeta del proyecto y abrirla en VS Code.
- [x] Crear entorno virtual e instalar dependencias.
- [x] Verificar el arranque local con SQLite.
- [x] Mantener SQL Server como opción mediante `DATABASE_URL` y pyodbc.
- [x] Crear scripts reproducibles de instalación y arranque para Windows.
- [x] `.gitignore` y `.env.example` (para que el proyecto ya quede listo para subir al final), y estructura de carpetas.

### Fase 1: Modelos 
- [x] `Voter`: `email` único, `has_voted` default `False`.
- [x] `Candidate`: `party` opcional, `votes` default `0`.
- [x] `Vote`: FKs a voter y candidate, `UNIQUE(voter_id)`.
- [x] Crear tablas al iniciar la app (`Base.metadata.create_all`).

### Fase 2: CRUD de votantes 
- [x] `POST /voters` (409 si el email existe).
- [x] `GET /voters`, `GET /voters/{id}` (404 si no existe).
- [x] `DELETE /voters/{id}`.

### Fase 3: CRUD de candidatos 
- [x] Mismos endpoints que votantes.
- [x] Validación cruzada votante ↔ candidato (en ambos sentidos).

### Fase 4: Votos 
- [x] `POST /votes` con transacción atómica (`vote_service.py`).
- [x] 404 si el votante o candidato no existe; 409 si ya votó.
- [x] `GET /votes`.

### Fase 5: Estadísticas 
- [x] `GET /votes/statistics`: total por candidato, porcentaje, votantes que han votado.
- [x] Manejo de división por cero.

### Fase 6: Manejo de errores 
- [x] Mensajes claros y consistentes en todos los errores.
- [x] Revisar códigos HTTP según la tabla de decisiones.

### Fase 7: Pruebas 
- [x] Votar correctamente actualiza `has_voted` y el conteo del candidato.
- [x] Segundo voto del mismo votante → 409.
- [x] Candidato inexistente → 404.
- [x] Email duplicado → 409.
- [x] Votante registrado como candidato → 409.
- [x] Estadísticas sin votos (sin error de división por cero).

### Fase 8: README, guías y capturas 
- [x] Descripción y decisiones de diseño.
- [x] Instrucciones para ejecutar localmente.
- [x] Ejemplos con curl o Postman de todos los endpoints principales.
- [x] **Capturas de las estadísticas** (disponibles en `docs/ScreenShotsPostman/`).
- [x] Enlace al Swagger (`/docs`).
- [x] Guías, anexos, consultas y evidencias enlazadas desde el README en `docs/`.

### Fase 9: Extras 
- [x] Paginación (`skip`/`limit`) y filtros en `GET /voters` y `GET /candidates`.
- [x] Autenticación JWT con roles `admin` y `voter` para proteger los endpoints.

### Checklist previo a publicar (todo en local) 
- [x] Todos los endpoints funcionan desde Swagger.
- [x] README completo con capturas.
- [x] Tests pasan (`pytest`).
- [ ] `.env` no está incluido y `.env.example` sí.
- [x] Scripts de instalación y arranque independientes de la ruta local.
- [ ] Probar la instalación desde cero en una carpeta limpia siguiendo el README.

### Fase 10: Publicar en GitHub 
- [ ] Crear el repositorio **público** en GitHub (sin README inicial, para evitar conflictos).
- [ ] En la carpeta del proyecto: `git init`, `git add .`, `git commit -m "feat: API de votaciones"`.
- [ ] Verificar con `git status` que `.env` y `venv/` **no** se van a subir.
- [ ] `git remote add origin <URL>`, `git branch -M main`, `git push -u origin main`.
- [ ] Abrir el repo en el navegador y comprobar que el README se ve bien, con las capturas.
- [ ] Copiar el enlace del repo para la entrega.

---

## 5. Comandos útiles

```bash
# Instalación reproducible (Windows, desde la raíz)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup_windows.ps1

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la API
.\scripts\start_backend.ps1
# Swagger: http://127.0.0.1:8000/docs

# Ejecutar el frontend en otra terminal
.\scripts\start_frontend.ps1

# Ejecutar tests
pytest -v
```

**Ejemplos curl para el README:**
```bash
curl -X POST http://127.0.0.1:8000/voters -H "Content-Type: application/json" \
  -d '{"name":"Ana Gómez","email":"ana@mail.com"}'

curl -X POST http://127.0.0.1:8000/candidates -H "Content-Type: application/json" \
  -d '{"name":"Carlos Ruiz","party":"Partido Verde"}'

curl -X POST http://127.0.0.1:8000/votes -H "Content-Type: application/json" \
  -d '{"voter_id":1,"candidate_id":1}'

curl http://127.0.0.1:8000/votes/statistics
```
