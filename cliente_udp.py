import argparse
import json
import socket

parser = argparse.ArgumentParser(description="Cliente UDP")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--mensagem")
args = parser.parse_args()

try:
    texto = (
        args.mensagem
        if args.mensagem is not None
        else input("Texto: ")
    )
    dados = texto.encode("utf-8")
    if not texto.strip():
        raise ValueError("Digite um texto com conteúdo.")
    if "\n" in texto or "\r" in texto:
        raise ValueError("Envie apenas uma linha de texto.")
    if len(dados) > 1024:
        raise ValueError("O texto excede 1024 bytes.")
    destino = (socket.gethostbyname(args.host), 1200)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cliente:
        cliente.settimeout(3)
        cliente.sendto(dados, destino)
        resposta, origem = cliente.recvfrom(8193)
        if origem != destino:
            raise ValueError(
                "Resposta recebida de um endereço inesperado."
            )
        if len(resposta) > 8192:
            raise ValueError("Resposta acima do limite.")
        resultado = json.loads(resposta.decode("utf-8"))
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
except TimeoutError:
    raise SystemExit("Timeout: não chegou resposta UDP.")
except (OSError, ValueError) as erro:
    raise SystemExit(f"Erro: {erro}")
except (KeyboardInterrupt, EOFError):
    print("\nCliente encerrado.")