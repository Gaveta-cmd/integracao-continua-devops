import pytest

from src.calculadora import dividir, multiplicar, somar, subtrair


# ■■ Testes de Soma ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def test_somar_positivos():
    assert somar(2, 3) == 5


def test_somar_negativos():
    assert somar(-1, -4) == -5


def test_somar_com_zero():
    assert somar(0, 7) == 7


# ■■ Testes de Subtracao ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def test_subtrair_positivos():
    assert subtrair(10, 4) == 6


def test_subtrair_resultado_negativo():
    assert subtrair(3, 8) == -5


# ■■ Testes de Multiplicacao ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def test_multiplicar_positivos():
    assert multiplicar(3, 4) == 12


def test_multiplicar_por_zero():
    assert multiplicar(5, 0) == 0


def test_multiplicar_negativos():
    assert multiplicar(-2, 3) == -6


# ■■ Testes de Divisao ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def test_dividir_positivos():
    assert dividir(10, 2) == 5


def test_dividir_resultado_decimal():
    assert dividir(7, 2) == 3.5


def test_dividir_por_zero_lanca_excecao():
    with pytest.raises(ValueError):
        dividir(5, 0)