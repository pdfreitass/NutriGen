import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.database import criar_tabelas, fechar_conexao
from app.routers.diet import router as diet_router
from app.routers.auth import router as auth_router
from app.middleware.rate_limit import rate_limit_middleware
from app.middleware.request_id import request_id_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Executa tarefas de inicialização e desligamento da aplicação."""
    # Startup: criar tabelas no banco de dados (chamada síncrona)
    criar_tabelas()
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

# CORS - permitir todas origens em desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Servir o frontend estático (HTML, CSS, JS) como SPA
# html=True: qualquer rota não tratada pelos routers acima serve index.html
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
