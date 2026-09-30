import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    # Recarrega o módulo para usar o banco temporário
    import importlib

    import app.main as main

    importlib.reload(main)
    from fastapi.testclient import TestClient

    return TestClient(main.app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_crud_tarefa(client):
    r = client.post("/tarefas", json={"titulo": "Estudar DevSecOps"})
    assert r.status_code == 201
    tarefa = r.json()
    assert tarefa["titulo"] == "Estudar DevSecOps"
    assert tarefa["concluida"] is False

    r = client.get(f"/tarefas/{tarefa['id']}")
    assert r.status_code == 200

    r = client.get("/tarefas")
    assert len(r.json()) == 1

    r = client.delete(f"/tarefas/{tarefa['id']}")
    assert r.status_code == 204
    assert client.get(f"/tarefas/{tarefa['id']}").status_code == 404


def test_busca_resiste_a_sql_injection(client):
    client.post("/tarefas", json={"titulo": "segredo"})
    client.post("/tarefas", json={"titulo": "publica"})

    r = client.get("/tarefas/busca", params={"q": "' OR '1'='1"})
    assert r.status_code == 200
    assert r.json() == []  # o payload é tratado como texto, não como SQL

    r = client.get("/tarefas/busca", params={"q": "pub"})
    assert [t["titulo"] for t in r.json()] == ["publica"]


def test_validacao_de_entrada(client):
    assert client.post("/tarefas", json={"titulo": ""}).status_code == 422
    assert client.post("/tarefas", json={"titulo": "x" * 201}).status_code == 422


def test_cabecalhos_de_seguranca(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]
