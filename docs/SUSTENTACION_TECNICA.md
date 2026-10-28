# Documento técnico de sustentación

## 1. Presentación del proyecto

El proyecto es un sistema de votaciones expuesto mediante una API RESTful.
Permite administrar votantes y candidatos, registrar un único voto por
votante y consultar estadísticas de participación y resultados.

Como complemento se incluye un frontend independiente construido con HTML, CSS
y JavaScript nativo. El frontend consume la API por HTTP y no se conecta
directamente a la base de datos.

Repositorio:

<https://github.com/HOLOMAN582/SistemaDeVotaciones>

## 2. Objetivo funcional

El sistema resuelve las siguientes necesidades:

- Registrar votantes con email único.
- Registrar candidatos con partido opcional.
- Impedir que una misma persona sea votante y candidato.
- Garantizar un solo voto por votante.
- Validar que el candidato exista.
- Actualizar el estado del votante después de votar.
- Mantener el conteo de votos por candidato.
- Calcular estadísticas y porcentajes.
- Proteger las operaciones de escritura mediante JWT y roles.
- Permitir filtros y paginación en los listados.

## 3. Stack tecnológico

| Tecnología | Uso en el proyecto |
|---|---|
| Python 3.11+ | Lenguaje de programación |
| FastAPI | Framework de la API REST y documentación OpenAPI |
| Uvicorn | Servidor ASGI para ejecutar FastAPI |
| SQLAlchemy 2.x | ORM, modelos, consultas y transacciones |
| SQLite | Base local predeterminada para ejecución sencilla |
| SQL Server | Base compatible con la prueba técnica |
| pyodbc | Driver de conexión entre SQLAlchemy y SQL Server |
| Pydantic 2 | Validación de solicitudes y serialización de respuestas |
| python-jose | Creación y validación de tokens JWT |
| hashlib PBKDF2-HMAC-SHA256 | Hash seguro de contraseñas |
| pytest | Pruebas automatizadas |
| HTML/CSS/JavaScript | Frontend independiente |

### Razón de usar SQLite por defecto

SQLite permite que una persona descargue el repositorio y ejecute el proyecto
sin instalar un servidor de base de datos. La aplicación crea `votaciones.db`
y sus tablas al iniciar.

SQL Server continúa disponible mediante la variable `DATABASE_URL`. Esto
permite conservar la compatibilidad con el entorno original de desarrollo y
con la prueba técnica.

## 4. Arquitectura

La aplicación está organizada por responsabilidades:

```text
Navegador
   |
   v
Frontend HTML/CSS/JavaScript :5500
   |
   | HTTP/JSON + JWT
   v
FastAPI/Uvicorn :8000
   |
   +-- Routers: endpoints HTTP
   +-- Schemas: validación Pydantic
   +-- Auth: JWT, roles y contraseñas
   +-- Services: lógica transaccional
   |
   v
SQLAlchemy
   |
   v
SQLite o SQL Server
```

### Organización del backend

- `app/main.py`: crea la aplicación, configura CORS, crea tablas al iniciar y
  registra los routers.
- `app/config.py`: carga la configuración desde `.env`.
- `app/database.py`: crea el engine, la sesión y la dependencia `get_db`.
- `app/models.py`: define `Voter`, `Candidate` y `Vote`.
- `app/schemas.py`: define los contratos de entrada y salida.
- `app/auth.py`: hash de contraseñas, JWT y dependencias de autorización.
- `app/routers/auth.py`: login de administrador y votante.
- `app/routers/voters.py`: operaciones de votantes.
- `app/routers/candidates.py`: operaciones de candidatos.
- `app/routers/votes.py`: emisión de votos y estadísticas.
- `app/services/vote_service.py`: transacción central de emisión del voto.

## 5. Modelo de datos

### Voter

| Campo | Descripción |
|---|---|
| `id` | Identificador autogenerado |
| `name` | Nombre obligatorio |
| `email` | Email obligatorio y único |
| `password_hash` | Contraseña almacenada como hash |
| `has_voted` | Indica si el votante ya votó |

### Candidate

| Campo | Descripción |
|---|---|
| `id` | Identificador autogenerado |
| `name` | Nombre obligatorio |
| `party` | Partido opcional |
| `votes` | Contador de votos recibidos |

### Vote

| Campo | Descripción |
|---|---|
| `id` | Identificador autogenerado |
| `voter_id` | Clave foránea al votante |
| `candidate_id` | Clave foránea al candidato |

La tabla `votes` tiene una restricción única sobre `voter_id`:

```text
UNIQUE(voter_id)
```

Esta restricción protege la regla de voto único incluso si llegan solicitudes
simultáneas.

## 6. Endpoints principales

### Autenticación

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/auth/login` | Login del administrador |
| `POST` | `/auth/voter-login` | Login del votante |

### Votantes

| Método | Ruta | Permiso |
|---|---|---|
| `POST` | `/voters` | Administrador |
| `GET` | `/voters` | Público |
| `GET` | `/voters/{id}` | Público |
| `DELETE` | `/voters/{id}` | Administrador |

### Candidatos

| Método | Ruta | Permiso |
|---|---|---|
| `POST` | `/candidates` | Administrador |
| `GET` | `/candidates` | Público |
| `GET` | `/candidates/{id}` | Público |
| `DELETE` | `/candidates/{id}` | Administrador |

### Votos

| Método | Ruta | Permiso |
|---|---|---|
| `POST` | `/votes` | Votante |
| `GET` | `/votes` | Público |
| `GET` | `/votes/statistics` | Público |

Los endpoints de lectura son públicos porque forman parte del alcance de la
prueba. En un sistema productivo, `GET /voters` debería protegerse o
anonimizar emails, y `GET /votes` debería protegerse o no exponer la relación
entre una persona y su candidato.

## 7. Flujo completo del sistema

### 7.1. Instalación

1. Descargar el repositorio.
2. Ejecutar `scripts/setup_windows.ps1`.
3. El script crea el entorno virtual.
4. Instala `requirements.txt`.
5. Crea `.env` a partir de `.env.example`.
6. La configuración queda en SQLite por defecto.

### 7.2. Inicio de servicios

En una terminal:

```powershell
.\scripts\start_backend.ps1
```

En otra terminal:

```powershell
.\scripts\start_frontend.ps1
```

Direcciones:

- Frontend: <http://127.0.0.1:5500>
- API: <http://127.0.0.1:8000>
- Swagger: <http://127.0.0.1:8000/docs>

### 7.3. Flujo administrativo

1. El administrador inicia sesión en `/auth/login`.
2. La API valida `ADMIN_USERNAME` y `ADMIN_PASSWORD`.
3. La API genera un JWT con `role=admin`.
4. El frontend guarda temporalmente el token en `sessionStorage`.
5. El administrador puede registrar y eliminar votantes y candidatos.
6. Cada operación protegida envía `Authorization: Bearer <token>`.

### 7.4. Flujo del votante

1. El administrador registra al votante con una contraseña.
2. El votante inicia sesión con email y contraseña.
3. La API verifica el hash almacenado.
4. La API genera un JWT con `role=voter` y `voter_id`.
5. El votante puede emitir únicamente su propio voto.
6. El backend compara el `voter_id` del token con el enviado en la solicitud.
7. Si no coinciden, responde `403 Forbidden`.

### 7.5. Flujo de emisión de voto

La función `cast_vote` ejecuta la siguiente secuencia dentro de una
transacción:

1. Buscar el votante.
2. Buscar el candidato.
3. Verificar que el votante no haya votado.
4. Crear el registro `Vote`.
5. Marcar `Voter.has_voted = True`.
6. Incrementar `Candidate.votes` directamente en la base:

```sql
votes = votes + 1
```

7. Confirmar con `commit`.
8. Si ocurre un error, ejecutar `rollback`.

El incremento directo en la base evita perder actualizaciones cuando dos
votantes diferentes seleccionan el mismo candidato al mismo tiempo.

## 8. Seguridad y autorización

### JWT

- Algoritmo: `HS256`.
- Expiración configurable con `JWT_EXPIRE_MINUTES`.
- El token contiene el sujeto, el rol y, para votantes, el `voter_id`.
- Los tokens inválidos o expirados producen `401`.
- Un rol válido pero insuficiente produce `403`.

### Contraseñas

Las contraseñas de votantes no se almacenan en texto plano. Se utiliza
`PBKDF2-HMAC-SHA256` con:

- Salt aleatorio de 16 bytes.
- 310.000 iteraciones.
- Comparación segura mediante `compare_digest`.

### Secreto de desarrollo

Si la aplicación inicia con el secreto:

```text
change-this-development-secret
```

emite una advertencia. Para un entorno real se deben cambiar los secretos y
credenciales en `.env`.

## 9. Validaciones de negocio

- Email de votante obligatorio y único.
- Contraseña de votante con mínimo de 8 caracteres.
- Nombres obligatorios y normalizados.
- Comparación de nombres sin distinguir:
  - Mayúsculas/minúsculas.
  - Tildes.
  - Formas Unicode equivalentes.
  - Espacios repetidos.
- Un votante no puede registrarse como candidato.
- Un candidato no puede registrarse como votante.
- El votante debe existir para votar.
- El candidato debe existir para votar.
- Un votante no puede votar dos veces.
- No se puede eliminar un votante que ya votó.
- No se puede eliminar un candidato que ya recibió votos.
- Las estadísticas evitan división por cero.

## 10. Códigos HTTP importantes

| Código | Significado |
|---:|---|
| `200` | Consulta o autenticación exitosa |
| `201` | Recurso creado |
| `204` | Recurso eliminado |
| `401` | Token ausente, inválido, expirado o credenciales incorrectas |
| `403` | Rol sin permisos o intento de votar por otra persona |
| `404` | Votante o candidato inexistente |
| `409` | Conflicto de negocio, duplicado o segundo voto |
| `422` | Datos de entrada inválidos |

## 11. Pruebas automatizadas

La suite actual contiene **15 pruebas** y cubre:

- Voto exitoso.
- Actualización de `has_voted`.
- Incremento del contador.
- Segundo voto del mismo votante.
- Candidato inexistente.
- Email duplicado.
- Cruce votante/candidato.
- Nombres con tildes.
- Nombres sin tildes.
- Unicode en forma NFD.
- Estadísticas sin votos.
- Login administrativo.
- Login inválido.
- Login de votante.
- Solicitud protegida sin token.
- Votante usando otro `voter_id`.
- Votante intentando crear votantes.
- Administrador intentando votar.
- Contraseña de votante incorrecta.

Ejecutar:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Las pruebas usan SQLite en memoria con `StaticPool`, por lo que no modifican
la base configurada para la aplicación.

## 12. Guion recomendado para la sustentación

### Introducción

> Desarrollé una API RESTful para un sistema de votaciones usando Python y
> FastAPI. El sistema administra votantes, candidatos y votos, y garantiza que
> cada votante pueda votar una sola vez. También implementé JWT con dos roles y
> un frontend para demostrar visualmente la API.

### Explicar la arquitectura

> Separé la aplicación en routers, schemas, modelos, autenticación y un
> servicio transaccional. Los routers reciben las solicitudes, los schemas
> validan los datos, los modelos representan la base y el servicio concentra
> la lógica crítica del voto.

### Explicar la regla de voto único

> La regla se protege en dos niveles. Primero, el código valida
> `has_voted`. Segundo, la base de datos tiene `UNIQUE(voter_id)` en la tabla
> de votos. Así se mantiene la integridad incluso ante solicitudes
> concurrentes.

### Explicar la transacción

> Emitir un voto no es solo insertar un registro. También se actualiza el
> estado del votante y el contador del candidato. Por eso las tres operaciones
> ocurren en una transacción y, si alguna falla, se ejecuta rollback.

### Explicar los roles

> El administrador administra la información. El votante solo puede emitir su
> propio voto. El backend no confía únicamente en el frontend: valida el rol y
> compara el `voter_id` del token con el `voter_id` de la solicitud.

### Explicar la elección de SQLite

> SQLite es la configuración predeterminada para que el evaluador pueda
> ejecutar el proyecto sin instalar infraestructura adicional. También dejé
> soporte para SQL Server mediante una variable de entorno, manteniendo la
> compatibilidad con el requerimiento original.

## 13. Demostración recomendada

Orden sugerido para mostrar el proyecto:

1. Abrir el README y explicar el objetivo.
2. Mostrar la estructura del proyecto.
3. Ejecutar las pruebas:

   ```powershell
   .\venv\Scripts\python.exe -m pytest -q
   ```

4. Abrir Swagger en `/docs`.
5. Ejecutar login de administrador.
6. Registrar un candidato.
7. Registrar un votante con contraseña.
8. Ejecutar login de votante.
9. Emitir un voto.
10. Intentar emitir un segundo voto y mostrar `409`.
11. Intentar votar con otro `voter_id` y mostrar `403`.
12. Consultar `/votes/statistics`.
13. Mostrar el frontend y sus vistas según el rol.
14. Mostrar las evidencias de `docs/ScreenShotsPostman/`.

## 14. Respuestas breves a preguntas frecuentes

### ¿Por qué FastAPI?

Porque permite construir APIs REST con tipado, validación automática mediante
Pydantic, documentación Swagger y buen rendimiento con ASGI.

### ¿Por qué separar routers y servicios?

Para evitar que los endpoints concentren toda la lógica. El router maneja HTTP
y el servicio maneja la operación transaccional del dominio.

### ¿Por qué usar una restricción única además de `has_voted`?

`has_voted` facilita la validación y la visualización del estado. La
restricción única funciona como garantía final de integridad en la base de
datos.

### ¿Qué ocurre si el candidato no existe?

La API responde `404` y no modifica al votante ni registra el voto.

### ¿Qué ocurre si falla una actualización durante el voto?

La transacción se revierte con `rollback`, evitando datos parciales.

### ¿Dónde se documenta la API?

En Swagger:

<http://127.0.0.1:8000/docs>

Y en los documentos de la carpeta `docs/`.

### ¿Qué mejoraría en producción?

- Proteger o anonimizar endpoints de lectura sensibles.
- Usar migraciones formales como Alembic.
- Gestionar secretos con un vault.
- Agregar logging estructurado y monitoreo.
- Ejecutar la API detrás de HTTPS.
- Añadir pruebas de concurrencia contra el motor de producción.

## 15. Material complementario

- [README](../README.md)
- [Guía del proyecto](GUIA_PROYECTO.md)
- [Instalación local](INSTALACION_LOCAL.md)
- [Verificación SQL](SQL_VERIFICACION.md)
- [Evidencias](ScreenShotsPostman/)
- [Especificación](../SPEC_Y_PLAN.md)
