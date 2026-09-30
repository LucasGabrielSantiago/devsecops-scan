"""API de Tarefas — aplicação alvo da pipeline DevSecOps.

Aplicação propositalmente simples (CRUD de tarefas em SQLite) usada para
demonstrar SAST, SCA e DAST rodando automaticamente no GitHub Actions.
"""

import os
import sqlite3
from contextlib import closing

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

DB_PATH = os.getenv("DB_PATH", "tarefas.db")

app = FastAPI(
    title="API de Tarefas",
    description="Aplicação de exemplo para a pipeline DevSecOps (SAST + SCA + DAST).",
    version="1.0.0",
)
# OpenAPI 3.0.3 garante compatibilidade com o importador do OWASP ZAP (DAST).
app.openapi_version = "3.0.3"


# --------------------------------------------------------------------------- #
# Banco de dados
# --------------------------------------------------------------------------- #
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                concluida INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


init_db()


# --------------------------------------------------------------------------- #
# Cabeçalhos de segurança (mitigam alertas passivos do OWASP ZAP)
# --------------------------------------------------------------------------- #
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cache-Control": "no-store",
}

# A documentação interativa (/docs) precisa carregar JS/CSS de CDN,
# então recebe uma CSP menos restritiva que o restante da API.
DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "frame-ancestors 'none'"
)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    if request.url.path in ("/docs", "/redoc"):
        response.headers["Content-Security-Policy"] = DOCS_CSP
    return response


# --------------------------------------------------------------------------- #
# Modelos
# --------------------------------------------------------------------------- #
class TarefaIn(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    concluida: bool = False


class TarefaOut(TarefaIn):
    id: int


def _to_out(row: sqlite3.Row) -> TarefaOut:
    return TarefaOut(id=row["id"], titulo=row["titulo"], concluida=bool(row["concluida"]))


# --------------------------------------------------------------------------- #
# Rotas
# --------------------------------------------------------------------------- #
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tarefas", response_model=list[TarefaOut])
def listar_tarefas() -> list[TarefaOut]:
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT id, titulo, concluida FROM tarefas ORDER BY id").fetchall()
    return [_to_out(r) for r in rows]


@app.get("/tarefas/busca", response_model=list[TarefaOut])
def buscar_tarefas(q: str) -> list[TarefaOut]:
    # Consulta parametrizada: o valor de "q" nunca é concatenado ao SQL.
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT id, titulo, concluida FROM tarefas WHERE titulo LIKE ? ORDER BY id",
            (f"%{q}%",),
        ).fetchall()
    return [_to_out(r) for r in rows]


@app.get("/tarefas/{tarefa_id}", response_model=TarefaOut)
def obter_tarefa(tarefa_id: int) -> TarefaOut:
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT id, titulo, concluida FROM tarefas WHERE id = ?", (tarefa_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return _to_out(row)


@app.post("/tarefas", response_model=TarefaOut, status_code=201)
def criar_tarefa(tarefa: TarefaIn) -> TarefaOut:
    with closing(get_conn()) as conn:
        cur = conn.execute(
            "INSERT INTO tarefas (titulo, concluida) VALUES (?, ?)",
            (tarefa.titulo, int(tarefa.concluida)),
        )
        conn.commit()
        novo_id = cur.lastrowid
    return TarefaOut(id=novo_id, **tarefa.model_dump())


@app.delete("/tarefas/{tarefa_id}", status_code=204)
def remover_tarefa(tarefa_id: int) -> Response:
    with closing(get_conn()) as conn:
        cur = conn.execute("DELETE FROM tarefas WHERE id = ?", (tarefa_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return Response(status_code=204)
