# ================================================================
# MAIN.PY - INTEGRAÇÃO FASTAPI COM ENDPOINTS DE IMPORTAÇÃO
# ================================================================

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Importar os endpoints de importação
from routes.import_excel import app as import_app
from routes.validacao import router as validacao_router

# Criar instância FastAPI
app = FastAPI(
    title="COMEX Backend",
    description="API para gestão de operações comerciais (importação/exportação)",
    version="1.0.0"
)

# ================================================================
# CORS CONFIGURATION
# ================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, defina domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# CONFIGURAR LOGGING
# ================================================================
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="7 days",
    level="INFO"
)

# ================================================================
# INCLUIR ROTAS DE IMPORTAÇÃO
# ================================================================
# Os endpoints abaixo estarão disponíveis:
# POST /api/upload-e-importar-excel
# POST /api/upload-e-importar-cnae
# GET /validar-sistema

app.include_router(
    import_app,
    prefix="/api",
    tags=["importacao"]
)

app.include_router(
    validacao_router,
    tags=["sistema"]
)

# ================================================================
# HEALTH CHECK
# ================================================================
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "comex-backend",
        "version": "1.0.0"
    }

# ================================================================
# ROOT
# ================================================================
@app.get("/")
def root():
    return {
        "message": "COMEX Backend API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
