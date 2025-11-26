from bs4 import BeautifulSoup
import json

# HTMLs a serem processados
htmls = [
    """

    """,
    """

    """
]

# Lista para armazenar todos os jogadores
players = []

# Set para evitar duplicatas
jogadores_adicionados = set()

for html in htmls:
    soup = BeautifulSoup(html, "html.parser")
    
    # Procura por containers de jogadores usando padrão genérico
    # Procura por divs que contêm nomes (sem classes específicas)
    player_containers = soup.find_all("div", recursive=True)
    
    for container in player_containers:
        # Procura por divs que podem conter nomes de jogadores
        # Usa padrão genérico: procura por texto que parece nome
        nome_divs = container.find_all("div", string=True, recursive=False)
        
        for nome_div in nome_divs:
            nome_text = nome_div.get_text(strip=True)
            
            # Filtra textos que parecem nomes de jogadores
            if (len(nome_text) > 2 and 
                len(nome_text) < 50 and  # Nomes não são muito longos
                not any(char.isdigit() for char in nome_text) and 
                "." not in nome_text and 
                "+" not in nome_text and
                nome_text not in ["1+", "2+", "0.5", "1.5", "2.5"] and
                not nome_text.replace(".", "").isdigit()):  # Não é número
                
                # Evita duplicatas
                if nome_text in jogadores_adicionados:
                    continue
                
                # Procura por odds próximas a este nome
                # Procura por spans que contêm números (odds)
                parent_container = nome_div.parent
                if parent_container:
                    # Procura por spans com odds
                    odd_spans = parent_container.find_all("span", string=True)
                    
                    odd_val = None
                    found_1_plus = False
                    
                    # Primeiro, procura por "1+"
                    for span in odd_spans:
                        span_text = span.get_text(strip=True)
                        if span_text == "1+":
                            # Procura a odd correspondente (próximo span)
                            next_spans = span.find_next_siblings("span")
                            for next_span in next_spans:
                                try:
                                    odd_val = float(next_span.get_text(strip=True))
                                    found_1_plus = True
                                    break
                                except ValueError:
                                    continue
                            break
                    
                    # Fallback: se não encontrou "1+", pega a primeira odd disponível
                    if not found_1_plus and odd_val is None:
                        for span in odd_spans:
                            try:
                                odd_val = float(span.get_text(strip=True))
                                break
                            except ValueError:
                                continue
                    
                    # Adiciona o resultado se encontrou alguma odd válida
                    if odd_val is not None:
                        players.append({
                            "nome": nome_text, 
                            "odd": odd_val
                        })
                        jogadores_adicionados.add(nome_text)

# Salva no arquivo blaze.json
with open("blaze.json", "w", encoding="utf-8") as f:
    json.dump(players, f, ensure_ascii=False, indent=4)

print("Arquivo blaze.json criado com sucesso!")