import argparse
import json
import socket

parser = argparse.ArgumentParser(description="Cliente TCP")
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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
        cliente.settimeout(3)
        cliente.connect(destino)
        # O servidor identifica o fim da mensagem pelo \n.
        cliente.sendall(dados + b"\n")
        with cliente.makefile("rb") as leitura:
            resposta = leitura.readline(8194)
        if (
            len(resposta) > 8193
            or not resposta.endswith(b"\n")
        ):
            raise ValueError(
                "Resposta incompleta ou acima do limite."
            )
        resultado = json.loads(resposta.decode("utf-8"))
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
except TimeoutError:
    raise SystemExit("Timeout na comunicação TCP.")
except (OSError, ValueError) as erro:
    raise SystemExit(f"Erro: {erro}")
except (KeyboardInterrupt, EOFError):
    print("\nCliente encerrado.")