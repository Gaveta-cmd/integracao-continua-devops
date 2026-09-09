import json
import os

ARQUIVO_BANCO = "historico.json"


def carregar_historico(caminho=ARQUIVO_BANCO):
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as arquivo:
        try:
            return json.load(arquivo)
        except json.JSONDecodeError:
            return []


def salvar_historico(historico, caminho=ARQUIVO_BANCO):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(historico, arquivo, indent=4, ensure_ascii=False)


def salvar_operacao(operacao, a, b, resultado, caminho=ARQUIVO_BANCO):
    historico = carregar_historico(caminho)
    registro = {
        "operacao": operacao,
        "a": a,
        "b": b,
        "resultado": resultado
    }
    historico.append(registro)
    salvar_historico(historico, caminho)
    return registro


def limpar_historico(caminho=ARQUIVO_BANCO):
    if os.path.exists(caminho):
        os.remove(caminho)
