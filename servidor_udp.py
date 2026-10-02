import json
import math
import socket
import time

PORTA = 1200
LIMITE = 1024
ITERACOES_PADRAO = 1_000_000
ITERACOES_MAXIMAS = 5_000_000


def medir_pi(texto):
    partes = texto.split()
    if len(partes) == 1:
        iteracoes = ITERACOES_PADRAO
    elif len(partes) == 2 and partes[1].isdigit():
        iteracoes = int(partes[1])
    else:
        iteracoes = 0
    if not 1 <= iteracoes <= ITERACOES_MAXIMAS:
        raise ValueError(
            f"Use 'pi' ou 'pi <iteracoes>', de 1 a {ITERACOES_MAXIMAS}."
        )
    soma = 0.0
    sinal = 1.0
    inicio = time.perf_counter()
    for k in range(iteracoes):
        soma += sinal / (2 * k + 1)
        sinal = -sinal
    segundos = time.perf_counter() - inicio
    estimativa = 4.0 * soma
    return {
        "ok": True,
        "pi": estimativa,
        "desvio": abs(estimativa - math.pi),
        "iteracoes": iteracoes,
        "segundos": segundos,
        "iteracoes_por_segundo": iteracoes / segundos,
    }


def analisar(dados):
    if len(dados) > LIMITE:
        raise ValueError("O texto excede 1024 bytes.")
    texto = dados.decode("utf-8")
    if not texto.strip():
        raise ValueError("O texto está vazio.")
    if "\n" in texto or "\r" in texto:
        raise ValueError("Envie apenas uma linha de texto.")
    if texto.strip() == "pi" or texto.strip().startswith("pi "):
        return medir_pi(texto.strip())
    return {
        "ok": True,
        "texto_maiusculo": texto.upper(),
        "caracteres": len(texto),
        "palavras": len(texto.split()),
        "bytes_utf8": len(dados),
    }


try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as servidor:
        servidor.bind(("0.0.0.0", PORTA))
        print(f"Servidor UDP na porta {PORTA}", flush=True)
        while True:
            dados, cliente = servidor.recvfrom(LIMITE + 1)
            try:
                resultado = analisar(dados)
            except ValueError as erro:
                resultado = {"ok": False, "erro": str(erro)}
            resposta = json.dumps(
                resultado,
                ensure_ascii=False,
            ).encode("utf-8")
            try:
                servidor.sendto(resposta, cliente)
                print(
                    f"UDP: resposta enviada para {cliente}",
                    flush=True,
                )
            except OSError as erro:
                print(f"Falha ao responder: {erro}", flush=True)
except KeyboardInterrupt:
    print("\nServidor UDP encerrado.")
except OSError as erro:
    raise SystemExit(f"Erro UDP: {erro}")