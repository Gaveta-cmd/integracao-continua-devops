"""Servidor HTTP da Calculadora DevOps (apenas biblioteca padrao).

Uso: python -m src.app

Variaveis de ambiente:
    PORT            porta (padrao 8080)
    HISTORICO_PATH  arquivo do historico (padrao historico.json)
    ADMIN_TOKEN     token exigido para limpar o historico (DELETE)
"""
import hmac
import html
import json
import math
import os
import socket
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src import banco, calculadora

try:
    import fcntl
except ImportError:  # Windows: trava apenas entre threads
    fcntl = None

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGINA = os.path.join(RAIZ, "frontend", "index.html")
LIMITE_CORPO = 10000
TRAVA_THREADS = threading.Lock()

OPERACOES = {
    "soma": calculadora.somar,
    "somar": calculadora.somar,
    "+": calculadora.somar,
    "subtracao": calculadora.subtrair,
    "subtrair": calculadora.subtrair,
    "-": calculadora.subtrair,
    "multiplicacao": calculadora.multiplicar,
    "multiplicar": calculadora.multiplicar,
    "*": calculadora.multiplicar,
    "divisao": calculadora.dividir,
    "dividir": calculadora.dividir,
    "/": calculadora.dividir,
}


def caminho_historico():
    return os.environ.get("HISTORICO_PATH", banco.ARQUIVO_BANCO)


def nome_pod():
    return os.environ.get("HOSTNAME") or socket.gethostname()


@contextmanager
def trava_historico():
    """Evita corrida entre threads e entre Pods que dividem o volume."""
    with TRAVA_THREADS:
        if fcntl is None:
            yield
            return
        pasta = os.path.dirname(os.path.abspath(caminho_historico()))
        os.makedirs(pasta, exist_ok=True)
        with open(caminho_historico() + ".lock", "w") as arquivo:
            fcntl.flock(arquivo, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(arquivo, fcntl.LOCK_UN)


def validar_numero(valor):
    ruim = isinstance(valor, bool) or not isinstance(valor, (int, float))
    if ruim or not math.isfinite(valor):
        raise ValueError("a e b devem ser numeros validos")
    return valor


def calcular(dados):
    if not isinstance(dados, dict):
        raise ValueError("corpo deve ser um objeto JSON")
    operacao = str(dados.get("operacao", "")).strip().lower()
    funcao = OPERACOES.get(operacao)
    if funcao is None:
        raise ValueError("operacao invalida")
    a = validar_numero(dados.get("a"))
    b = validar_numero(dados.get("b"))
    resultado = funcao(a, b)
    with trava_historico():
        registro = banco.salvar_operacao(
            operacao, a, b, resultado, caminho_historico()
        )
    registro["pod"] = nome_pod()
    return registro


def pagina_inicial():
    with open(PAGINA, "r", encoding="utf-8") as arquivo:
        conteudo = arquivo.read()
    selo = (
        '<div style="position:fixed;bottom:8px;right:8px;'
        "padding:4px 10px;background:#1a1a24;color:#8a8aa0;"
        'font:12px monospace;border-radius:8px">'
        "Atendido pelo Pod: " + html.escape(nome_pod()) + "</div>"
    )
    return conteudo.replace("</body>", selo + "</body>", 1)


class Handler(BaseHTTPRequestHandler):
    server_version = "CalculadoraDevOps"

    def _responder(self, status, corpo, tipo):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, status, dados):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self._responder(status, corpo, "application/json; charset=utf-8")

    def _ler_json(self):
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Content-Length invalido")
        if tamanho <= 0 or tamanho > LIMITE_CORPO:
            raise ValueError("corpo ausente ou grande demais")
        try:
            return json.loads(self.rfile.read(tamanho))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("JSON invalido")

    def _caminho(self):
        return self.path.split("?", 1)[0]

    def do_GET(self):
        caminho = self._caminho()
        if caminho == "/healthz":
            self._responder(200, b"ok", "text/plain; charset=utf-8")
        elif caminho == "/":
            try:
                corpo = pagina_inicial().encode("utf-8")
            except FileNotFoundError:
                self._json(404, {"erro": "frontend nao encontrado"})
                return
            self._responder(200, corpo, "text/html; charset=utf-8")
        elif caminho == "/api/info":
            self._json(200, {"pod": nome_pod()})
        elif caminho == "/api/historico":
            with trava_historico():
                historico = banco.carregar_historico(caminho_historico())
            self._json(200, historico)
        else:
            self._json(404, {"erro": "nao encontrado"})

    def do_POST(self):
        if self._caminho() != "/api/calcular":
            self._json(404, {"erro": "nao encontrado"})
            return
        try:
            registro = calcular(self._ler_json())
        except ValueError as erro:
            self._json(400, {"erro": str(erro)})
            return
        self._json(200, registro)

    def do_DELETE(self):
        if self._caminho() != "/api/historico":
            self._json(404, {"erro": "nao encontrado"})
            return
        esperado = os.environ.get("ADMIN_TOKEN", "")
        recebido = self.headers.get("Authorization", "")
        valido = esperado and hmac.compare_digest(
            recebido, "Bearer " + esperado
        )
        if not valido:
            self._json(401, {"erro": "nao autorizado"})
            return
        with trava_historico():
            banco.limpar_historico(caminho_historico())
        self._json(200, {"ok": True})


def main():
    porta = int(os.environ.get("PORT", "8080"))
    servidor = ThreadingHTTPServer(("0.0.0.0", porta), Handler)
    print("Servidor ouvindo na porta", porta, flush=True)
    servidor.serve_forever()


if __name__ == "__main__":
    main()