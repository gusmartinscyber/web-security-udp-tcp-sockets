FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY servidor_udp.py cliente_udp.py servidor_tcp.py cliente_tcp.py ./

USER 10001:10001

EXPOSE 1200/udp 1200/tcp

CMD ["python", "servidor_udp.py"]