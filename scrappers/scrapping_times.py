from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import re
import csv
import os

# ─── Configuração dos 20 times ─────────────────────────────────────────────────
TIMES_BRASILEIRAO = {
    "Flamengo":      {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/819/bra.flamengo",               "slug": "flamengo"},
    "Palmeiras":     {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/2029/bra.palmeiras",             "slug": "palmeiras"},
    "São Paulo":     {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/2026/bra.sao_paulo",             "slug": "sao-paulo"},
    "Fluminense":    {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/3445/bra.fluminense_fc",         "slug": "fluminense"},
    "Bahia":         {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/9967/bra.bahia",                 "slug": "bahia"},
    "Athletico-PR":  {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/3458/bra.atletico_paranaense",   "slug": "athletico-paranaense"},
    "Coritiba":      {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/3456/bra.coritiba_fbc",          "slug": "coritiba"},
    "Atlético-MG":   {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/7632/bra.atltico-mg",            "slug": "atletico-mg"},
    "Bragantino":    {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/6079/bra.bragantino",            "slug": "bragantino"},
    "Vitória":       {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/3457/bra.ec_vitoria",            "slug": "vitoria"},
    "Botafogo":      {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/6086/bra.botafogo",              "slug": "botafogo"},
    "Grêmio":        {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/6273/bra.gremio",                "slug": "gremio"},
    "Vasco":         {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/3454/bra.cr_vasco_da_gama",      "slug": "vasco-da-gama"},
    "Internacional": {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/1936/bra.internacional",         "slug": "internacional"},
    "Santos":        {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/2674/bra.santos",                "slug": "santos"},
    "Corinthians":   {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/874/bra.corinthians",            "slug": "corinthians"},
    "Cruzeiro":      {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/2022/bra.cruzeiro",              "slug": "cruzeiro"},
    "Remo":          {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/4936/betbrain.clube_do_remo",    "slug": "remo"},
    "Chapecoense":   {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/9318/betbrain.chapecoense_af",   "slug": "chapecoense"},
    "Mirassol":      {"url": "https://www.espn.com.br/futebol/time/calendario/_/id/9169/bra.mirassol",              "slug": "mirassol"},
}

def get_proximos_jogos(url, slug, limite=5):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    jogos = []

    for linha in soup.find_all("tr"):
        if "Campeonato Brasileiro" not in linha.get_text():
            continue

        link = linha.find("a", href=re.compile(r"/futebol/partida/_/jogoId/"))
        if not link: continue

        match = re.search(r"/jogoId/\d+/(.+)$", link["href"])
        if not match: continue

        confronto = match.group(1) 

        # Ajuste para o Bragantino: a ESPN as vezes usa red-bull-bragantino na URL
        # mas no seu dicionário está apenas 'bragantino'
        if slug in confronto:
            # 1. Definimos a situação (sua lógica invertida que funcionou)
            if confronto.startswith(slug + "-"):
                situacao = "visitante"
            elif confronto.endswith("-" + slug):
                situacao = "mandante"
            else:
                situacao = "mandante" # Fallback

            # 2. LIMPEZA BLINDADA:
            # Removemos tanto o slug curto quanto o nome completo da ESPN
            adversario = confronto
            termos_para_remover = [slug, "red-bull-bragantino", "red-bull", "bragantino"]
            
            for termo in termos_para_remover:
                adversario = adversario.replace(termo, "")
            
            # Remove hífens extras que sobraram nas pontas (ex: "-remo" ou "palmeiras-")
            adversario = adversario.strip("-")

            # Se mesmo assim a string for vazia (bug raro), não adicionamos para não gerar NaN
            if adversario:
                jogos.append({"adversario": adversario, "situacao": situacao})

        # REMOVI A SEGUNDA LINHA JOGOS.APPEND QUE ESTAVA AQUI E CAUSAVA DUPLICIDADE
        if len(jogos) >= limite: break

    return jogos

if __name__ == "__main__":
    output_dir = "data/raw"
    output_file = os.path.join(output_dir, "sequencias_times.csv")
    
    # Cria a pasta se não existir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    lista_final = []
    total = len(TIMES_BRASILEIRAO)

    print(f"Iniciando scraping das sequências no Python 3.12...")

    for i, (nome_time, dados) in enumerate(TIMES_BRASILEIRAO.items(), 1):
        print(f"[{i:02d}/{total}] Coletando: {nome_time}", end="\r")
        try:
            jogos = get_proximos_jogos(dados["url"], dados["slug"])
            for ordem, jogo in enumerate(jogos, 1):
                lista_final.append({
                    "time_base": nome_time,
                    "sequencia": ordem,
                    "adversario": jogo["adversario"],
                    "mando": jogo["situacao"]
                })
        except Exception as e:
            print(f"\nErro no time {nome_time}: {e}")

    # Salva o CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["time_base", "sequencia", "adversario", "mando"])
        writer.writeheader()
        writer.writerows(lista_final)

    print(f"\n✓ Arquivo gerado em: {output_file}")