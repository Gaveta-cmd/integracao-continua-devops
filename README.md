# Calculadora DevOps — Python

Projeto da disciplina Integração DevOps — CEUB 2026/2
Prof. Danilo Silva

## Equipe
- **Davi** — Operações / Infraestrutura
- **Adrian** — Desenvolvedor
- **Pedro Vitor** — Qualidade (QA)

## Tecnologias
- Python 3.11
- pytest (testes automatizados)
- flake8 (linter)
- GitHub Actions (pipeline CI)

## Como executar localmente

### Pré-requisitos
- Python 3.11+

### Instalação
```bash
pip install -r requirements-dev.txt
```

### Testes
```bash
pytest tests/ -v
```

### Linter
```bash
flake8 src/ tests/
```

## Estrutura do projeto
```
.
├── .github/
│   └── workflows/
│       └── ci.yml        # Pipeline de CI
├── src/
│   └── calculadora.py    # Código da calculadora
├── tests/
│   └── test_calculadora.py  # Testes automatizados
├── .flake8
├── .gitignore
├── requirements-dev.txt
└── README.md
```
