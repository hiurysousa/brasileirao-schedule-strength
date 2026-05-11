from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import os
import time

URL_CLASSIFICACAO = "https://www.espn.com.br/futebol/classificacao/_/liga/bra.1"

def get_classificacao() -> list[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Acessando a página e aguardando carregamento...")
        
        # Aumentamos o timeout e esperamos a rede ficar ociosa
        page.goto(URL_CLASSIFICACAO, wait_until="networkidle", timeout=60000)
        
        # Scroll suave para garantir que elementos dinâmicos carreguem
        page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
        time.sleep(2)
        
        html = page.content()
        browser.close()

    # ... (código anterior do Playwright igual)

    soup = BeautifulSoup(html, "html.parser")
    classificacao = []

    # Localiza as linhas das duas tabelas (nomes e estatísticas)
    linhas_nomes = soup.select(".Table--fixed-left tbody tr")
    linhas_stats = soup.select(".Table__Scroller tbody tr")

    colunas = ["jogos", "vitorias", "empates", "derrotas", "gols_pro", "gols_contra", "saldo", "pontos"]

    # Iteramos usando o tamanho da tabela de nomes
    for i in range(len(linhas_nomes)):
        try:
            # 1. Extração do Nome e Slug (Tabela da Esquerda)
            # A ESPN usa classes como 'team-name' ou links dentro da célula
            link = linhas_nomes[i].find("a", href=True)
            if not link:
                continue
            
            # Pega o texto do span ou do link que contém o nome completo
            nome = link.get_text(strip=True)
            # Se o nome vier vazio ou muito curto (abreviação), tentamos o title ou o alt da imagem
            if len(nome) <= 3:
                img = linhas_nomes[i].find("img")
                nome = img.get("title") if img else nome

            href = link["href"]
            slug = href.split("/")[-1]

            # 2. Extração dos Números (Tabela da Direita)
            stats_tds = linhas_stats[i].find_all("td")
            valores = [td.get_text(strip=True) for td in stats_tds]

            # Verificamos se temos as colunas necessárias (pode variar entre 8 e 10 colunas)
            # Geralmente a última é PTS
            if len(valores) >= 8:
                entrada = {
                    "time": nome,
                    "slug": slug,
                    "jogos": int(valores[0]),
                    "vitorias": int(valores[1]),
                    "empates": int(valores[2]),
                    "derrotas": int(valores[3]),
                    "gols_pro": int(valores[4]),
                    "gols_contra": int(valores[5]),
                    "saldo": int(valores[6].replace("+", "")),
                    "pontos": int(valores[-1]) # Pegamos o último valor para garantir que é o PTS
                }
                
                j = entrada["jogos"]
                entrada["aproveitamento"] = round(entrada["pontos"] / (j * 3), 4) if j > 0 else 0.0
                classificacao.append(entrada)
                
        except Exception as e:
            print(f"Erro na linha {i}: {e}")
            continue

    return classificacao

def salvar_csv(classificacao: list[dict], caminho: str):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    colunas = ["time", "slug", "jogos", "vitorias", "empates", "derrotas",
               "gols_pro", "gols_contra", "saldo", "pontos", "aproveitamento"]

    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(classificacao)
    print(f"✓ CSV salvo com sucesso em: {os.path.abspath(caminho)}")

if __name__ == "__main__":
    print("Buscando classificação do Brasileirão (ESPN via Playwright)...")
    dados = get_classificacao()

    if not dados:
        print("Nenhum dado encontrado. Verifique se o site mudou os seletores.")
    else:
        # Exibe os 5 primeiros apenas para conferência
        for i, t in enumerate(dados[:5], 1):
            print(f"{i}º {t['time']} - {t['pontos']} pts")
        
        salvar_csv(dados, "data/raw/classificacao.csv")