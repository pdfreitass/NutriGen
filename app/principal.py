import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.banco_dados import criar_tabelas, fechar_conexao
from app.routers.dieta import router as diet_router
from app.routers.autenticacao import router as auth_router
from app.routers.admin import router as admin_router
from app.middleware.limite_taxa import rate_limit_middleware
from app.middleware.id_requisicao import request_id_middleware
from app.middleware.cabecalhos_seguranca import security_headers_middleware
from app.configuracao import APP_ENV
from app.configuracao_logs import setup_logging
from app.infrastructure.cost_tracker import cost_tracker
from app.configuracao import MAX_DAILY_COST_BRL

# Configurar logging estruturado (SPEC-013)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Executa tarefas de inicialização e desligamento da aplicação."""
    # Startup: criar tabelas no banco de dados (chamada síncrona)
    criar_tabelas()
    # Configurar limite de custo diário (SPEC-045)
    cost_tracker.configurar_limite(MAX_DAILY_COST_BRL)
    yield
    # Shutdown: fechar conexão com o banco (chamada síncrona)
    fechar_conexao()


app = FastAPI(
    title="NutriGen API",
    description=(
        "API para geração de planos alimentares personalizados com IA. "
        "O usuário descreve sua rotina em linguagem natural e recebe 3 planos distintos."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — restrito a localhost em desenvolvimento (SPEC-012)
_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",  # frontend dev server (se aplicável)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

# Security headers (SPEC-012)
@app.middleware("http")
async def security_headers_handler(request: Request, call_next):
    """Adiciona headers de segurança em todas as respostas."""
    response = await security_headers_middleware(request, call_next)
    return response

# Request ID — deve vir ANTES do rate limiting (SPEC-011)
@app.middleware("http")
async def request_id_handler(request: Request, call_next):
    """Injeta e propaga request_id para correlação de logs."""
    response = await request_id_middleware(request, call_next)
    return response

# Rate limiting (específico para /api/diet/generate)
@app.middleware("http")
async def rate_limit_handler(request: Request, call_next):
    """Aplica rate limiting antes de processar a requisição."""
    from fastapi import HTTPException
    try:
        await rate_limit_middleware(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
            headers=getattr(e, "headers", None),
        )
    return await call_next(request)

# ⚠️ ORDEM CRÍTICA: Routers DEVEM ser registrados ANTES do StaticFiles mount
# O mount em "/" com html=True captura qualquer rota não tratada (SPA fallback).
# Se um router for registrado depois do mount, seus endpoints nunca serão alcançados.
app.include_router(auth_router)
app.include_router(diet_router)
app.include_router(admin_router)

# Servir o frontend estático (HTML, CSS, JS) como SPA
# html=True: qualquer rota não tratada pelos routers acima serve index.html
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
