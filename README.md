# Analisador de texto remoto em UDP e TCP

O projeto contém quatro programas independentes: cliente e servidor UDP, cliente e servidor TCP. Os servidores convertem texto para maiúsculas e devolvem contagens do texto original. A entrada tem até 1024 bytes em UTF-8 e deve ocupar uma única linha. No TCP, a mensagem termina em `\n`; no UDP, cada mensagem ocupa um datagrama. O TCP atende um cliente por vez.

Porta **1200** nos dois casos, uma em UDP e outra em TCP. Python 3, somente biblioteca padrão.

## Arquivos

```text
servidor_udp.py
cliente_udp.py
servidor_tcp.py
cliente_tcp.py
Dockerfile
.dockerignore
```

Os quatro programas são independentes: cada um roda sozinho e não importa nada do projeto. A função de análise aparece nos dois servidores de propósito, para que cada arquivo se sustente sem os demais.

## Executar no mesmo computador

Servidor UDP, em um terminal:

```bash
python3 servidor_udp.py
```

Servidor TCP, em outro terminal:

```bash
python3 servidor_tcp.py
```

Cliente UDP, em um terceiro:

```bash
python3 cliente_udp.py --mensagem "Olá mundo"
```

Cliente TCP:

```bash
python3 cliente_tcp.py --mensagem "Olá mundo"
```

Saída idêntica nos dois clientes:

```json
{
  "ok": true,
  "texto_maiusculo": "OLÁ MUNDO",
  "caracteres": 9,
  "palavras": 2,
  "bytes_utf8": 10
}
```

Os dois servidores podem ficar ativos ao mesmo tempo: UDP/1200 e TCP/1200 são portas distintas por definição de protocolo. Ctrl+C encerra cada servidor.

Sem `--mensagem`, o programa pergunta o texto e lê com `input()`. Ambos aceitam `--host` para apontar a outro computador. A porta é fixa em 1200 e não tem opção de linha de comando.

## Executar em computadores diferentes

```bash
python3 cliente_udp.py --host IP_DO_SERVIDOR --mensagem "Olá mundo"
```

```bash
python3 cliente_tcp.py --host IP_DO_SERVIDOR --mensagem "Olá mundo"
```

Os servidores escutam em `0.0.0.0:1200`, ou seja, em todas as interfaces IPv4. Esse endereço não é o destino do cliente: use o IP real do servidor. A rede e o firewall precisam permitir a porta 1200 nos dois protocolos; liberar uma não libera a outra.

## Regras da análise

- **Maiúsculas:** `texto.upper()`. O resultado pode ter mais caracteres que o original: `"ß".upper()` devolve `"SS"`. Por isso as contagens são calculadas sobre o texto recebido, e não sobre o texto em maiúsculas.
- **Caracteres:** `len(texto)`, incluindo espaços e pontuação. A contagem corresponde a pontos de código Unicode; um símbolo visual pode envolver mais de um.
- **Palavras:** grupos separados por espaços, tabulações, usando `split()`.
- **Bytes:** tamanho do texto recebido em UTF-8. Letras acentuadas podem ocupar mais de um byte.
- **`ok`:** informa se a análise foi realizada. Quando é falso, chega apenas `ok` e `erro`, sem contagens.

O servidor entrega o resultado como objeto JSON. O cliente decodifica, mostra o JSON formatado com `indent=2` e não depende de nenhum módulo compartilhado.

## Entradas recusadas

- Texto vazio ou apenas com espaços.
- Texto com `\n` ou `\r`, ou seja, mais de uma linha.
- Texto acima de 1024 bytes em UTF-8.

Os clientes conferem antes de enviar. Os servidores conferem de novo, porque qualquer remetente pode escrever no socket.

## UDP: como os dados circulam

1. `bind()` reserva a porta 1200.
2. `recvfrom()` recebe o texto e o endereço do cliente.
3. `analisar()` monta o resultado ou levanta o erro do texto recusado.
4. O erro vira `{"ok": false, "erro": ...}` e volta ao cliente como resposta normal.
5. `sendto()` entrega a resposta ao endereço de origem.
6. O servidor volta ao `recvfrom()` e atende o próximo cliente.

Uma requisição ocupa um datagrama e a resposta ocupa outro. Não há `listen()` nem `accept()`. O servidor lê até 1025 bytes para identificar entrada grande e rejeitá-la, sem analisar mensagem truncada.

## TCP: como os dados circulam

1. `bind()` reserva a porta e `listen(5)` define a fila de conexões pendentes.
2. `accept()` recebe uma conexão por vez.
3. O cliente envia o texto seguido de `\n`.
4. O servidor abre `makefile("rb")` e usa `readline()` para ler até o `\n`. Uma mensagem partida em vários pacotes chega inteira, porque `readline()` continua lendo até achar o fim de linha ou o limite.
5. `linha[:-1]` retira o `\n` antes da análise.
6. O servidor devolve o JSON com `\n` e fecha a conexão daquele cliente.
7. O servidor volta ao `accept()`.

`listen(5)` configura a fila de conexões pendentes; não cria cinco atendimentos simultâneos. Se a linha não termina em `\n` ou passa de 1024 bytes de texto, o servidor registra a falha, fecha aquela conexão e segue atendendo.

## Testes

Verificados com sockets reais na porta 1200, com os dois servidores ativos ao mesmo tempo:

- `Olá mundo` nos dois protocolos: 9 caracteres, 2 palavras, 10 bytes.
- `conexão, já!` nos dois protocolos: 12 caracteres, 2 palavras, 14 bytes.
- Texto de 1024 bytes exatos: aceito, com 1024 caracteres e 1 palavra.
- Texto de 1025 bytes: recusado antes do envio.
- TCP com a mensagem entregue em dois pedaços: `readline()` junta e a análise sai completa.
- TCP sem `\n` e conexão cortada antes do fim: o servidor registra e volta ao `accept()`.
- Cliente legítimo depois das falhas: resposta normal, o que confirma que o servidor não caiu.
- Datagrama acima do limite, UTF-8 inválido e texto só com espaços: chegam como `ok` falso com `erro`.
- `straße` → `STRASSE`: 6 caracteres na origem, 7 no texto em maiúsculas.