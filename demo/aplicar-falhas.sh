#!/usr/bin/env bash
# Injeta falhas propositais na aplicação para demonstrar a pipeline em FAIL.
#
# Uso (sempre em uma branch separada, nunca na main):
#   git checkout -b demo/vulneravel
#   bash demo/aplicar-falhas.sh
#   git add -A && git commit -m "demo: injeta vulnerabilidades" && git push -u origin demo/vulneravel
#   -> abra um Pull Request para a main e veja a pipeline falhar.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1) Código inseguro (SAST + DAST)
cp demo/rotas_inseguras.py src/app/rotas_inseguras.py
if ! grep -q "rotas_inseguras" src/app/main.py; then
  cat >> src/app/main.py <<'EOF'


# --- DEMO: rotas vulneráveis (remover para voltar ao PASS) ---
from app.rotas_inseguras import router as rotas_inseguras  # noqa: E402

app.include_router(rotas_inseguras)
EOF
fi

# 2) Dependência com CVEs conhecidas (SCA + Trivy)
grep -q "^requests==" requirements.txt || echo "requests==2.19.1" >> requirements.txt

echo "Falhas aplicadas:"
echo "  - src/app/rotas_inseguras.py (SQLi, command injection, eval, segredo hardcoded)"
echo "  - requirements.txt: requests==2.19.1 (CVE-2018-18074, CVE-2023-32681, CVE-2024-35195)"
