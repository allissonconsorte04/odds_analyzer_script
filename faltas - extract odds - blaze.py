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
    
    # Abordagem semântica: encontra containers de jogadores pela estrutura
    # Cada jogador está em um container que contém:
    # 1. Um div com o nome do jogador
    # 2. Um div com múltiplos tableOutcomePlate
    
    # Estratégia: encontrar todos os divs que contêm tableOutcomePlate
    # e agrupá-los por container pai comum
    
    all_outcome_plates = soup.find_all("div", attrs={"data-editor-id": "tableOutcomePlate"})
    
    # Agrupa os plates por container de jogador
    # Estratégia: encontrar o container pai que contém múltiplos tableOutcomePlate
    # (indicando que é o container de um jogador)
    
    player_containers = {}
    
    for plate in all_outcome_plates:
        # Sobe na hierarquia para encontrar o container do jogador
        # O container do jogador é um div que contém múltiplos tableOutcomePlate
        current = plate.find_parent()
        player_container = None
        
        # Sobe até encontrar um div que contenha múltiplos tableOutcomePlate
        for level in range(8):
            if not current:
                break
            
            # Verifica quantos tableOutcomePlate este div contém
            plates_in_current = current.find_all("div", attrs={"data-editor-id": "tableOutcomePlate"})
            
            # Se contém pelo menos 1 plate (e este plate está na lista), é um candidato
            if len(plates_in_current) >= 1 and plate in plates_in_current:
                # Verifica se este div também contém um nome de jogador válido
                # Procura por texto que parece nome de jogador
                all_text_nodes = current.find_all(string=True)
                has_valid_name = False
                
                for text_node in all_text_nodes:
                    text = text_node.strip()
                    # Valida se é um nome válido
                    if (len(text) > 2 and len(text) < 50 and
                        not any(char.isdigit() for char in text) and
                        "." not in text and "+" not in text and
                        text not in ["1+", "2+", "0.5", "1.5", "2.5", "Remates do Jogador", "Incluíndo Prolongamento"] and
                        "Remates" not in text and "Prolongamento" not in text and
                        not text.replace(".", "").isdigit()):
                        # Verifica se este texto não está dentro de um tableOutcomePlate
                        parent = text_node.find_parent()
                        is_in_plate = False
                        while parent and parent != current:
                            if parent.get("data-editor-id") == "tableOutcomePlate":
                                is_in_plate = True
                                break
                            parent = parent.find_parent() if parent else None
                        
                        if not is_in_plate:
                            has_valid_name = True
                            break
                
                if has_valid_name:
                    player_container = current
                    break
            
            current = current.find_parent() if current else None
        
        if not player_container:
            continue
        
        # Usa o container como chave
        container_id = id(player_container)
        if container_id not in player_containers:
            player_containers[container_id] = {
                "container": player_container,
                "plates": []
            }
        
        player_containers[container_id]["plates"].append(plate)
    
    # Para cada container de jogador, extrai o nome e as odds
    for container_id, data in player_containers.items():
        container = data["container"]
        plates = data["plates"]
        
        # Procura pelo nome do jogador no container
        # O nome está em um texto que não está dentro de um tableOutcomePlate
        player_name = None
        
        # Procura por todos os nós de texto no container
        all_text_nodes = container.find_all(string=True)
        for text_node in all_text_nodes:
            text = text_node.strip()
            
            # Valida se é um nome válido
            if (len(text) > 2 and len(text) < 50 and
                not any(char.isdigit() for char in text) and
                "." not in text and "+" not in text and
                text not in ["1+", "2+", "0.5", "1.5", "2.5", "Remates do Jogador", "Incluíndo Prolongamento"] and
                "Remates" not in text and "Prolongamento" not in text and
                not text.replace(".", "").isdigit()):
                
                # Verifica se este texto não está dentro de um tableOutcomePlate
                parent = text_node.find_parent()
                is_in_plate = False
                while parent and parent != container:
                    if parent.get("data-editor-id") == "tableOutcomePlate":
                        is_in_plate = True
                        break
                    parent = parent.find_parent() if parent else None
                
                if not is_in_plate:
                    player_name = text
                    break
                    
        if not player_name:
            continue
        
        # Evita duplicatas
        if player_name in jogadores_adicionados:
            continue
        
        # Extrai as odds dos plates
        odd_1_plus = None
        odd_2_plus = None
        
        for plate in plates:
            # Procura pelo label "1+" ou "2+"
            label_spans = plate.find_all("span", string=lambda t: t and t.strip() in ["1+", "2+"])
            
            if not label_spans:
                continue
            
            label_text = label_spans[0].get_text(strip=True)
            
            # Procura pela odd no mesmo plate
            all_spans = plate.find_all("span")
            odd_value = None
            
            for span in all_spans:
                span_text = span.get_text(strip=True)
                if span_text in ["1+", "2+"]:
                    continue
                try:
                    float(span_text)
                    odd_value = span_text
                    break
                except ValueError:
                    continue
                    
            if odd_value:
                if label_text == "1+":
                    odd_1_plus = odd_value
                elif label_text == "2+":
                    odd_2_plus = odd_value
        
        # Adiciona o jogador se encontrou pelo menos uma odd
        if odd_1_plus is not None or odd_2_plus is not None:
            players.append({
                "nome": player_name,
                "odd_1_plus": odd_1_plus,
                "odd_2_plus": odd_2_plus
            })
            jogadores_adicionados.add(player_name)

# Salva no arquivo blaze.json
with open("blaze.json", "w", encoding="utf-8") as f:
    json.dump(players, f, ensure_ascii=False, indent=4)

print("Arquivo blaze.json criado com sucesso!")
