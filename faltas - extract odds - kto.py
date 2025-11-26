from bs4 import BeautifulSoup
import json

# Cole o HTML completo da tabela aqui
html = """

"""

soup = BeautifulSoup(html, "html.parser")

players = []

# Encontra a coluna "Mais" procurando por um h4 que contenha o texto "Mais"
mais_column = None
all_h4 = soup.find_all("h4")
for h4 in all_h4:
    if "Mais" in h4.get_text(strip=True):
        # Encontra o div pai que é a coluna
        parent = h4.parent
        while parent:
            if parent.name == 'div':
                # Verifica se este div tem múltiplos filhos (provavelmente é a coluna)
                children_count = sum(1 for _ in parent.children if hasattr(_, 'name'))
                if children_count > 5:  # Coluna terá muitos filhos
                    mais_column = parent
                    break
            parent = parent.parent
        if mais_column:
            break

if not mais_column:
    print("Erro: Coluna 'Mais' não encontrada")
else:
    # Coleta todos os elementos filhos diretos da coluna em ordem
    all_children = []
    for child in mais_column.children:
        if hasattr(child, 'name'):
            all_children.append(child)
    
    # Processa sequencialmente
    current_player_name = None
    current_odds = {}
    
    for element in all_children:
        # Verifica se é um div que contém nome de jogador (tem h4 > span com texto válido)
        if element.name == 'div':
            h4_tag = element.find('h4')
            if h4_tag:
                span_tag = h4_tag.find('span')
                if span_tag:
                    player_name = span_tag.get_text(strip=True)
                    # Verifica se é um nome válido (não vazio, não é "Mais"/"Menos", tem mais de 1 caractere)
                    if (player_name and 
                        player_name not in ["Mais", "Menos", "&nbsp;"] and 
                        len(player_name) > 1 and
                        not player_name.replace('.', '').replace(',', '').isdigit()):  # Não é só número
                        
                        # Salva o jogador anterior se houver
                        if current_player_name and (current_odds.get('0.5') or current_odds.get('1.5')):
                            players.append({
                                "nome": current_player_name,
                                "odd_1_plus": current_odds.get('0.5'),
                                "odd_2_plus": current_odds.get('1.5')
                            })
                        
                        # Inicia novo jogador
                        current_player_name = player_name.strip().strip('"\'')
                        current_odds = {}
        
        # Verifica se é um botão com odds
        elif element.name == 'button':
            # Ignora botões desabilitados
            if element.get('disabled'):
                continue
            
            # Verifica se o botão pertence à coluna "Mais" (deve conter texto "Mais")
            button_text_all = element.get_text()
            if "Mais" not in button_text_all:
                continue
            
            # Só processa se já temos um jogador atual
            if not current_player_name:
                continue
            
            # Procura por números no botão
            all_text_in_button = []
            for div in element.find_all('div'):
                text = div.get_text(strip=True)
                if text:
                    all_text_in_button.append(text)
            
            linha_value = None
            odd_value = None
            
            # Identifica linha (0.5, 1.5, etc.) e odd (valor numérico maior)
            for text in all_text_in_button:
                try:
                    num = float(text)
                    # Valores de linha geralmente são 0.5, 1.5, 2.5, 3.5
                    if num in [0.5, 1.5, 2.5, 3.5]:
                        linha_value = text
                    # Odds são valores geralmente entre 1.0 e 100
                    elif num >= 1.0 and num <= 100:
                        odd_value = str(num)
                except ValueError:
                    pass
            
            # Armazena a odd se encontrou linha e odd
            if linha_value and odd_value:
                if linha_value == "0.5" and not current_odds.get('0.5'):
                    current_odds['0.5'] = odd_value
                elif linha_value == "1.5" and not current_odds.get('1.5'):
                    current_odds['1.5'] = odd_value
    
    # Salva o último jogador processado
    if current_player_name and (current_odds.get('0.5') or current_odds.get('1.5')):
        players.append({
            "nome": current_player_name,
            "odd_1_plus": current_odds.get('0.5'),
            "odd_2_plus": current_odds.get('1.5')
        })

# Salva no arquivo kto.json
with open("kto.json", "w", encoding="utf-8") as f:
    json.dump(players, f, ensure_ascii=False, indent=4)

print(f"Arquivo kto.json criado com sucesso! {len(players)} jogadores extraídos.")