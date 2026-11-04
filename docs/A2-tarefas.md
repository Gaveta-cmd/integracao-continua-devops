# A2 — Divisao de tarefas da equipe (IaC e CD)

Prazo da avaliacao A2: **04/11/2026**. Cada pessoa entrega a sua parte numa
branch propria e abre Pull Request para `main` (a `main` exige PR, 1
aprovacao e o check `build-and-test`).

| Entrega da A2 | Quem | Onde |
|---|---|---|
| Dockerfile | Davi | `Dockerfile`, `.dockerignore` |
| Manifestos Kubernetes | Davi | `k8s/` |
| Pipeline de CD (GHCR + deploy simulado) | Davi | `.github/workflows/cd.yml` |
| Segredos (GitHub Secrets) | Davi | secret `ADMIN_TOKEN` no GitHub |
| **Servidor da aplicacao (HTTP)** | **Adrian** | `src/app.py` |
| **Testes do servidor** | **Pedro Vitor** | `tests/test_app.py` |
| **Evidencias: autocura, escala e rollback** | **Pedro Vitor** | `docs/evidencias/` |
| README (arquitetura e execucao) | todos | `README.md` |

## Adrian — `src/app.py`

O Dockerfile e os manifestos ja assumem este contrato. Nao precisa mexer em
`calculadora.py` nem em `banco.py` (apenas usar).

- Rodar com `python -m src.app`, usando **apenas a biblioteca padrao**
  (`http.server`), porta `PORT` (padrao `8080`), escutando em `0.0.0.0`.
- `GET /healthz` -> `200` com texto `ok` (usado pelas probes do Kubernetes).
- `GET /` -> serve `frontend/index.html`.
- `GET /api/historico` -> lista do historico em JSON (`banco.carregar_historico`).
- `POST /api/calcular` com `{"operacao","a","b"}` -> calcula com
  `calculadora.py`, grava com `banco.salvar_operacao` e devolve o registro.
  Divisao por zero -> `400` com mensagem de erro.
- `DELETE /api/historico` -> limpa o historico, **so** se o cabecalho
  `Authorization: Bearer <ADMIN_TOKEN>` bater com a variavel de ambiente
  `ADMIN_TOKEN`; senao `401`.
- O arquivo do historico vem da variavel `HISTORICO_PATH`
  (padrao `/data/historico.json`; localmente pode ser `historico.json`).
- Mostrar na pagina (ou em `GET /api/info`) o nome do Pod: variavel
  `HOSTNAME`. A atividade da Aula 12 usa isso para ver o balanceamento
  ("Atendido pelo Pod: ...").
- Atencao: 3 replicas escrevem no mesmo arquivo. Grave de forma segura
  (escrever em arquivo temporario e `os.replace`, ou travar o arquivo).
- Passar no `flake8 src/ tests/` (limite de 79 colunas).

## Pedro Vitor — testes e evidencias

1. `tests/test_app.py`: testar `/healthz`, `/api/historico`, `/api/calcular`
   (soma, divisao por zero -> 400) e `DELETE` com e sem token. Use
   `HISTORICO_PATH` apontando para um arquivo temporario.
2. Depois que o cluster estiver de pe (ver `docs/ROLLBACK.md` e o roteiro
   abaixo), rodar e **registrar com prints** em `docs/evidencias/`:
   - **Autocura:** `kubectl delete pod <um-pod>` e o cluster recria; 3
     replicas de volta.
   - **Escala:** `kubectl scale deployment/calculadora-deployment --replicas=5`
     e atualizar a pagina vendo pods diferentes respondendo.
   - **Rollback:** seguir `docs/ROLLBACK.md` (versao `1.1.0` com defeito ->
     volta para `1.0.0`).

## Roteiro local (Docker Desktop com Kubernetes ligado)

```bash
docker build -t calculadora:1.0.0 .
kubectl create secret generic app-secret --from-literal=ADMIN_TOKEN='troque-isto'
kubectl apply -f k8s/
kubectl set image deployment/calculadora-deployment calculadora=calculadora:1.0.0
kubectl get pods -w
# abrir http://localhost:30080
```

Limpeza ao terminar: `kubectl delete -f k8s/` e
`kubectl delete secret app-secret`.
