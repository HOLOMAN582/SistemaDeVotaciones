# Frontend del Sistema de Votaciones

Frontend independiente construido con HTML, CSS y JavaScript nativo. Consume la API FastAPI mediante HTTP/JSON y no se conecta directamente a SQL Server.

## Ejecución

Con el backend ejecutándose en `http://127.0.0.1:8000`, abrir otra terminal:

```powershell
cd frontend
..\venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1
```

Desde la raíz también puedes usar `.\scripts\start_frontend.ps1`.

Abrir <http://127.0.0.1:5500>.

## Funcionalidades

- Panel de estadísticas.
- Registro de votantes.
- Registro de candidatos.
- Emisión de votos.
- Tablas de votantes y candidatos.
- Mensajes de error provenientes de la API.
- Inicio de sesión JWT previo a cualquier vista.
- Pantallas separadas para administrador y votante.
- El administrador gestiona registros y el votante solo emite su propio voto.
- Diseño responsive.

## Credenciales de desarrollo

Por defecto, el entorno local usa:

```text
Usuario: admin
Contraseña: admin123
```

Estas credenciales se definen en `.env` mediante `ADMIN_USERNAME` y `ADMIN_PASSWORD`. Deben cambiarse antes de publicar un entorno real.

La URL de la API se configura en `js/api.js` mediante `API_BASE_URL`.
