"""ROTAS PROPOSITALMENTE VULNERÁVEIS — usadas apenas na demonstração FAIL.

NÃO usar em produção. Este arquivo é copiado para src/app/ pelo script
demo/aplicar-falhas.sh para provar que a pipeline bloqueia código inseguro.
"""

import os
import sqlite3
import subprocess

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/inseguro", tags=["demo-inseguro"])

# [SAST] Segredo hardcoded no código-fonte
API_KEY = "admin123"


@router.get("/busca")
def busca_insegura(q: str):
    # [SAST/DAST] SQL Injection: entrada do usuário concatenada na query
    conn = sqlite3.connect(os.getenv("DB_PATH", "tarefas.db"))
    sql = f"SELECT id, titulo FROM tarefas WHERE titulo = '{q}'"
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as e:
        # [DAST] Mensagem de erro do banco vazando para o cliente
        raise HTTPException(status_code=500, detail=f"SQLite error: {e}")
    return [dict(id=r[0], titulo=r[1]) for r in rows]


@router.get("/ping")
def ping(host: str):
    # [SAST/DAST] Command Injection: shell=True com entrada do usuário
    resultado = subprocess.run(
        f"ping -c 1 {host}", shell=True, capture_output=True, text=True
    )
    return {"saida": resultado.stdout + resultado.stderr}


@router.get("/calc")
def calc(expr: str):
    # [SAST] Execução de código arbitrário via eval()
    return {"resultado": eval(expr)}
