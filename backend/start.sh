#!/bin/bash
set -e

echo "🚀 Iniciando aplicação..."

# Executar migrations
echo "📊 Executando migrations..."
cd /opt/render/project/src/backend
python -m alembic upgrade head || {
    echo "⚠️ Migration falhou, mas continuando..."
}

# Iniciar servidor
echo "🌐 Iniciando servidor FastAPI..."
python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
