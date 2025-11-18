from collections import defaultdict
from rapidfuzz import process
import unicodedata
import json
import subprocess
import sys
from datetime import datetime
from difflib import SequenceMatcher
import re

# Função para executar scripts de extração
def execute_extraction_scripts():
    """Executa todos os scripts de extração de odds"""
    scripts = [
        "faltas - extract odds - blaze.py",
        "faltas - extract odds - bet365.py", 
        "faltas - extract odds - pitaco.py",
        "faltas - extract odds - kto.py"
    ]
    
    print("=== EXECUTANDO SCRIPTS DE EXTRAÇÃO ===")
    
    for script in scripts:
        try:
            print(f"Executando {script}...")
            result = subprocess.run([sys.executable, script], 
                                  capture_output=True, 
                                  text=True, 
                                  encoding='utf-8',
                                  errors='replace')
            
            if result.returncode == 0:
                print(f"✓ {script} executado com sucesso")
            else:
                print(f"✗ Erro ao executar {script}:")
                if result.stderr:
                    print(f"  {result.stderr}")
                
        except Exception as e:
            print(f"✗ Erro ao executar {script}: {e}")
    
    print("=== FIM DA EXTRAÇÃO ===\n")

# Executa os scripts de extração
execute_extraction_scripts()

# Solicita informações do jogo ao usuário
print("\n=== INFORMAÇÕES DO JOGO ===")
time_mandante = input("Digite o nome do time mandante: ").strip()
time_visitante = input("Digite o nome do time visitante: ").strip()

# Cria nome do arquivo baseado nos times
nome_arquivo = f"{time_mandante}_vs_{time_visitante}.json"
nome_arquivo = nome_arquivo.replace(" ", "_").replace("/", "_").replace("\\", "_")

print(f"\nArquivo será salvo como: {nome_arquivo}")

# Carrega dados dos arquivos JSON
def load_json_data():
    data = []
    
    # Carrega Pitaco (formato novo com odd_1_plus e odd_2_plus)
    with open('pitaco.json', 'r', encoding='utf-8') as f:
        pitaco_data = json.load(f)
        # Cria items separados para 1+ e 2+
        items_1_plus = [{"nome": item["nome"], "linha": "1+", "odd": item.get("odd_1_plus")} for item in pitaco_data if item.get("odd_1_plus")]
        items_2_plus = [{"nome": item["nome"], "linha": "2+", "odd": item.get("odd_2_plus")} for item in pitaco_data if item.get("odd_2_plus")]
        data.append({
            "casa": "Pitaco",
            "items": items_1_plus + items_2_plus
        })
    
    # Carrega Blaze (formato novo com odd_1_plus e odd_2_plus)
    with open('blaze.json', 'r', encoding='utf-8') as f:
        blaze_data = json.load(f)
        # Cria items separados para 1+ e 2+
        items_1_plus = [{"nome": item["nome"], "linha": "1+", "odd": item.get("odd_1_plus")} for item in blaze_data if item.get("odd_1_plus")]
        items_2_plus = [{"nome": item["nome"], "linha": "2+", "odd": item.get("odd_2_plus")} for item in blaze_data if item.get("odd_2_plus")]
        data.append({
            "casa": "Blaze",
            "items": items_1_plus + items_2_plus
        })
    
    # Carrega Bet365 (formato novo com odd_1_plus e odd_2_plus)
    with open('bet365.json', 'r', encoding='utf-8') as f:
        bet365_data = json.load(f)
        # Cria items separados para 1+ e 2+
        items_1_plus = [{"nome": item["nome"], "linha": "1+", "odd": item.get("odd_1_plus")} for item in bet365_data if item.get("odd_1_plus")]
        items_2_plus = [{"nome": item["nome"], "linha": "2+", "odd": item.get("odd_2_plus")} for item in bet365_data if item.get("odd_2_plus")]
        data.append({
            "casa": "Bet365",
            "items": items_1_plus + items_2_plus
        })
    
    # Carrega KTO (formato novo com odd_1_plus e odd_2_plus)
    with open('kto.json', 'r', encoding='utf-8') as f:
        kto_data = json.load(f)
        # Cria items separados para 1+ e 2+
        items_1_plus = [{"nome": item["nome"], "linha": "1+", "odd": item.get("odd_1_plus")} for item in kto_data if item.get("odd_1_plus")]
        items_2_plus = [{"nome": item["nome"], "linha": "2+", "odd": item.get("odd_2_plus")} for item in kto_data if item.get("odd_2_plus")]
        data.append({
            "casa": "KTO",
            "items": items_1_plus + items_2_plus
        })
    
    return data

data = load_json_data()

# Função para normalizar nomes (remove acentos e deixa minúsculo)
def normalize_name(name):
    name = name.lower()
    name = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    return name

# Função para normalizar nomes para unificação (remove acentos, caracteres especiais)
def normalize_name_for_unification(name):
    """
    Normaliza o nome removendo acentos, convertendo para minúsculas e removendo caracteres especiais.
    """
    # Remover acentos
    name = name.lower()
    name = re.sub(r'[àáâãäå]', 'a', name)
    name = re.sub(r'[èéêë]', 'e', name)
    name = re.sub(r'[ìíîï]', 'i', name)
    name = re.sub(r'[òóôõö]', 'o', name)
    name = re.sub(r'[ùúûü]', 'u', name)
    name = re.sub(r'[ç]', 'c', name)
    name = re.sub(r'[ñ]', 'n', name)
    
    # Remover caracteres especiais e espaços extras
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def extract_initials(name):
    """
    Extrai as iniciais de um nome.
    """
    words = name.split()
    initials = ''.join([word[0] for word in words if len(word) > 0])
    return initials

def is_abbreviation(name1, name2):
    """
    Verifica se um nome é uma abreviação do outro.
    """
    norm1 = normalize_name_for_unification(name1)
    norm2 = normalize_name_for_unification(name2)
    
    # Verificar se um é inicial do outro
    initials1 = extract_initials(norm1)
    initials2 = extract_initials(norm2)
    
    # Se um nome é muito curto e contém apenas iniciais
    if len(norm1) <= 3 and norm1 in initials2:
        return True, norm2
    if len(norm2) <= 3 and norm2 in initials1:
        return True, norm1
    
    # Verificar se um nome contém o outro (incluindo apelidos)
    if norm1 in norm2 and len(norm1) < len(norm2):
        return True, norm2
    if norm2 in norm1 and len(norm2) < len(norm1):
        return True, norm1
    
    # Verificar apelidos: se um nome curto aparece como palavra completa no outro
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    # Se um nome tem apenas uma palavra e essa palavra aparece no outro nome
    if len(words1) == 1 and list(words1)[0] in norm2 and len(list(words1)[0]) >= 4:
        # Verificar se há sobrenome em comum (palavras com 4+ caracteres)
        long_words2 = [w for w in words2 if len(w) >= 4]
        if long_words2:
            return True, norm2
    if len(words2) == 1 and list(words2)[0] in norm1 and len(list(words2)[0]) >= 4:
        long_words1 = [w for w in words1 if len(w) >= 4]
        if long_words1:
            return True, norm1
    
    return False, None

def calculate_similarity(name1, name2):
    """
    Calcula a similaridade entre dois nomes usando diferentes métodos.
    """
    norm1 = normalize_name_for_unification(name1)
    norm2 = normalize_name_for_unification(name2)
    
    # Similaridade básica usando SequenceMatcher
    basic_similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Verificar se é abreviação
    is_abbrev, full_name = is_abbreviation(name1, name2)
    if is_abbrev:
        return 0.9, full_name  # Alta similaridade para abreviações
    
    # Verificar similaridade de palavras
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    # Verificar se um nome curto (apelido) aparece como palavra no outro nome mais longo
    # Ex: "Vitinho" vs "Vitinho da Silva" ou "Victor Da Silva Vitinho"
    nickname_similarity = 0
    if len(words1) == 1 and len(words2) > 1:
        # Nome 1 é curto (possível apelido)
        short_word = list(words1)[0]
        # Verificar se o apelido aparece no nome mais longo (como palavra completa ou parte)
        if short_word in norm2 and len(short_word) >= 4:
            # Verificar se há sobrenome em comum (palavras longas, geralmente sobrenomes)
            long_words2 = [w for w in words2 if len(w) >= 4]
            if long_words2:
                nickname_similarity = 0.85
    elif len(words2) == 1 and len(words1) > 1:
        # Nome 2 é curto (possível apelido)
        short_word = list(words2)[0]
        if short_word in norm1 and len(short_word) >= 4:
            long_words1 = [w for w in words1 if len(w) >= 4]
            if long_words1:
                nickname_similarity = 0.85
    
    # Verificar caso especial: apelido aparece entre aspas ou no final
    # Ex: "Victor Da Silva \"Vitinho" contém "Vitinho"
    if nickname_similarity == 0:
        # Se um nome tem apenas uma palavra e o outro tem múltiplas palavras
        if len(words1) == 1 and len(words2) > 1:
            short_word = list(words1)[0]
            # Verificar se aparece como palavra completa no outro (mesmo com caracteres especiais)
            words2_list = norm2.split()
            if any(short_word in w or w in short_word for w in words2_list if len(w) >= 4 or len(short_word) >= 4):
                # Verificar se há palavras longas em comum (sobrenomes)
                long_words2 = [w for w in words2 if len(w) >= 4]
                if long_words2:
                    nickname_similarity = 0.85
        elif len(words2) == 1 and len(words1) > 1:
            short_word = list(words2)[0]
            words1_list = norm1.split()
            if any(short_word in w or w in short_word for w in words1_list if len(w) >= 4 or len(short_word) >= 4):
                long_words1 = [w for w in words1 if len(w) >= 4]
                if long_words1:
                    nickname_similarity = 0.85
    
    if words1 and words2:
        # Similaridade de Jaccard (intersecção / união)
        word_similarity = len(words1.intersection(words2)) / len(words1.union(words2)) if words1.union(words2) else 0
        
        # Verificar se um conjunto de palavras está contido no outro (mais restritivo)
        # Também verifica se um nome curto (apelido) está contido no outro
        if (words1.issubset(words2) or words2.issubset(words1)):
            if len(words1) >= 2 and len(words2) >= 2:
                containment_similarity = 0.85  # Alta similaridade para contenção
            elif (len(words1) == 1 and len(words2) > 1) or (len(words2) == 1 and len(words1) > 1):
                # Caso especial: apelido contido no nome completo
                containment_similarity = 0.85
            else:
                containment_similarity = 0
        else:
            containment_similarity = 0
        
        # Verificar se há sobreposição significativa de palavras (ex: Alan Franco vs Alan Steven Franco)
        common_words = words1.intersection(words2)
        
        # Verificar se há palavras significativas em comum (ex: A. Cabral vs Arthur Cabral)
        # Verifica se há pelo menos uma palavra com 4+ caracteres em comum
        # IMPORTANTE: Além do sobrenome, deve verificar se o primeiro nome/inicial também bate
        significant_common_words = [word for word in common_words if len(word) >= 4]
        
        # Pega as primeiras palavras de cada nome (primeiro nome ou inicial)
        # IMPORTANTE: Considera apenas a PRIMEIRA palavra de cada nome, não todas as palavras únicas
        # Ex: "R. Lima da Silva" -> primeira palavra é "r"
        # Ex: "Vitinho da Silva" -> primeira palavra é "vitinho"
        first_word1_set = words1 - common_words  # Palavras únicas do nome 1
        first_word2_set = words2 - common_words  # Palavras únicas do nome 2
        
        # Pega a primeira palavra de cada nome normalizado
        norm1_words_list = norm1.split()
        norm2_words_list = norm2.split()
        first_word1_actual = norm1_words_list[0] if norm1_words_list else ""
        first_word2_actual = norm2_words_list[0] if norm2_words_list else ""
        
        # Cria sets com apenas a primeira palavra para comparação
        first_word1 = {first_word1_actual} if first_word1_actual else first_word1_set
        first_word2 = {first_word2_actual} if first_word2_actual else first_word2_set
        
        # Se há palavra significativa em comum (sobrenome), verifica se o primeiro nome/inicial também corresponde
        if (len(significant_common_words) >= 1 and 
            len(words1) >= 2 and len(words2) >= 2):
            
            # Se ambos têm palavras únicas (primeiro nome diferente), NÃO unifica
            # Ex: "Rodrigo Gomes" vs "Joao Gomes" -> {'rodrigo'} vs {'joao'} -> diferentes
            if first_word1 and first_word2 and not first_word1.intersection(first_word2):
                # Verifica se uma é inicial da outra
                # Ex: "R. Gomes" vs "Rodrigo Gomes" -> 'r' pode ser inicial de 'rodrigo'
                is_initial_match = False
                for w1 in first_word1:
                    for w2 in first_word2:
                        # Se um é muito curto (inicial) e o outro começa com essa letra
                        # IMPORTANTE: Só considera se a inicial pode realmente ser do nome
                        # Ex: "R." pode ser "Rodrigo" ou "Rafael", mas não "Victor"
                        if (len(w1) <= 2 and len(w2) > 2 and w2.startswith(w1[0].lower())) or \
                           (len(w2) <= 2 and len(w1) > 2 and w1.startswith(w2[0].lower())):
                            # Verificação adicional: se a inicial não corresponde ao início do nome, não unifica
                            # Ex: "R." vs "Victor" -> 'r' não é inicial de 'victor', então não unifica
                            if len(w1) <= 2:
                                # w1 é inicial, verifica se w2 começa com essa letra
                                if w2[0].lower() == w1[0].lower():
                                    is_initial_match = True
                                    break
                            elif len(w2) <= 2:
                                # w2 é inicial, verifica se w1 começa com essa letra
                                if w1[0].lower() == w2[0].lower():
                                    is_initial_match = True
                                    break
                
                # Verifica se um é apelido do outro (ex: "Vitinho" vs "Victor")
                is_nickname_match = False
                for w1 in first_word1:
                    for w2 in first_word2:
                        # Verifica se um nome curto (apelido) aparece no outro nome mais longo
                        # Ex: "Vitinho" contém "vit" que está em "Victor"
                        if (len(w1) >= 4 and len(w2) >= 4 and (w1 in w2 or w2 in w1)) or \
                           (len(w1) >= 4 and w1 in norm2) or (len(w2) >= 4 and w2 in norm1):
                            # Verificação adicional: verifica se há similaridade fonética ou de apelido
                            # Ex: "Vitinho" (7 chars) vs "Victor" (6 chars) - ambos começam com "vit"
                            if (w1.startswith(w2[:3]) or w2.startswith(w1[:3])) and abs(len(w1) - len(w2)) <= 3:
                                is_nickname_match = True
                                break
                
                if is_initial_match or is_nickname_match:
                    first_name_similarity = 0.8  # É uma abreviação válida ou apelido
                else:
                    first_name_similarity = 0  # Primeiros nomes diferentes, não unifica
            else:
                # Se não há palavras únicas ou há interseção, verifica se realmente são o mesmo jogador
                # Se há apenas uma palavra significativa em comum (sobrenome) e os primeiros nomes são diferentes,
                # reduz a similaridade para evitar unificações incorretas
                if len(significant_common_words) == 1 and first_word1 and first_word2:
                    # Apenas sobrenome em comum, primeiros nomes diferentes - reduz similaridade
                    first_name_similarity = 0.3  # Baixa similaridade, não deve unificar
                else:
                    first_name_similarity = 0.8  # Alta similaridade se há palavra significativa em comum
        else:
            first_name_similarity = 0
        if (len(common_words) >= 2 and  # Pelo menos 2 palavras em comum
            len(words1) >= 2 and len(words2) >= 2 and
            len(common_words) / max(len(words1), len(words2)) >= 0.5):  # Pelo menos 50% de sobreposição
            word_overlap_similarity = 0.85
        else:
            word_overlap_similarity = 0
        
        # PENALIDADE: Se há apenas uma palavra significativa em comum (sobrenome) e os primeiros nomes são diferentes,
        # reduz drasticamente a similaridade para evitar unificações incorretas
        # Ex: "R. Lima da Silva" vs "Vitinho da Silva" -> só têm "Silva" em comum, primeiros nomes diferentes
        if (len(significant_common_words) == 1 and 
            len(words1) >= 2 and len(words2) >= 2 and
            first_word1 and first_word2 and 
            not first_word1.intersection(first_word2)):
            # Verifica se os primeiros nomes são realmente diferentes (não são iniciais ou apelidos)
            first_names_different = True
            for w1 in first_word1:
                for w2 in first_word2:
                    # Se um é inicial do outro ou são apelidos, não são diferentes
                    if ((len(w1) <= 2 and w2.startswith(w1[0].lower())) or 
                        (len(w2) <= 2 and w1.startswith(w2[0].lower())) or
                        (w1.startswith(w2[:3]) or w2.startswith(w1[:3]))):
                        first_names_different = False
                        break
                if not first_names_different:
                    break
            
            if first_names_different:
                # Primeiros nomes claramente diferentes, apenas sobrenome em comum - penaliza
                word_overlap_similarity = max(word_overlap_similarity - 0.5, 0)  # Reduz similaridade
                if first_name_similarity > 0:
                    first_name_similarity = max(first_name_similarity - 0.5, 0)  # Reduz similaridade do primeiro nome
        
        # Verificar casos específicos como "Alan Franco" vs "Alan Steven Franco"
        # Se temos pelo menos 2 palavras em comum e uma das palavras tem pelo menos 4 caracteres
        if (len(common_words) >= 2 and 
            any(len(word) >= 4 for word in common_words) and
            len(words1) >= 2 and len(words2) >= 2):
            specific_case_similarity = 0.9
        else:
            specific_case_similarity = 0
        
        combined_similarity = max(basic_similarity, word_similarity, containment_similarity, first_name_similarity, word_overlap_similarity, specific_case_similarity, nickname_similarity)
    else:
        combined_similarity = max(basic_similarity, nickname_similarity)
    
    return combined_similarity, None

def unify_duplicate_players(players, similarity_threshold=0.75):
    """
    Unifica jogadores duplicados automaticamente baseado na similaridade dos nomes.
    """
    print(f"\n=== UNIFICANDO JOGADORES DUPLICADOS (threshold: {similarity_threshold}) ===")
    
    # Encontrar duplicatas
    duplicates = []
    processed = set()
    
    for i, player1 in enumerate(players):
        if i in processed:
            continue
            
        current_group = [i]
        name1 = player1['nome']
        
        for j, player2 in enumerate(players[i+1:], i+1):
            if j in processed:
                continue
                
            name2 = player2['nome']
            similarity, full_name = calculate_similarity(name1, name2)
            
            if similarity >= similarity_threshold:
                current_group.append(j)
                processed.add(j)
        
        if len(current_group) > 1:
            duplicates.append(current_group)
            processed.update(current_group)
    
    print(f"Encontrados {len(duplicates)} grupos de jogadores duplicados:")
    for i, group in enumerate(duplicates):
        print(f"Grupo {i+1}: {[players[idx]['nome'] for idx in group]}")
    
    # Criar novo dicionário para jogadores unificados
    unified_players = {}
    processed_indices = set()
    
    # Processar grupos de duplicatas
    for group in duplicates:
        # Escolher o nome prioritário: 1. Bet365, 2. Nome mais completo
        group_players = [players[idx] for idx in group]
        
        # Verificar se algum jogador do grupo tem odd na Bet365
        bet365_players = [p for p in group_players if p['Bet365'] is not None]
        
        if bet365_players:
            # Prioriza o nome da Bet365
            main_player = bet365_players[0]
        else:
            # Se não houver Bet365, usa o nome mais completo
            main_player = max(group_players, key=lambda x: len(x['nome']))
        
        main_name = main_player['nome']
        
        # Combinar odds de todos os jogadores do grupo
        # Agrupa por linha (1+ ou 2+)
        combined_odds_by_line = {}
        
        for player in group_players:
            linha = player.get('linha', '1+')
            if linha not in combined_odds_by_line:
                combined_odds_by_line[linha] = {
                    'nome': main_name,
                    'linha': linha,
                    'Pitaco': None,
                    'Blaze': None,
                    'Bet365': None,
                    'KTO': None
                }
            
            for casa in ['Pitaco', 'Blaze', 'Bet365', 'KTO']:
                if player[casa] is not None:
                    # Se a casa já tem uma odd, manter a menor (mais favorável)
                    if combined_odds_by_line[linha][casa] is None or player[casa] < combined_odds_by_line[linha][casa]:
                        combined_odds_by_line[linha][casa] = player[casa]
        
        # Adiciona cada linha separadamente
        for combined_odds in combined_odds_by_line.values():
            key = f"{main_name}_{combined_odds['linha']}"
            unified_players[key] = combined_odds
        processed_indices.update(group)
        
        print(f"Unificado: {main_name} <- {[p['nome'] for p in group_players]}")
    
    # Adicionar jogadores não duplicados
    for i, player in enumerate(players):
        if i not in processed_indices:
            linha = player.get('linha', '1+')
            key = f"{player['nome']}_{linha}"
            unified_players[key] = {
                'nome': player['nome'],
                'linha': linha,
                'Pitaco': player['Pitaco'],
                'Blaze': player['Blaze'],
                'Bet365': player['Bet365'],
                'KTO': player.get('KTO')
            }
    
    # Converter de volta para lista e ordenar
    unified_list = list(unified_players.values())
    unified_list.sort(key=lambda x: x['nome'])
    
    print(f"Total de jogadores antes: {len(players)}")
    print(f"Total de jogadores depois: {len(unified_list)}")
    print("=== FIM DA UNIFICAÇÃO ===\n")
    
    return unified_list

# Função para limpar odds e transformar em float ou None
def parse_odds(value):
    if not value or value == '-':
        return None
    value = str(value).replace('x', '').strip()
    try:
        return float(value)
    except ValueError:
        return None

# Funções para análise do critério de Kelly
def calculate_implied_probability(odds):
    """
    Calcula a probabilidade implícita das odds.
    Para odds decimais: probabilidade = 1 / odds
    """
    if odds is None or odds <= 0:
        return None
    return 1 / odds

def calculate_expected_value(odds, true_probability):
    """
    Calcula o valor esperado de uma aposta.
    EV = (odds * true_probability) - (1 - true_probability)
    """
    if odds is None or true_probability is None:
        return None
    
    win_amount = odds - 1  # Ganho líquido (odds - stake)
    ev = (win_amount * true_probability) - (1 - true_probability)
    return ev

def calculate_kelly_fraction(odds, true_probability, max_fraction=0.02):
    """
    Calcula a fração de Kelly para determinar o tamanho ideal da aposta.
    Kelly% = (bp - q) / b
    onde:
    b = odds - 1 (ganho líquido)
    p = probabilidade de ganhar
    q = probabilidade de perder (1 - p)
    
    Versão conservadora: limita a no máximo 2% do bankroll
    """
    if odds is None or true_probability is None:
        return None
    
    b = odds - 1  # Ganho líquido
    p = true_probability
    q = 1 - p
    
    kelly = (b * p - q) / b
    
    # Versão conservadora: limita a no máximo 2% do bankroll
    # Kelly deve estar entre 0 e max_fraction (0% a 2% do bankroll)
    return max(0, min(max_fraction, kelly))

def calculate_kelly_fraction_unlimited(odds, true_probability):
    """
    Calcula a fração de Kelly SEM LIMITE - valor matemático puro.
    Este é o valor ideal segundo o critério de Kelly clássico.
    """
    if odds is None or true_probability is None:
        return None
    
    b = odds - 1  # Ganho líquido
    p = true_probability
    q = 1 - p
    
    kelly = (b * p - q) / b
    
    # Retorna o valor real, mas não permite valores negativos
    return max(0, kelly)

def suggest_conservative_fraction(kelly_fraction):
    """
    Sugere valores conservadores específicos baseados na fração de Kelly.
    Valores sugeridos: 0.5%, 0.75%, 1.0%, 1.25%, 1.5%, 1.75%, 2.0%
    """
    if kelly_fraction is None or kelly_fraction <= 0:
        return None, "NÃO APOSTAR"
    
    # Valores conservadores sugeridos (em decimal)
    conservative_values = [0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175, 0.02]
    
    # Encontra o valor mais próximo mas não maior que Kelly
    suggested = None
    for value in conservative_values:
        if value <= kelly_fraction:
            suggested = value
        else:
            break
    
    if suggested is None:
        return None, "NÃO APOSTAR"
    
    # Determina a recomendação baseada no valor sugerido
    if suggested >= 0.015:  # 1.5% ou mais
        recommendation = "APOSTA FORTE"
    elif suggested >= 0.01:  # 1.0% ou mais
        recommendation = "APOSTA MÉDIA"
    elif suggested >= 0.005:  # 0.5% ou mais
        recommendation = "APOSTA FRACA"
    else:
        recommendation = "NÃO APOSTAR"
    
    return suggested, recommendation

def estimate_true_probability_from_odds(odds_dict):
    """
    Estima a probabilidade "verdadeira" baseada na média PONDERADA das odds disponíveis.
    
    Pesos utilizados:
    - Bet365: 30% (casa estabelecida, odds confiáveis)
    - Pitaco: 30% (casa estabelecida, odds confiáveis)
    - Estrela: 20% (casa menor)
    - Blaze: 20% (casa menor)
    
    Args:
        odds_dict: Dicionário com formato {'Casa': odd_value, ...}
    
    Returns:
        Probabilidade estimada baseada na média ponderada das odds
    """
    if not odds_dict or len(odds_dict) < 2:
        return None
    
    # Define os pesos para cada casa
    weights = {
        'Bet365': 0.35,
        'Pitaco': 0.35,
        'KTO': 0.20,
        'Blaze': 0.10
    }
    
    # Calcula a média ponderada das odds
    weighted_sum = 0
    total_weight = 0
    
    for casa, odd in odds_dict.items():
        if odd is not None and odd > 0 and casa in weights:
            weighted_sum += odd * weights[casa]
            total_weight += weights[casa]
    
    if total_weight == 0:
        return None
    
    # Média ponderada das odds
    weighted_avg_odds = weighted_sum / total_weight
    
    # Retorna a probabilidade implícita da média ponderada
    return 1 / weighted_avg_odds

def analyze_kelly_opportunities(players_data):
    """
    Analisa oportunidades de Kelly para cada jogador.
    """
    kelly_analysis = []
    
    for player in players_data:
        nome = player['nome']
        odds_dict = {k: v for k, v in player.items() if k in ['Pitaco', 'Blaze', 'Bet365', 'KTO'] and v is not None}
        
        if len(odds_dict) < 2:  # Precisa de pelo menos 2 casas para análise
            continue
        
        # Estima probabilidade verdadeira baseada na média ponderada das odds
        true_prob = estimate_true_probability_from_odds(odds_dict)
        
        if true_prob is None:
            continue
        
        player_analysis = {
            'nome': nome,
            'probabilidade_estimada': round(true_prob, 4),
            'casas': {}
        }
        
        # Analisa cada casa de apostas
        for casa, odds in odds_dict.items():
            implied_prob = calculate_implied_probability(odds)
            ev = calculate_expected_value(odds, true_prob)
            kelly_real = calculate_kelly_fraction_unlimited(odds, true_prob)  # Kelly sem limite
            kelly_fraction = calculate_kelly_fraction(odds, true_prob)  # Kelly com limite de 2%
            conservative_fraction, conservative_recommendation = suggest_conservative_fraction(kelly_fraction)
            
            player_analysis['casas'][casa] = {
                'odds': odds,
                'probabilidade_implícita': round(implied_prob, 4),
                'valor_esperado': round(ev, 4),
                'fração_kelly_real': round(kelly_real, 4) if kelly_real else None,  # NOVO: Kelly matemático puro
                'fração_kelly_com_limite_2%': round(kelly_fraction, 4),  # Kelly limitado a 2%
                'fração_kelly_conservadora': round(conservative_fraction, 4) if conservative_fraction else None,
                'recomendação_conservadora': conservative_recommendation,
                'recomendação_original': 'APOSTAR' if ev > 0 and kelly_fraction > 0.01 else 'NÃO APOSTAR'
            }
        
        kelly_analysis.append(player_analysis)
    
    return kelly_analysis

# Lista para armazenar nomes unificados
final_results = []

# Percorre cada casa e cria um registro para cada jogador
for casa_data in data:
    casa = casa_data['casa']
    for item in casa_data['items']:
        original_name = item.get('nome')
        if not original_name:
            continue

        # Cria um novo registro para cada jogador (sem unificação prévia)
        # Agora também inclui a linha (1+ ou 2+)
        linha = item.get('linha', '1+')  # Default para 1+ se não especificado
        val = parse_odds(item.get('odd'))
        final_results.append({
            'nome': original_name,
            'linha': linha,
            'Pitaco': None,
            'Blaze': None,
            'Bet365': None,
            'KTO': None,
            casa: val
        })

# Aplica unificação genérica de jogadores duplicados
final_results = unify_duplicate_players(final_results)

# Exibe resultado unificado
print("--- RESULTADO UNIFICADO ---")
for r in final_results:
    print(r)

# --- Highlight: maiores diferenças de odds por linha (1+ e 2+) ---
highlight_1_plus = []
highlight_2_plus = []

for record in final_results:
    linha = record.get('linha', '1+')
    # Pega apenas as odds que não são None
    odds = [v for k, v in record.items() if k in ['Pitaco', 'Blaze', 'Bet365', 'KTO'] and v is not None]
    
    # Considera apenas se houver pelo menos 2 casas com odd diferente
    if len(set(odds)) >= 2:
        diff = max(odds) - min(odds)
        highlight_item = {
            'nome': record['nome'],
            'linha': linha,
            'diferença_max': diff,
            'odds': {k: v for k, v in record.items() if k in ['Pitaco', 'Blaze', 'Bet365', 'KTO'] and v is not None}
        }
        
        if linha == '1+':
            highlight_1_plus.append(highlight_item)
        elif linha == '2+':
            highlight_2_plus.append(highlight_item)

# Ordena pela maior diferença
highlight_1_plus_sorted = sorted(highlight_1_plus, key=lambda x: x['diferença_max'], reverse=True)
highlight_2_plus_sorted = sorted(highlight_2_plus, key=lambda x: x['diferença_max'], reverse=True)

# Mostra todas as diferenças
print(f"\n--- HIGHLIGHT: {len(highlight_1_plus_sorted)} maiores diferenças de odds para 1+ FALTAS ---")
for h in highlight_1_plus_sorted[:10]:  # Top 10
    print(f"{h['nome']} - Diferença: {h['diferença_max']:.3f} - Odds: {h['odds']}")

print(f"\n--- HIGHLIGHT: {len(highlight_2_plus_sorted)} maiores diferenças de odds para 2+ FALTAS ---")
for h in highlight_2_plus_sorted[:10]:  # Top 10
    print(f"{h['nome']} - Diferença: {h['diferença_max']:.3f} - Odds: {h['odds']}")

# === ANÁLISE DO CRITÉRIO DE KELLY ===
print(f"\n=== ANÁLISE DO CRITÉRIO DE KELLY ===")
kelly_analysis = analyze_kelly_opportunities(final_results)

# Filtra apenas oportunidades com valor esperado positivo e fração conservadora
# APENAS PARA BET365
profitable_opportunities = []
for analysis in kelly_analysis:
    for casa, data in analysis['casas'].items():
        # Filtra apenas Bet365
        if casa != 'Bet365':
            continue
            
        if (data['valor_esperado'] > 0 and 
            data['fração_kelly_conservadora'] is not None and 
            data['fração_kelly_conservadora'] > 0.005):  # Mínimo 0.5%
            
            profitable_opportunities.append({
                'jogador': analysis['nome'],
                'casa': casa,
                'odds': data['odds'],
                'prob_estimada': analysis['probabilidade_estimada'],
                'prob_implícita': data['probabilidade_implícita'],
                'valor_esperado': data['valor_esperado'],
                'fração_kelly_real': data['fração_kelly_real'],
                'fração_kelly_com_limite_2%': data['fração_kelly_com_limite_2%'],
                'fração_kelly_conservadora': data['fração_kelly_conservadora'],
                'recomendação': data['recomendação_conservadora']
            })

# Ordena por valor esperado (maior primeiro)
profitable_opportunities.sort(key=lambda x: x['valor_esperado'], reverse=True)

print(f"Encontradas {len(profitable_opportunities)} oportunidades lucrativas (VERSÃO CONSERVADORA):")
print("📊 Valores sugeridos: 0.5%, 0.75%, 1.0%, 1.25%, 1.5%, 1.75%, 2.0% (máximo)")
print("🎯 Limite máximo: 2% do bankroll por aposta")
print()

for i, opp in enumerate(profitable_opportunities[:10], 1):  # Mostra top 10
    print(f"{i}. {opp['jogador']} - {opp['casa']}")
    print(f"   Odds: {opp['odds']:.2f} | Prob. Estimada: {opp['prob_estimada']:.1%} | Prob. Implícita: {opp['prob_implícita']:.1%}")
    print(f"   Valor Esperado: {opp['valor_esperado']:.3f}")
    print(f"   Kelly Real (sem limite): {opp['fração_kelly_real']:.2%}")
    print(f"   Kelly com Limite 2%: {opp['fração_kelly_com_limite_2%']:.2%} | Kelly Conservador: {opp['fração_kelly_conservadora']:.2%}")
    print(f"   Recomendação: {opp['recomendação']}")
    print()

if len(profitable_opportunities) > 10:
    print(f"... e mais {len(profitable_opportunities) - 10} oportunidades")

# Salva o resultado completo em arquivo JSON
resultado_completo = {
    "jogo": f"{time_mandante} vs {time_visitante}",
    "data_processamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "jogadores": final_results,
    "maiores_diferencas_1_plus": highlight_1_plus_sorted,  # Salva todas as diferenças para 1+
    "maiores_diferencas_2_plus": highlight_2_plus_sorted,  # Salva todas as diferenças para 2+
    "analise_kelly": {
        "metodologia": {
            "tipo": "CRITÉRIO DE KELLY CONSERVADOR COM MÉDIA PONDERADA",
            "limite_maximo_bankroll": "2%",
            "valores_sugeridos": ["0.5%", "0.75%", "1.0%", "1.25%", "1.5%", "1.75%", "2.0%"],
            "filtro_minimo": "0.5% do bankroll",
            "pesos_casas": {
                "Bet365": "35%",
                "Pitaco": "35%",
                "KTO": "20%",
                "Blaze": "10%"
            },
            "campos_kelly": {
                "fração_kelly_real": "Valor matemático puro do critério de Kelly (sem limite)",
                "fração_kelly_com_limite_2%": "Kelly limitado a máximo 2% do bankroll",
                "fração_kelly_conservadora": "Valor sugerido conservador (0.5%, 0.75%, 1%, 1.25%, 1.5%, 1.75%, 2%)"
            },
            "descricao": "Versão conservadora que limita apostas a no máximo 2% do bankroll, usando média ponderada das odds para estimar probabilidade verdadeira. Casas mais estabelecidas (Bet365, Pitaco) têm peso maior (35% cada) vs casas menores (KTO 20%, Blaze 10%). As oportunidades lucrativas mostradas são APENAS para Bet365. Inclui 3 valores de Kelly: Real (matemático puro), Com Limite 2% e Conservador (sugestão)."
        },
        "total_analisados": len(kelly_analysis),
        "oportunidades_lucrativas": len(profitable_opportunities),
        "top_oportunidades": profitable_opportunities[:20],  # Top 20 oportunidades
        "analise_completa": kelly_analysis  # Análise completa de todos os jogadores
    }
}

# Salva no arquivo JSON
with open(nome_arquivo, 'w', encoding='utf-8') as f:
    json.dump(resultado_completo, f, ensure_ascii=False, indent=4)

print(f"\n✅ Resultado unificado salvo em: {nome_arquivo}")
print(f"📊 Total de jogadores únicos: {len(final_results)}")
print(f"🎯 Maiores diferenças 1+ encontradas: {len(highlight_1_plus_sorted)}")
print(f"🎯 Maiores diferenças 2+ encontradas: {len(highlight_2_plus_sorted)}")
print(f"💰 Oportunidades Kelly analisadas: {len(kelly_analysis)}")
print(f"🚀 Oportunidades lucrativas encontradas: {len(profitable_opportunities)}")
print(f"🔄 Unificação automática aplicada com sucesso!")
print(f"📈 Análise do critério de Kelly CONSERVADOR concluída!")
print(f"🛡️  Limite máximo: 2% do bankroll por aposta")
print(f"💡 Valores sugeridos: 0.5%, 0.75%, 1.0%, 1.25%, 1.5%, 1.75%, 2.0%")