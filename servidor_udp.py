import json
import socket

PORTA = 1200
LIMITE = 1024


def analisar(dados):
    if len(dados) > LIMITE:
        raise ValueError("O texto excede 1024 bytes.")
    texto = dados.decode("utf-8")
    if not texto.strip():
        raise ValueError("O texto está vazio.")
    if "\n" in texto or "\r" in texto:
        raise ValueError("Envie apenas uma linha de texto.")
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