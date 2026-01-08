# Dockerfile para Comex Backend
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de requirements
COPY backend/requirements-render-ultra-minimal.txt /app/backend/requirements-render-ultra-minimal.txt

# Instalar dependências
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r backend/requirements-render-ultra-minimal.txt

# Copiar código da aplicação
COPY backend /app/backend

# Copiar config.py se existir na raiz
COPY config.py /app/ 2>/dev/null || echo "config.py não encontrado na raiz, usando do backend"

# Criar diretório de dados se não existir
RUN mkdir -p /app/backend/data

# Variável de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expor porta
EXPOSE 8000

# Comando de start
WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

