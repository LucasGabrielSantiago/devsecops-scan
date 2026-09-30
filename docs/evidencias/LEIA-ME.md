# Evidências

Salve aqui os prints referenciados no README (nomes exatos):

| Arquivo | O que capturar |
|---|---|
| `01-pipeline-fail.png` | Aba **Actions** → execução do PR `demo/vulneravel` → grafo dos jobs com o resultado em vermelho |
| `02-semgrep-findings.png` | Summary da execução (seção "SAST — Semgrep") **ou** aba **Security → Code scanning** |
| `03-pip-audit.png` | Summary da execução (seção "SCA — pip-audit") com a tabela de CVEs |
| `04-zap-report.png` | Artifact `relatorio-dast-zap` → abrir `report_html.html` → alerta *Remote OS Command Injection* |
| `05-pipeline-pass.png` | Execução da `main` com todos os jobs verdes e a tabela "Resultado" toda PASS |
