from bs4 import BeautifulSoup
import json

# HTML fornecido para bet365
html = """

"""

# Lista para armazenar os jogadores
players = []

# Parse do HTML
soup = BeautifulSoup(html, "html.parser")

# Procurar por todos os nomes e odds
name_divs = soup.find_all("div", class_=lambda x: x and "Name" in x)
odds_spans = soup.find_all("span", class_=lambda x: x and "Odds" in x)

# Extrair apenas os textos
nomes = [div.get_text(strip=True) for div in name_divs]
odds = [span.get_text(strip=True) for span in odds_spans]

# Se temos o mesmo número de nomes e odds, vamos mapeá-los
if len(nomes) == len(odds):
    for i in range(len(nomes)):
        players.append({
            "nome": nomes[i],
            "odd": odds[i]
        })
else:
    print(f"Erro: Número de nomes ({len(nomes)}) diferente do número de odds ({len(odds)})")

# Salva no arquivo bet365.json
with open("bet365.json", "w", encoding="utf-8") as f:
    json.dump(players, f, ensure_ascii=False, indent=4)

print("Arquivo bet365.json criado com sucesso!")
