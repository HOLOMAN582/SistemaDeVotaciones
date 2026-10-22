# Instalación y ejecución local

Esta guía permite ejecutar el proyecto desde una copia nueva del repositorio,
sin depender de rutas, usuarios o entornos virtuales de otra máquina.

## 1. Requisitos

- Windows 10/11.
- Python 3.11 o superior instalado desde [python.org](https://www.python.org/downloads/).
- Git, si el proyecto se descargará desde GitHub.
- SQL Server y ODBC Driver 18 únicamente si se desea usar SQL Server en vez del
  modo SQLite local.

Durante la instalación de Python activa la opción **Add Python to PATH**.

## 2. Descargar el proyecto

Desde PowerShell:

```powershell
git clone <URL_DEL_REPOSITORIO>
cd EntregableNewInntech
```

Si se recibió un archivo ZIP, descomprímelo y entra a la carpeta que contiene
`README.md`, `app` y `frontend`.

## 3. Ejecutar la instalación automática

Desde la raíz del proyecto:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup_windows.ps1
```

El script:

1. Crea `venv` dentro de la copia local.
2. Instala las dependencias desde `requirements.txt`.
3. Crea `.env` usando `.env.example`.
4. Deja lista la aplicación para iniciar.

No se copia `venv` desde otra máquina. Cada equipo crea su propio entorno.

## 4. Base de datos local predeterminada

La configuración inicial usa SQLite:

```env
DATABASE_URL=sqlite:///./votaciones.db
```

No hay que crear tablas manualmente. FastAPI las crea al iniciar y el archivo
`votaciones.db` se genera en la raíz del proyecto. Este archivo es local y no
debe publicarse.

Credenciales iniciales del administrador:

```text
Usuario: admin
Contraseña: admin123
```

Antes de compartir o publicar una instalación real, cambia esos valores y
`JWT_SECRET_KEY` en `.env`.

## 5. Iniciar backend y frontend

Abre dos terminales PowerShell en la raíz del proyecto.

Terminal 1:

```powershell
.\scripts\start_backend.ps1
```

Terminal 2:

```powershell
.\scripts\start_frontend.ps1
```

Direcciones:

- Frontend: <http://127.0.0.1:5500>
- Swagger: <http://127.0.0.1:8000/docs>
- API: <http://127.0.0.1:8000>

El login se muestra antes de cargar cualquier información. Usa las credenciales
del administrador para crear votantes y candidatos.

## 6. Usar SQL Server en lugar de SQLite

Esta opción conserva la compatibilidad con la prueba técnica original.

1. Instala SQL Server y ODBC Driver 18 for SQL Server.
2. Crea la base:

```sql
CREATE DATABASE VotacionesDB;
```

3. Edita `.env` y reemplaza `DATABASE_URL` por una cadena válida para ese equipo:

```env
DATABASE_URL=mssql+pyodbc://@localhost/VotacionesDB?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes
```

4. Reinicia el backend. Las tablas se crean automáticamente.

La cadena no contiene rutas de Windows ni nombres de usuario fijos. Para
autenticación SQL Server, usa la cadena correspondiente a las credenciales y
servidor de la máquina.

## 7. Ejecutar pruebas

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Las pruebas usan una base SQLite temporal y no modifican la base configurada
en `.env`.

## 8. Problemas frecuentes

### PowerShell no permite ejecutar scripts

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### El puerto está ocupado

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
Get-NetTCPConnection -LocalPort 5500 -State Listen
```

Cierra el proceso identificado o usa otro puerto actualizando también
`frontend/js/api.js` si cambias el puerto del backend.

### El frontend no conecta

Confirma que el backend esté activo en `http://127.0.0.1:8000` y que el
frontend se haya iniciado con `start_frontend.ps1`.
