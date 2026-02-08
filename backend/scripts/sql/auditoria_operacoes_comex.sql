-- Auditoria: operacoes_comex e empresas importadoras/exportadoras
-- Executar no PostgreSQL (conectar ao banco do projeto e rodar cada bloco).

-- 1) Totais gerais
SELECT COUNT(*) AS total_registros FROM operacoes_comex;

SELECT COUNT(DISTINCT razao_social_importador) AS total_importadoras_distintas
FROM operacoes_comex
WHERE razao_social_importador IS NOT NULL AND TRIM(razao_social_importador) <> '';

SELECT COUNT(DISTINCT razao_social_exportador) AS total_exportadoras_distintas
FROM operacoes_comex
WHERE razao_social_exportador IS NOT NULL AND TRIM(razao_social_exportador) <> '';

SELECT COUNT(*) AS registros_sem_importador
FROM operacoes_comex
WHERE razao_social_importador IS NULL OR TRIM(razao_social_importador) = '';

SELECT COUNT(*) AS registros_sem_exportador
FROM operacoes_comex
WHERE razao_social_exportador IS NULL OR TRIM(razao_social_exportador) = '';

-- 2) Top 10 importadoras (por operações)
SELECT razao_social_importador AS nome, COUNT(*) AS total_operacoes, ROUND(SUM(valor_fob)::numeric, 2) AS valor_total_fob
FROM operacoes_comex
WHERE razao_social_importador IS NOT NULL AND TRIM(razao_social_importador) <> ''
GROUP BY razao_social_importador
ORDER BY total_operacoes DESC
LIMIT 10;

-- 3) Top 10 exportadoras (por operações)
SELECT razao_social_exportador AS nome, COUNT(*) AS total_operacoes, ROUND(SUM(valor_fob)::numeric, 2) AS valor_total_fob
FROM operacoes_comex
WHERE razao_social_exportador IS NOT NULL AND TRIM(razao_social_exportador) <> ''
GROUP BY razao_social_exportador
ORDER BY total_operacoes DESC
LIMIT 10;

-- 4) Teste de filtro por empresa (ex.: nome contém VALE)
SELECT COUNT(*) AS operacoes, ROUND(SUM(valor_fob)::numeric, 2) AS valor_total
FROM operacoes_comex
WHERE razao_social_importador ILIKE '%VALE%';
