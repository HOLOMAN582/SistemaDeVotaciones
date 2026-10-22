# Consultas SQL Server para verificar la API

Este documento contiene consultas de solo lectura para comprobar el esquema, los datos y las reglas principales de la API. Ejecutarlas en SQL Server Management Studio, Azure Data Studio o con `sqlcmd`.

## 1. Seleccionar la base de datos

```sql
USE VotacionesDB;
GO

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    SYSDATETIME() AS checked_at;
GO
```

Con `sqlcmd` desde PowerShell:

```powershell
sqlcmd -S localhost -E -C -d VotacionesDB
```

## 2. Verificar que existen las tablas

```sql
SELECT
    TABLE_SCHEMA,
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_SCHEMA, TABLE_NAME;
GO
```

Resultado esperado: `candidates`, `voters` y `votes`.

## 3. Verificar columnas y tipos

```sql
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('voters', 'candidates', 'votes')
ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO
```

## 4. Verificar claves primarias, foráneas y restricciones

### Claves primarias y foráneas

```sql
SELECT
    fk.name AS foreign_key_name,
    OBJECT_SCHEMA_NAME(fk.parent_object_id) AS source_schema,
    OBJECT_NAME(fk.parent_object_id) AS source_table,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS source_column,
    OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS target_schema,
    OBJECT_NAME(fk.referenced_object_id) AS target_table,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS target_column
FROM sys.foreign_keys AS fk
INNER JOIN sys.foreign_key_columns AS fkc
    ON fk.object_id = fkc.constraint_object_id
WHERE OBJECT_NAME(fk.parent_object_id) IN ('voters', 'candidates', 'votes')
ORDER BY source_table, foreign_key_name;
GO
```

### Restricciones únicas

```sql
SELECT
    t.name AS table_name,
    i.name AS constraint_name,
    c.name AS column_name,
    i.is_unique,
    i.is_unique_constraint
FROM sys.indexes AS i
INNER JOIN sys.tables AS t ON i.object_id = t.object_id
INNER JOIN sys.index_columns AS ic
    ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns AS c
    ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE t.name IN ('voters', 'candidates', 'votes')
  AND i.is_unique = 1
ORDER BY t.name, i.name;
GO
```

Debe aparecer una restricción única para `voters.email` y otra para `votes.voter_id`.

## 5. Consultar los datos actuales

```sql
SELECT id, name, email, has_voted
FROM dbo.voters
ORDER BY id;
GO

SELECT id, name, party, votes
FROM dbo.candidates
ORDER BY id;
GO

SELECT id, voter_id, candidate_id
FROM dbo.votes
ORDER BY id;
GO
```

## 6. Verificar integridad de los votos

### Cada voto apunta a entidades existentes

```sql
SELECT v.*
FROM dbo.votes AS v
LEFT JOIN dbo.voters AS vo ON vo.id = v.voter_id
LEFT JOIN dbo.candidates AS ca ON ca.id = v.candidate_id
WHERE vo.id IS NULL OR ca.id IS NULL;
GO
```

Resultado esperado: cero filas.

### Un votante no tiene más de un voto

```sql
SELECT
    voter_id,
    COUNT(*) AS vote_count
FROM dbo.votes
GROUP BY voter_id
HAVING COUNT(*) > 1;
GO
```

Resultado esperado: cero filas. La restricción `UNIQUE(voter_id)` debe impedir duplicados.

### Votantes marcados correctamente

```sql
SELECT
    vo.id,
    vo.name,
    vo.has_voted,
    COUNT(v.id) AS votes_in_table
FROM dbo.voters AS vo
LEFT JOIN dbo.votes AS v ON v.voter_id = vo.id
GROUP BY vo.id, vo.name, vo.has_voted
HAVING (vo.has_voted = 1 AND COUNT(v.id) <> 1)
    OR (vo.has_voted = 0 AND COUNT(v.id) <> 0);
GO
```

Resultado esperado: cero filas.

### Conteo almacenado del candidato frente a la tabla de votos

```sql
SELECT
    ca.id AS candidate_id,
    ca.name,
    ca.votes AS stored_votes,
    COUNT(v.id) AS calculated_votes
FROM dbo.candidates AS ca
LEFT JOIN dbo.votes AS v ON v.candidate_id = ca.id
GROUP BY ca.id, ca.name, ca.votes
HAVING ca.votes <> COUNT(v.id);
GO
```

Resultado esperado: cero filas.

## 7. Consulta equivalente a las estadísticas de la API

```sql
DECLARE @total_votes INT =
(
    SELECT COUNT(*)
    FROM dbo.votes
);

SELECT
    ca.id AS candidate_id,
    ca.name AS candidate_name,
    ca.votes,
    CAST(
        CASE
            WHEN @total_votes = 0 THEN 0
            ELSE ca.votes * 100.0 / @total_votes
        END
        AS DECIMAL(10, 2)
    ) AS percentage
FROM dbo.candidates AS ca
ORDER BY ca.id;

SELECT
    @total_votes AS total_votes,
    (
        SELECT COUNT(*)
        FROM dbo.voters
        WHERE has_voted = 1
    ) AS voters_who_voted;
GO
```

## 8. Detectar nombres repetidos o cruces votante-candidato

La API compara nombres ignorando mayúsculas/minúsculas y espacios repetidos al registrarlos. Esta consulta detecta coincidencias directas:

```sql
SELECT
    vo.id AS voter_id,
    vo.name AS voter_name,
    ca.id AS candidate_id,
    ca.name AS candidate_name
FROM dbo.voters AS vo
INNER JOIN dbo.candidates AS ca
    ON LOWER(LTRIM(RTRIM(vo.name))) = LOWER(LTRIM(RTRIM(ca.name)));
GO
```

Resultado esperado: cero filas.

## 9. Verificar eliminaciones permitidas

Estos candidatos no tienen votos y, por tanto, la API permite eliminarlos:

```sql
SELECT ca.id, ca.name
FROM dbo.candidates AS ca
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.votes AS v
    WHERE v.candidate_id = ca.id
);
GO
```

Estos candidatos tienen votos y la API debe responder `409 Conflict` si se intenta eliminarlos:

```sql
SELECT ca.id, ca.name, COUNT(v.id) AS vote_count
FROM dbo.candidates AS ca
INNER JOIN dbo.votes AS v ON v.candidate_id = ca.id
GROUP BY ca.id, ca.name;
GO
```

La misma verificación para votantes:

```sql
SELECT vo.id, vo.name, COUNT(v.id) AS vote_count
FROM dbo.voters AS vo
INNER JOIN dbo.votes AS v ON v.voter_id = vo.id
GROUP BY vo.id, vo.name;
GO
```

## 10. Verificar una transacción sin modificar datos

Este bloque permite revisar el efecto de una operación dentro de una transacción y deshacerla inmediatamente:

```sql
BEGIN TRANSACTION;

SELECT
    vo.id AS voter_id,
    vo.has_voted,
    ca.id AS candidate_id,
    ca.votes
FROM dbo.voters AS vo
CROSS JOIN dbo.candidates AS ca
WHERE vo.has_voted = 0;

ROLLBACK TRANSACTION;
GO
```

No ejecutar `COMMIT` en este bloque: la API es la responsable de registrar votos mediante su transacción atómica.

## 11. Consultas rápidas para diagnóstico

```sql
SELECT COUNT(*) AS total_voters FROM dbo.voters;
SELECT COUNT(*) AS total_candidates FROM dbo.candidates;
SELECT COUNT(*) AS total_votes FROM dbo.votes;
SELECT COUNT(*) AS voters_who_voted FROM dbo.voters WHERE has_voted = 1;
GO

SELECT TOP (10)
    v.id,
    vo.name AS voter_name,
    ca.name AS candidate_name
FROM dbo.votes AS v
INNER JOIN dbo.voters AS vo ON vo.id = v.voter_id
INNER JOIN dbo.candidates AS ca ON ca.id = v.candidate_id
ORDER BY v.id DESC;
GO
```

## 12. Mantenimiento excepcional

Estas instrucciones son únicamente para limpiar datos de desarrollo. No ejecutarlas en una base de datos de entrega o producción sin respaldo:

```sql
-- DELETE FROM dbo.votes;
-- UPDATE dbo.voters SET has_voted = 0;
-- UPDATE dbo.candidates SET votes = 0;
```

Para eliminar todos los datos respetando el orden de las relaciones:

```sql
-- BEGIN TRANSACTION;
-- DELETE FROM dbo.votes;
-- UPDATE dbo.voters SET has_voted = 0;
-- UPDATE dbo.candidates SET votes = 0;
-- COMMIT TRANSACTION;
```
