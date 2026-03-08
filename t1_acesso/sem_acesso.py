# sem_acesso.py
import json
import requests

def ler_configuracao(origem: str):
    import os
    if origem == "local":
        path = "config.json"
        if not os.path.exists(path) and os.path.exists("t1_acesso/config.json"):
            path = "t1_acesso/config.json"
        with open(path) as f:
            return json.load(f)
    elif origem == "http":
        resp = requests.get("http://config-srv/config")
        return resp.json()
    elif origem == "s3":
        raise NotImplementedError("S3 não configurado neste lab")

try:
    cfg = ler_configuracao("local")
    print("Configuração carregada:", cfg)
except FileNotFoundError:
    print("config.json não encontrado — crie um para testar")