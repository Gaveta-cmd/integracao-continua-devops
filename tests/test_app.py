import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from src import app

TOKEN = "token-de-teste"


@pytest.fixture
def servidor(tmp_path, monkeypatch):
    monkeypatch.setenv("HISTORICO_PATH", str(tmp_path / "historico.json"))
    monkeypatch.setenv("ADMIN_TOKEN", TOKEN)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield "http://127.0.0.1:%d" % httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


def chamar(base, metodo, caminho, corpo=None, cabecalhos=None):
    dados = None
    if corpo is not None:
        dados = json.dumps(corpo).encode("utf-8")
    pedido = urllib.request.Request(
        base + caminho, data=dados, method=metodo, headers=cabecalhos or {}
    )
    if dados is not None:
        pedido.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(pedido, timeout=5) as resposta:
            return resposta.status, resposta.read().decode("utf-8")
    except urllib.error.HTTPError as erro:
        return erro.code, erro.read().decode("utf-8")


def test_healthz_responde_ok(servidor):
    status, corpo = chamar(servidor, "GET", "/healthz")
    assert status == 200
    assert corpo == "ok"


def test_historico_comeca_vazio(servidor):
    status, corpo = chamar(servidor, "GET", "/api/historico")
    assert status == 200
    assert json.loads(corpo) == []


def test_soma_2_mais_3_da_5_e_grava_no_historico(servidor):
    conta = {"operacao": "soma", "a": 2, "b": 3}
    status, corpo = chamar(servidor, "POST", "/api/calcular", conta)
    assert status == 200
    assert json.loads(corpo)["resultado"] == 5

    status, corpo = chamar(servidor, "GET", "/api/historico")
    historico = json.loads(corpo)
    assert len(historico) == 1
    assert historico[0]["resultado"] == 5


def test_divisao_por_zero_da_erro_400(servidor):
    conta = {"operacao": "dividir", "a": 1, "b": 0}
    status, corpo = chamar(servidor, "POST", "/api/calcular", conta)
    assert status == 400
    assert "erro" in json.loads(corpo)


def test_operacao_invalida_da_erro_400(servidor):
    conta = {"operacao": "potencia", "a": 2, "b": 3}
    status, _ = chamar(servidor, "POST", "/api/calcular", conta)
    assert status == 400


def test_apagar_historico_sem_token_da_401(servidor):
    status, _ = chamar(servidor, "DELETE", "/api/historico")
    assert status == 401


def test_apagar_historico_com_token_errado_da_401(servidor):
    cabecalhos = {"Authorization": "Bearer token-errado"}
    status, _ = chamar(
        servidor, "DELETE", "/api/historico", cabecalhos=cabecalhos
    )
    assert status == 401


def test_apagar_historico_com_token_certo_limpa(servidor):
    conta = {"operacao": "soma", "a": 1, "b": 1}
    chamar(servidor, "POST", "/api/calcular", conta)

    cabecalhos = {"Authorization": "Bearer " + TOKEN}
    status, _ = chamar(
        servidor, "DELETE", "/api/historico", cabecalhos=cabecalhos
    )
    assert status == 200

    _, corpo = chamar(servidor, "GET", "/api/historico")
    assert json.loads(corpo) == []
