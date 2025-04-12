import requests
import subprocess
import os
import shutil
import time
import logging

# Configuração do logger
logging.basicConfig(
    filename="execucao.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# CONFIGURAÇÕES
BB_USER = "usuario_bitbucket"
BB_APP_PASSWORD = "senha_de_app_bitbucket_com_permissao_de_leitura"
BB_WORKSPACE = "nome_do_workspace"
GH_USER = "usuario_github"
BASE_API_URL = f"https://api.bitbucket.org/2.0/repositories/{BB_WORKSPACE}"

# Cabeçalhos
auth = (BB_USER, BB_APP_PASSWORD)

def listar_repositorios():
    repos = []
    # Se precisar de mais de 100 repositórios, use a paginação
    url = BASE_API_URL + "?pagelen=100"
    while url:
        print(f"Consultando: {url}")
        res = requests.get(url, auth=auth)

        # Verificar se a resposta foi bem-sucedida
        if res.status_code != 200:
            print(f"Erro ao consultar a API: {res.status_code} - {res.text}")
            print(res)
            break

        try:
            data = res.json()
        except ValueError as e:
            print(f"Erro ao decodificar JSON: {e}")
            print(f"Resposta da API: {res.text}")
            break

        repos.extend([repo["slug"] for repo in data["values"]])
        url = data.get("next")

    # Salvar em arquivo
    with open("repos.txt", "w") as f:
        for repo in repos:
            f.write(f"{repo}\n")

    return repos

def clonar_e_migrar(repo):
    logging.info(f"Iniciando migração do repositório: {repo}")
    print(f">>> Migrando: {repo}")

    if os.path.exists(f"{repo}.git"):
        logging.info(f"O diretório '{repo}.git' já existe. Removendo...")
        print(f"O diretório '{repo}.git' já existe. Removendo...")
        try:
            for root, dirs, files in os.walk(f"{repo}.git"):
                for dir in dirs:
                    os.chmod(os.path.join(root, dir), 0o777)
                for file in files:
                    os.chmod(os.path.join(root, file), 0o777)
            shutil.rmtree(f"{repo}.git", ignore_errors=True)
        except Exception as e:
            logging.error(f"Erro ao remover o diretório '{repo}.git': {e}")
            print(f"Erro ao remover o diretório '{repo}.git': {e}")
            return

    bb_url = f"https://{BB_USER}:{BB_APP_PASSWORD}@bitbucket.org/{BB_WORKSPACE}/{repo}.git"

    result = subprocess.run(["git", "clone", "--mirror", bb_url], check=False)
    if result.returncode != 0:
        logging.error(f"Erro ao clonar o repositório '{repo}'. Verifique as credenciais e a URL.")
        print(f"Erro ao clonar o repositório '{repo}'. Verifique as credenciais e a URL.")
        return

    if not os.path.exists(f"{repo}.git"):
        logging.error(f"Erro: O diretório '{repo}.git' não foi criado após o clone.")
        print(f"Erro: O diretório '{repo}.git' não foi criado após o clone.")
        return

    os.chdir(f"{repo}.git")

    result = subprocess.run(["gh", "repo", "create", f"{GH_USER}/{repo}", "--private"], check=False)
    if result.returncode != 0:
        logging.error(f"Erro ao criar o repositório '{repo}' no GitHub.")
        print(f"Erro ao criar o repositório '{repo}' no GitHub.")
        os.chdir("..")
        shutil.rmtree(f"{repo}.git", ignore_errors=True)
        return

    logging.info("Aguardando GitHub reconhecer o repositório...")
    print("Aguardando GitHub reconhecer o repositório...")
    time.sleep(5)

    # Se usar alias para multiplas chaves SSH, altere o link do github para o alias necessário
    # Exemplo: subprocess.run(["git", "remote", "set-url", "origin", f"git@[alias-ssh-github]:{GH_USER}/{repo}.git"], check=False)
    subprocess.run(["git", "remote", "set-url", "origin", f"git@github.com:{GH_USER}/{repo}.git"], check=False)

    logging.info(f"Fazendo push do repositório '{repo}' para o GitHub.")
    print(f"Fazendo push do repositório '{repo}' para o GitHub.")
    result = subprocess.run(["git", "push", "--mirror"], check=False)
    if result.returncode != 0:
        logging.error(f"Erro ao fazer push do repositório '{repo}'. Verifique o acesso SSH e permissões.")
        print(f"Erro ao fazer push do repositório '{repo}'. Verifique o acesso SSH e permissões.")
        os.chdir("..")
        shutil.rmtree(f"{repo}.git", ignore_errors=True)
        return

    os.chdir("..")
    shutil.rmtree(f"{repo}.git", ignore_errors=True)

    logging.info(f"✓ Migração concluída para o repositório: {repo}")

    # Apaga a pasta temporária
    try:
        shutil.rmtree(f"{repo}.git", ignore_errors=True)
    except Exception as e:
        logging.error(f"Erro ao remover o diretório '{repo}.git': {e}")
        print(f"Erro ao remover o diretório '{repo}.git': {e}")

    print(f"✓ Concluído: {repo}")


def main():
    listar_repositorios()

    # Lê os repositórios do arquivo
    with open("repos.txt", "r") as f:
        repos = [line.strip() for line in f.readlines()]
        repos = [repo for repo in repos if repo]

    print(f"Total de repositórios encontrados: {len(repos)}")

    for repo in repos:
        try:
            clonar_e_migrar(repo)
        except Exception as e:
            print(f"Erro ao migrar {repo}: {e}")

if __name__ == "__main__":
    main()
