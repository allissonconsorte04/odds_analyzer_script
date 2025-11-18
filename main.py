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
        "extract odds - blaze.py",
        "extract odds - bet365.py", 
        "extract odds - pitaco.py",
        "extract odds - estrela.py"
    ]
    
    print("=== EXECUTANDO SCRIPTS DE EXTRAÇÃO ===")
    
    for script in scripts:
        try:
            print(f"Executando {script}...")
            result = subprocess.run([sys.executable, script], 
                                  capture_output=True, 
                                  text=True, 
                                  encoding='utf-8')
            
            if result.returncode == 0:
                print(f"✓ {script} executado com sucesso")
            else:
                print(f"✗ Erro ao executar {script}:")
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
    
    # Carrega Estrela
    with open('estrela.json', 'r', encoding='utf-8') as f:
        estrela_data = json.load(f)
        data.append({
            "casa": "Estrela",
            "items": [{"nome": item["nome"], "odd": item["odd"]} for item in estrela_data]
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
    
    # Verificar se um nome contém o outro
    if norm1 in norm2 and len(norm1) < len(norm2):
        return True, norm2
    if norm2 in norm1 and len(norm2) < len(norm1):
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
    
    if words1 and words2:
        # Similaridade de Jaccard (intersecção / união)
        word_similarity = len(words1.intersection(words2)) / len(words1.union(words2))
        
        # Verificar se um conjunto de palavras está contido no outro (mais restritivo)
        if (words1.issubset(words2) or words2.issubset(words1)) and len(words1) >= 2 and len(words2) >= 2:
            containment_similarity = 0.85  # Alta similaridade para contenção
        else:
            containment_similarity = 0
        
        # Verificar se há sobreposição significativa de palavras (ex: Alan Franco vs Alan Steven Franco)
        common_words = words1.intersection(words2)
        
        # Verificar se há palavras significativas em comum (ex: A. Cabral vs Arthur Cabral)
        # Verifica se há pelo menos uma palavra com 4+ caracteres em comum
        significant_common_words = [word for word in common_words if len(word) >= 4]
        if (len(significant_common_words) >= 1 and 
            len(words1) >= 2 and len(words2) >= 2):
            first_name_similarity = 0.8  # Alta similaridade se há palavra significativa em comum
        else:
            first_name_similarity = 0
        if (len(common_words) >= 2 and  # Pelo menos 2 palavras em comum
            len(words1) >= 2 and len(words2) >= 2 and
            len(common_words) / max(len(words1), len(words2)) >= 0.5):  # Pelo menos 50% de sobreposição
            word_overlap_similarity = 0.85
        else:
            word_overlap_similarity = 0
        
        # Verificar casos específicos como "Alan Franco" vs "Alan Steven Franco"
        # Se temos pelo menos 2 palavras em comum e uma das palavras tem pelo menos 4 caracteres
        if (len(common_words) >= 2 and 
            any(len(word) >= 4 for word in common_words) and
            len(words1) >= 2 and len(words2) >= 2):
            specific_case_similarity = 0.9
        else:
            specific_case_similarity = 0
        
        combined_similarity = max(basic_similarity, word_similarity, containment_similarity, first_name_similarity, word_overlap_similarity, specific_case_similarity)
    else:
        combined_similarity = basic_similarity
    
    return combined_similarity, None

def unify_duplicate_players(players, similarity_threshold=0.75):
    """
    Unifica jogadores duplicados automaticamente baseado na similaridade dos nomes.
    Agora considera a linha (1+ ou 2+) para unificar apenas jogadores da mesma linha.
    """
    print(f"\n=== UNIFICANDO JOGADORES DUPLICADOS (threshold: {similarity_threshold}) ===")
    
    # Separar jogadores por linha
    players_1_plus = [p for p in players if p.get('linha') == '1+']
    players_2_plus = [p for p in players if p.get('linha') == '2+']
    
    unified_list = []
    
    # Processar cada linha separadamente
    for linha_players, linha in [(players_1_plus, '1+'), (players_2_plus, '2+')]:
        if not linha_players:
            continue
            
        # Encontrar duplicatas
        duplicates = []
        processed = set()
        
        for i, player1 in enumerate(linha_players):
            if i in processed:
                continue
                
            current_group = [i]
            name1 = player1['nome']
            
            for j, player2 in enumerate(linha_players[i+1:], i+1):
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
        
        if duplicates:
            print(f"Encontrados {len(duplicates)} grupos de jogadores duplicados na linha {linha}:")
            for i, group in enumerate(duplicates):
                print(f"Grupo {i+1}: {[linha_players[idx]['nome'] for idx in group]}")
        
        # Criar novo dicionário para jogadores unificados
        unified_players = {}
        processed_indices = set()
        
        # Processar grupos de duplicatas
        for group in duplicates:
            # Escolher o nome prioritário: 1. Bet365, 2. Nome mais completo
            group_players = [linha_players[idx] for idx in group]
            
            # Verificar se algum jogador do grupo tem odd na Bet365
            bet365_players = [p for p in group_players if p.get('Bet365') is not None]
            
            if bet365_players:
                # Prioriza o nome da Bet365
                main_player = bet365_players[0]
            else:
                # Se não houver Bet365, usa o nome mais completo
                main_player = max(group_players, key=lambda x: len(x.get('nome', '')))
            
            main_name = main_player.get('nome')
            
            # Combinar odds de todos os jogadores do grupo
            combined_odds = {
                'nome': main_name,
                'linha': linha,
                'Pitaco': None,
                'Blaze': None,
                'Estrela': None,
                'Bet365': None
            }
            
            for player in group_players:
                for casa in ['Pitaco', 'Blaze', 'Estrela', 'Bet365']:
                    if player.get(casa) is not None:
                        # Se a casa já tem uma odd, manter a menor (mais favorável)
                        if combined_odds[casa] is None or player[casa] < combined_odds[casa]:
                            combined_odds[casa] = player[casa]
            
            unified_players[main_name] = combined_odds
            processed_indices.update(group)
            
            print(f"Unificado ({linha}): {main_name} <- {[p.get('nome') for p in group_players]}")
        
        # Adicionar jogadores não duplicados
        for i, player in enumerate(linha_players):
            if i not in processed_indices:
                unified_players[player.get('nome')] = {
                    'nome': player.get('nome'),
                    'linha': linha,
                    'Pitaco': player.get('Pitaco'),
                    'Blaze': player.get('Blaze'),
                    'Estrela': player.get('Estrela'),
                    'Bet365': player.get('Bet365')
                }
        
        unified_list.extend(list(unified_players.values()))
    
    # Ordenar por nome e linha
    unified_list.sort(key=lambda x: (x.get('nome', ''), x.get('linha', '')))
    
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

def estimate_true_probability_from_odds(odds_list):
    """
    Estima a probabilidade "verdadeira" baseada na média das odds disponíveis.
    Remove outliers extremos para uma estimativa mais robusta.
    """
    if not odds_list or len(odds_list) < 2:
        return None
    
    # Converte odds em probabilidades
    probabilities = [1/odd for odd in odds_list if odd is not None and odd > 0]
    
    if len(probabilities) < 2:
        return None
    
    # Remove outliers (valores muito distantes da média)
    mean_prob = sum(probabilities) / len(probabilities)
    filtered_probs = [p for p in probabilities if abs(p - mean_prob) <= 2 * (max(probabilities) - min(probabilities))]
    
    if not filtered_probs:
        filtered_probs = probabilities
    
    # Retorna a média das probabilidades filtradas
    return sum(filtered_probs) / len(filtered_probs)

def analyze_kelly_opportunities(players_data):
    """
    Analisa oportunidades de Kelly para cada jogador.
    """
    kelly_analysis = []
    
    for player in players_data:
        nome = player['nome']
        odds_dict = {k: v for k, v in player.items() if k in ['Pitaco', 'Blaze', 'Estrela', 'Bet365'] and v is not None}
        
        if len(odds_dict) < 2:  # Precisa de pelo menos 2 casas para análise
            continue
        
        # Estima probabilidade verdadeira baseada em todas as odds
        all_odds = list(odds_dict.values())
        true_prob = estimate_true_probability_from_odds(all_odds)
        
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
            kelly_fraction = calculate_kelly_fraction(odds, true_prob)
            conservative_fraction, conservative_recommendation = suggest_conservative_fraction(kelly_fraction)
            
            player_analysis['casas'][casa] = {
                'odds': odds,
                'probabilidade_implícita': round(implied_prob, 4),
                'valor_esperado': round(ev, 4),
                'fração_kelly_original': round(kelly_fraction, 4),
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
            'Estrela': None,
            'Bet365': None,
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
    odds = [v for k, v in record.items() if k in ['Pitaco', 'Blaze', 'Estrela', 'Bet365'] and v is not None]
    
    # Considera apenas se houver pelo menos 2 casas com odd diferente
    if len(set(odds)) >= 2:
        diff = max(odds) - min(odds)
        highlight_item = {
            'nome': record.get('nome'),
            'linha': linha,
            'diferença_max': diff,
            'odds': {k: v for k, v in record.items() if k in ['Pitaco', 'Blaze', 'Estrela', 'Bet365'] and v is not None}
        }
        
        if linha == '1+':
            highlight_1_plus.append(highlight_item)
        elif linha == '2+':
            highlight_2_plus.append(highlight_item)

# Ordena pela maior diferença
highlight_1_plus_sorted = sorted(highlight_1_plus, key=lambda x: x['diferença_max'], reverse=True)
highlight_2_plus_sorted = sorted(highlight_2_plus, key=lambda x: x['diferença_max'], reverse=True)

# Mostra todas as diferenças
print(f"\n--- HIGHLIGHT: {len(highlight_1_plus_sorted)} maiores diferenças de odds (1+) ---")
for h in highlight_1_plus_sorted:
    print(h)

print(f"\n--- HIGHLIGHT: {len(highlight_2_plus_sorted)} maiores diferenças de odds (2+) ---")
for h in highlight_2_plus_sorted:
    print(h)

# === ANÁLISE DO CRITÉRIO DE KELLY ===
print(f"\n=== ANÁLISE DO CRITÉRIO DE KELLY ===")
kelly_analysis = analyze_kelly_opportunities(final_results)

# Filtra apenas oportunidades com valor esperado positivo e fração conservadora
profitable_opportunities = []
for analysis in kelly_analysis:
    for casa, data in analysis['casas'].items():
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
                'fração_kelly_original': data['fração_kelly_original'],
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
    print(f"   Kelly Original: {opp['fração_kelly_original']:.1%} | Kelly Conservador: {opp['fração_kelly_conservadora']:.1%}")
    print(f"   Recomendação: {opp['recomendação']}")
    print()

if len(profitable_opportunities) > 10:
    print(f"... e mais {len(profitable_opportunities) - 10} oportunidades")

# Salva o resultado completo em arquivo JSON
resultado_completo = {
    "jogo": f"{time_mandante} vs {time_visitante}",
    "data_processamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "jogadores": final_results,
    "maiores_diferencas_1_plus": highlight_1_plus_sorted,  # Salva todas as diferenças 1+
    "maiores_diferencas_2_plus": highlight_2_plus_sorted,  # Salva todas as diferenças 2+
    "analise_kelly": {
        "metodologia": {
            "tipo": "CRITÉRIO DE KELLY CONSERVADOR",
            "limite_maximo_bankroll": "2%",
            "valores_sugeridos": ["0.5%", "0.75%", "1.0%", "1.25%", "1.5%", "1.75%", "2.0%"],
            "filtro_minimo": "0.5% do bankroll",
            "descricao": "Versão conservadora que limita apostas a no máximo 2% do bankroll, sugerindo valores específicos para gestão de risco"
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
print(f"🎯 Maiores diferenças encontradas (1+): {len(highlight_1_plus_sorted)}")
print(f"🎯 Maiores diferenças encontradas (2+): {len(highlight_2_plus_sorted)}")
print(f"💰 Oportunidades Kelly analisadas: {len(kelly_analysis)}")
print(f"🚀 Oportunidades lucrativas encontradas: {len(profitable_opportunities)}")
print(f"🔄 Unificação automática aplicada com sucesso!")
print(f"📈 Análise do critério de Kelly CONSERVADOR concluída!")
print(f"🛡️  Limite máximo: 2% do bankroll por aposta")
print(f"💡 Valores sugeridos: 0.5%, 0.75%, 1.0%, 1.25%, 1.5%, 1.75%, 2.0%")