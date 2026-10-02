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
- **Palavras:** grupos separados por caracteres de espaço em branco, incluindo espaços, tabulações e separadores Unicode, usando `split()`.
- **Bytes:** tamanho do texto recebido em UTF-8. Letras acentuadas podem ocupar mais de um byte.
- **`ok`:** informa se a análise foi realizada. Quando é falso, chega apenas `ok` e `erro`, sem contagens.

O servidor entrega o resultado como objeto JSON. O cliente decodifica, mostra o JSON formatado com `indent=2` e não depende de nenhum módulo compartilhado.

## Entradas recusadas

- Texto vazio ou composto apenas por caracteres de espaço em branco.
- Texto com `\n` ou `\r` nos clientes; o delimitador `\n` acrescentado pelo cliente TCP não faz parte do texto analisado.
- Texto acima de 1024 bytes em UTF-8.

Os clientes conferem antes de enviar. Os servidores também validam o conteúdo recebido. No UDP, a validação considera o datagrama recebido. No TCP, o primeiro `\n` delimita a mensagem: se um remetente direto enviar `primeira\nsegunda\n`, apenas `primeira` será analisada e a conexão será encerrada. Um `\r` dentro dessa primeira linha é recusado.

## Comando pi

Além de analisar texto, os servidores aceitam `pi`, que calcula π pela série de Leibniz e cronometra o esforço. O caminho é o mesmo do texto: a mensagem vai no datagrama ou na linha do TCP, e a resposta volta no mesmo JSON.

```bash
python3 cliente_udp.py --host IP_DO_SERVIDOR --mensagem "pi"
```

Exemplo de resposta, com tempo e taxa ilustrativos e arredondados; os valores reais dependem da execução:

```json
{
  "ok": true,
  "pi": 3.1415916535897743,
  "desvio": 1.0000000187915248e-06,
  "iteracoes": 1000000,
  "segundos": 0.184,
  "iteracoes_por_segundo": 5434782.6
}
```

- `pi` usa 1.000.000 de iterações.
- `pi <iteracoes>` escolhe a quantidade, de 1 a 5.000.000.
- O tempo depende do processador, da versão do Python e da carga. Mesmo dentro do limite de iterações, o pedido pode ultrapassar o timeout de 3 s configurado nos clientes; esse timeout se aplica às operações bloqueantes do socket, não ao tempo total do programa.
- `desvio` é `abs(estimativa - math.pi)`. Para muitas iterações, o erro de truncamento da série é aproximadamente `1/iterações`, não exatamente igual. Pelo limite das séries alternadas, em aritmética exata ele é no máximo `4 / (2 * iteracoes + 1)`; a implementação também está sujeita ao arredondamento de ponto flutuante.
- O campo `erro` continua reservado às recusas, sempre com texto. Por isso a precisão usa `desvio`, e não `erro`.
- `iteracoes_por_segundo` é `iteracoes / segundos`: mede a taxa desse cálculo em Python naquela execução, não a capacidade geral da máquina.

A série de Leibniz é determinística: com a mesma quantidade de iterações e as mesmas condições de aritmética de ponto flutuante, produz a mesma estimativa de π. O cálculo é sequencial e pode ocupar intensamente um núcleo; não mede todos os recursos da máquina. Durante o cálculo, o servidor correspondente fica sem atender outras solicitações, tanto no TCP quanto no UDP. O limite de iterações restringe esse trabalho, mas não garante um tempo máximo de atendimento.

Antes de reconhecer o comando, o servidor remove caracteres de espaço em branco das extremidades com `strip()`. Depois disso, a mensagem precisa ser `pi` ou começar com `pi `, em minúsculas e com espaço comum após `pi`. Assim, `  pi 1  ` é um comando, enquanto `pizza`, `PI` e `pi` seguido diretamente de tabulação e um número são analisados como texto.

## UDP: como os dados circulam

1. `bind()` reserva a porta 1200.
2. `recvfrom()` recebe o texto e o endereço do cliente.
3. `analisar()` monta o resultado ou levanta o erro do texto recusado.
4. O erro vira `{"ok": false, "erro": ...}` e volta ao cliente como resposta normal.
5. `sendto()` envia a resposta ao endereço de origem; UDP não garante sua entrega.
6. O servidor volta ao `recvfrom()` e atende o próximo cliente.

Uma requisição ocupa um datagrama e a resposta ocupa outro. Não há `listen()` nem `accept()`. O servidor lê até 1025 bytes: se receber esse tamanho, rejeita a entrada antes de decodificar ou analisar o texto. Datagramas maiores podem ser truncados na recepção, mas o trecho recebido já excede o limite de 1024 bytes e também é rejeitado.

## TCP: como os dados circulam

1. `bind()` reserva a porta e `listen(5)` define a fila de conexões pendentes.
2. `accept()` recebe uma conexão por vez.
3. O cliente envia o texto seguido de `\n`.
4. O servidor abre `makefile("rb")` e usa `readline()` para ler até o `\n`. Uma mensagem partida em vários pacotes chega inteira, porque `readline()` continua lendo até achar o fim de linha, atingir o limite, encontrar o fim do fluxo ou ocorrer o timeout de 5 s da conexão.
5. `linha[:-1]` retira o `\n` antes da análise.
6. O servidor devolve o JSON com `\n` e fecha a conexão daquele cliente.
7. O servidor volta ao `accept()`.

`listen(5)` configura a fila de conexões pendentes; não cria cinco atendimentos simultâneos. Se a linha não termina em `\n` ou passa de 1024 bytes de texto, o servidor registra a falha, fecha aquela conexão e segue atendendo.

## Testes

Verificados com sockets reais na porta 1200, com os dois servidores ativos ao mesmo tempo:

- `Olá mundo` nos dois protocolos: 9 caracteres, 2 palavras, 10 bytes.
- `conexão, já!` nos dois protocolos: 12 caracteres, 2 palavras, 14 bytes.
- 1024 letras ASCII `a`: aceitas, com 1024 bytes, 1024 caracteres e 1 palavra.
- 512 letras `é`: aceitas, com 1024 bytes, 512 caracteres e 1 palavra.
- Texto de 1025 bytes: recusado antes do envio.
- TCP com a mensagem entregue em dois pedaços: `readline()` junta e a análise sai completa.
- TCP sem `\n` e conexão cortada antes do fim: o servidor registra e volta ao `accept()`.
- Cliente legítimo depois das falhas: resposta normal, o que confirma que o servidor não caiu.
- Datagrama acima do limite, UTF-8 inválido e texto só com espaços: chegam como `ok` falso com `erro`.
- `straße` → `STRASSE`: 6 caracteres na origem, 7 no texto em maiúsculas.
- `pi` nos dois protocolos: 1.000.000 de iterações, com estimativa `3.1415916535897743` e desvio aproximado de `1e-6`.
- `pi 5000000` nos dois protocolos: 5.000.000 de iterações, com estimativa `3.1415924535897797` e desvio aproximado de `2e-7`.
- `  pi 1  `: reconhecido como comando, com estimativa `4.0` e desvio aproximado de `0.858407`.
- TCP com `primeira\nsegunda\n` enviado diretamente pelo socket: apenas a primeira linha é analisada.
- `pi 0`, `pi abc` e `pi 6000000`: recusados com a mensagem de uso.
- `pizza`: analisada como texto, confirmando que o comando não captura palavras parecidas.
