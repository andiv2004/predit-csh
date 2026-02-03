from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import time
import os
import json
import random
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from functools import lru_cache
from datetime import datetime, timedelta
from auth import require_auth



########################3
#DEPENDINTE EXTERNE
def fetch_team_season_stats(team_number, season=2025):
    # Query extins pentru a include și evenimentele (pentru OPR_History)
    query = gql(f"""    
    query {{
      teamByNumber(number: {team_number}) {{
        number
        name
        # Pentru mediile de meci (Net Points, Auto, RP-uri)
        matches(season: {season}) {{
          match {{
            matchNum
            teams {{
              teamNumber
              alliance
            }}
            scores {{
              ... on MatchScores2025 {{
                red {{
                  totalPointsNp
                  autoPoints
                  dcPoints
                  goalRp
                  patternRp
                  movementRp
                }}
                blue {{
                  totalPointsNp
                  autoPoints
                  dcPoints
                  goalRp
                  patternRp
                  movementRp
                }}
              }}
            }}
          }}
        }}
        # Pentru istoricul OPR-urilor
        events(season: {season}) {{
          event {{
            name
            updatedAt
          }}
          stats {{
            ... on TeamEventStats2025 {{
              opr {{
                totalPointsNp
              }}
            }}
          }}
        }}
        # OPR-ul global actual
        quickStats(season: {season}) {{
          tot {{ value }}
        }}
      }}
    }}
    """)

    result = client.execute(query)
    team_data = result['teamByNumber']

    if not team_data or not team_data['matches']:
        return {"error": f"Nu s-au gasit date pentru echipa {team_number}."}

    # --- LOGICA EXISTENTĂ (Mediile pe meci) ---
    opr_season = team_data['quickStats']['tot']['value'] if team_data['quickStats'] else 0
    match_records = []

    for m_entry in team_data['matches']:
        m = m_entry['match']
        if not m['scores']: continue

        team_in_match = next((t for t in m['teams'] if t['teamNumber'] == team_number), None)

        if team_in_match:
            alliance = team_in_match['alliance'].lower()
            opponent = 'blue' if alliance == 'red' else 'red'
            my_score_data = m['scores'][alliance]
            opp_score_data = m['scores'][opponent]

            g_rp = 1 if my_score_data.get('goalRp') else 0
            p_rp = 1 if my_score_data.get('patternRp') else 0
            m_rp = 1 if my_score_data.get('movementRp') else 0

            win = my_score_data['totalPointsNp'] > opp_score_data['totalPointsNp']
            r_score = g_rp + p_rp + m_rp + (3 if win else 0)

            match_records.append({
                'totalPointsNp': my_score_data['totalPointsNp'],
                'autoPoints': my_score_data['autoPoints'],
                'dcPoints': my_score_data['dcPoints'],
                'ranking_score': r_score,
                'GoalRP_Rate': g_rp,
                'PatternRP_Rate': p_rp,
                'MovementRP_Rate': m_rp
            })

    # Calculare Medii
    df_season = pd.DataFrame(match_records)
    season_averages = df_season.mean().to_dict()

    # --- LOGICA NOUĂ (Istoric OPR ordonat) ---
    events_raw = team_data.get('events', [])
    # Sortăm evenimentele după data actualizării
    events_sorted = sorted(
        events_raw,
        key=lambda x: x['event']['updatedAt'] if x['event']['updatedAt'] else ""
    )

    opr_history = []
    for e in events_sorted:
        if e['stats'] and 'opr' in e['stats']:
            val = e['stats']['opr']['totalPointsNp']
            opr_history.append(round(val, 1))

    # Adăugăm datele în dicționarul final
    season_averages['OPR_History'] = opr_history
    season_averages['OPR_Season'] = round(opr_season, 2)
    season_averages['Matches_Played'] = len(df_season)
    season_averages['Team'] = team_number
    season_averages['Name'] = team_data['name']

    return season_averages

def get_team_full_metrics(team_num, teams_data):
    """
    Extrage setul complet de metrice pentru o echipă din DataFrame-ul teams_data.
    Include acum și valoarea 'Predicted_OPR' necesară pentru simulările de meci.
    """
    row = teams_data[teams_data['Team'] == team_num]

    if not row.empty:
        r = row.iloc[0]

        return {
            'name': r['Name'],
            'opr': r['OPR_Season'],
            'Predicted_OPR': r.get('Predicted_OPR', 0), # ADAUGAT AICI
            'net': r['totalPointsNp'],
            'auto': r['autoPoints'],
            'rs': r['ranking_score'],
            'goal_rate': r.get('GoalRP_Rate', 0),
            'pattern_rate': r.get('PatternRP_Rate', 0),
            'move_rate': r.get('MovementRP_Rate', 0),
            'opr_history': r.get('OPR_History', []),
            'matches_played': r.get('Matches_Played', 0)
        }

    # Fallback: Adăugăm Predicted_OPR: 0 și aici pentru siguranță
    return {
        'name': f"Unknown ({team_num})",
        'opr': 0,
        'Predicted_OPR': 0, # ADAUGAT AICI
        'net': 0,
        'auto': 0,
        'rs': 0,
        'goal_rate': 0,
        'pattern_rate': 0,
        'move_rate': 0,
        'opr_history': [],
        'matches_played': 0
    }

import numpy as np

def predict_team_opr_weighted(teams_data, team_number, alpha=0.5):
    """
    Predice următorul OPR pentru o echipă folosind Weighted Least Squares
    pe baza coloanei 'OPR_History' din teams_data.
    """
    # 1. Extragem rândul echipei
    row = teams_data[teams_data['Team'] == team_number]

    if row.empty:
        return 0.0

    # 2. Preluăm istoricul OPR (lista de totalPointsNp per eveniment)
    history = row['OPR_History'].iloc[0]

    # Verificare: avem nevoie de cel puțin 2 puncte pentru regresie
    if not history or len(history) == 0:
        return row['OPR_Season'].iloc[0] # Fallback la media de sezon
    if len(history) == 1:
        return float(history[0]) # Nu există trend, returnăm singura valoare

    # 3. Pregătim datele pentru regresie
    Y = np.array(history)
    X = np.arange(len(Y))

    # 4. Calculăm ponderile exponențiale
    weights = np.exp(alpha * X)

    # 5. Calculăm Regresia Ponderată (WLS)
    # polyfit returnează [panta, intercept]
    coef = np.polyfit(X, Y, 1, w=weights)
    p = np.poly1d(coef)

    # 6. Prezicem pentru următorul eveniment (indexul len(Y))
    next_index = len(Y)
    prediction = p(next_index)

    # Opțional: constrângem predicția să nu fie negativă (fizic imposibil în FTC)
    return round(prediction, 2)

###########################
##############################
##############################



# Configurează build-ul React
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend', 'build')
CACHE_DIR = os.path.join(BASE_DIR, '.cache')

# Creează directorul cache dacă nu există
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache de date
cache = {}
CACHE_EXPIRY = 7200

def get_cache_file(key):
    """Obține path-ul fisierului de cache"""
    return os.path.join(CACHE_DIR, f"{key}.json")

def load_cache_from_disk():
    """Încarcă cache-ul din fisierele salvate"""
    global cache
    if not os.path.exists(CACHE_DIR):
        return
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(CACHE_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    key = filename[:-5]  # Elimini .json
                    cache[key] = (data, data.get('_expiry'))
                    print(f"✨ Încărcat din disk: {key}")
            except Exception as e:
                print(f"⚠️ Eroare la încărcarea {filename}: {e}")

def get_cache(key):
    """Obține din cache (memoria sau disk) dacă nu a expirat"""
    # 1. Încearcă să găsească în memoria RAM (cache dict)
    if key in cache:
        data, expiry_time_str = cache[key]
        if expiry_time_str:
            expiry_time = datetime.fromisoformat(expiry_time_str)
            if datetime.now() < expiry_time:
                print(f"✨ Cache HIT (RAM) pentru {key}")
                return data
        # Cache a expirat, șterge-l
        del cache[key]
        cache_file = get_cache_file(key)
        if os.path.exists(cache_file):
            os.remove(cache_file)
        return None
    
    # 2. FALLBACK: Încearcă să găsească pe disk dacă nu e în RAM
    cache_file = get_cache_file(key)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                expiry_time_str = data.get('_expiry')
                
                # Verifică dacă a expirat
                if expiry_time_str:
                    expiry_time = datetime.fromisoformat(expiry_time_str)
                    if datetime.now() < expiry_time:
                        # Cache valid! Încarcă-l în RAM pentru viitoare
                        cache[key] = (data, expiry_time_str)
                        print(f"✨ Cache HIT (DISK) pentru {key} - reîncărcat în RAM")
                        return data
                    else:
                        # Cache expirat, șterge-l
                        os.remove(cache_file)
                        print(f"⏰ Cache expirat pentru {key}")
                        return None
        except Exception as e:
            print(f"⚠️ Eroare la citirea cache din disk ({key}): {e}")
            return None
    
    return None

def set_cache(key, data):
    """Salvează în cache și pe disk - NU suprascrie dacă deja există și e valid"""
    cache_file = get_cache_file(key)
    
    # VERIFICARE: Dacă fișierul deja există și e valid, NU rescrie pe disk
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                existing_data = json.load(f)
                expiry_time_str = existing_data.get('_expiry')
                
                # Dacă cache-ul nu a expirat, nu rescriu nimic
                if expiry_time_str:
                    expiry_time = datetime.fromisoformat(expiry_time_str)
                    if datetime.now() < expiry_time:
                        print(f"✅ Cache deja există și e valid pentru {key} - NU rescriu")
                        # Doar încarcă în RAM dacă nu e deja acolo
                        if key not in cache:
                            cache[key] = (existing_data, expiry_time_str)
                        return
        except Exception as e:
            print(f"⚠️ Eroare la verificarea cache existent: {e}")
    
    # Dacă nu există sau a expirat, rescrie complet
    expiry_time = datetime.now() + timedelta(seconds=CACHE_EXPIRY)
    expiry_str = expiry_time.isoformat()
    
    # Convertim DataFrame în dict pentru serializare JSON
    if isinstance(data, tuple) and len(data) == 2:
        df, event_name = data
        # Convertim DataFrame în JSON-serializable format
        json_data = {
            'data': df.to_dict(orient='records'),
            'event_name': event_name,
            '_expiry': expiry_str
        }
    else:
        json_data = {'_expiry': expiry_str, 'data': data}
    
    cache[key] = (json_data, expiry_str)
    
    # Salvez pe disk
    try:
        with open(cache_file, 'w') as f:
            json.dump(json_data, f, default=str)
        print(f"💾 Salvat (NOU) în cache (disk): {key}")
    except Exception as e:
        print(f"⚠️ Eroare la salvare cache: {e}")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')
CORS(app)

# Încarcă cache-ul din disk la startup
load_cache_from_disk()

# DEBUG: Afișează ce e în cache
print(f"\n📦 Cache loader STARTUP - {len(cache)} intrări în memorie")
if cache:
    for key in list(cache.keys())[:5]:  # Arată primele 5
        print(f"   - {key}")

# Configurație GraphQL
transport = RequestsHTTPTransport(url="https://api.ftcscout.org/graphql")
client = Client(transport=transport, fetch_schema_from_transport=True)

def get_event_season_report(event_code, season=2025):
    """Colectează și procesează datele de echipe pentru un eveniment"""
    # Verifică cache
    cache_key = f"{event_code}_{season}"
    cached_data = get_cache(cache_key)
    
    if cached_data:
        try:
            # Reconstituie DataFrame din dict
            df = pd.DataFrame(cached_data['data'])
            event_name = cached_data['event_name']
            print(f"✨ Cache HIT pentru {event_code}_{season}! Se folosesc datele cached.")
            return df, event_name
        except Exception as e:
            print(f"⚠️ Eroare la reconstructia cache: {e}")
            # Dacă nu poți reconstrui, continua cu fetch-ul normal
    
    try:
        # 1. Luăm lista de echipe de la eveniment
        print(f"📡 Preluăm lista de echipe pentru {event_code}...")
        event_query = gql(f"""
        query {{
          eventByCode(code: "{event_code}", season: {season}) {{
            name
            teams {{
              team {{
                number
              }}
            }}
          }}
        }}
        """)

        event_res = client.execute(event_query)
        teams_list = [t['team']['number'] for t in event_res['eventByCode']['teams']]
        event_name = event_res['eventByCode']['name']

        print(f"✅ Am găsit {len(teams_list)} echipe. Începem colectarea datelor...")

        all_team_stats = []

        for i, team_num in enumerate(teams_list):
            try:
                print(f"[{i+1}/{len(teams_list)}] Analizăm echipa {team_num}...", end="\r")
                stats = fetch_team_season_stats(team_num, season)

                if stats and isinstance(stats, dict) and "error" not in stats:
                    stats['Predicted_OPR'] = 0.0
                    all_team_stats.append(stats)

                time.sleep(0.05)  # Redus de la 0.1 pentru viteză
            except Exception as e:
                print(f"\n⚠️ Eroare la echipa {team_num}: {e}")
                continue

        if not all_team_stats:
            return None, "Nu s-au putut colecta date pentru nicio echipă!"

        # 2. Creăm DataFrame-ul
        report_df = pd.DataFrame(all_team_stats)

        # Definirea coloanelor dorite
        cols = [
            'Team', 'Name', 'ranking_score', 'OPR_Season',
            'totalPointsNp', 'autoPoints', 'dcPoints',
            'GoalRP_Rate', 'PatternRP_Rate', 'MovementRP_Rate',
            'Matches_Played', 'OPR_History', 'Predicted_OPR'
        ]

        report_df = report_df.reindex(columns=cols)

        # Convertim Team și Matches_Played la int
        report_df['Team'] = report_df['Team'].astype(int)
        report_df['Matches_Played'] = report_df['Matches_Played'].astype(int)

        # Sortăm după ranking_score
        sort_by = 'ranking_score' if 'ranking_score' in report_df.columns else report_df.columns[0]
        report_df = report_df.sort_values(by=sort_by, ascending=False)

        print(f"\n✨ Raport finalizat pentru {event_name}!")
        
        # Salvez în cache
        result = (report_df, event_name)
        set_cache(cache_key, result)
        
        return result

    except Exception as e:
        print(f"❌ Eroare generală: {e}")
        return None, str(e)

def generate_ftc_schedule_pro(teams_data, matches_per_team=6, max_retries=50):
    """
    Generează program FTC cu distribuție uniformă a meciurilor și evitare de alianțe duplicate.
    Inspirat de algoritm cu:
    - Tracker pentru match_counts (fiecare echipă știm câte meciuri a jucat)
    - Tracker pentru previous_match_teams (echipele care abia au jucat)
    - played_together set pentru a evita duplicate de alianțe
    """
    teams_list = teams_data['Team'].tolist()
    num_teams = len(teams_list)
    
    # 1. Inițializare trackers
    match_counts = {team: 0 for team in teams_list}
    played_together = set()  # Alianțe folosite
    previous_match_teams = set()  # Echipele din meciul anterior
    
    # 2. Calculare total meciuri
    total_slots_needed = num_teams * matches_per_team
    total_matches = int(total_slots_needed / 4)
    
    schedule = []
    duplicate_alliance_count = 0
    
    print(f"📊 Generare program: {num_teams} echipe, ~{total_matches} meciuri, {matches_per_team} meciuri/echipă")
    
    # 3. Bucla de generare meciuri
    for m in range(total_matches):
        valid_match_found = False
        attempts = 0
        
        candidates = []
        
        while not valid_match_found and attempts < max_retries:
            # A. Sortăm echipele după:
            #    1. Câte meciuri au jucat (puține = prioritate)
            #    2. Dacă au jucat în meciul anterior (recent = puțină prioritate)
            teams_list_copy = teams_list.copy()
            random.shuffle(teams_list_copy)
            teams_list_copy.sort(key=lambda x: (match_counts[x], x in previous_match_teams))
            
            # Luăm primele 4 echipe (cele mai "odihnite")
            candidates = teams_list_copy[:4]
            
            # Verificare siguranță
            if len(set(candidates)) < 4:
                break
            
            # B. Încercăm să formăm alianțe nefolosite
            for _ in range(5):
                random.shuffle(candidates)
                
                red_alliance = frozenset([candidates[0], candidates[1]])
                blue_alliance = frozenset([candidates[2], candidates[3]])
                
                # Verificare: alianțele nu au fost folosite înainte
                if (red_alliance not in played_together) and (blue_alliance not in played_together):
                    valid_match_found = True
                    played_together.add(red_alliance)
                    played_together.add(blue_alliance)
                    break
            
            attempts += 1
        
        # C. Fallback: acceptăm duplicate dacă nu avem încotro
        if not valid_match_found:
            duplicate_alliance_count += 1
            red_alliance = frozenset([candidates[0], candidates[1]])
            blue_alliance = frozenset([candidates[2], candidates[3]])
            played_together.add(red_alliance)
            played_together.add(blue_alliance)
        
        # D. Actualizăm contorul de meciuri
        for team in candidates:
            match_counts[team] += 1
        
        # E. Salvez cine a jucat acum (pentru meciurile viitoare)
        previous_match_teams = set(candidates)
        
        # F. Salvez meciurile
        schedule.append({
            'Match': m + 1,
            'Red 1': int(candidates[0]), 
            'Red 2': int(candidates[1]),
            'Blue 1': int(candidates[2]), 
            'Blue 2': int(candidates[3])
        })
    
    print(f"✅ Program generat: {len(schedule)} meciuri, {duplicate_alliance_count} alianțe duplicate")
    print(f"📊 Distribuție: {min(match_counts.values())} - {max(match_counts.values())} meciuri/echipă")
    
    return pd.DataFrame(schedule), duplicate_alliance_count

def run_full_schedule_prediction_v5(schedule_df, teams_data):
    """
    Generează predicții pentru meciuri folosind OPR și statistici echipelor
    """
    predictions = []

    for _, row in schedule_df.iterrows():
        r1, r2 = int(row['Red 1']), int(row['Red 2'])
        b1, b2 = int(row['Blue 1']), int(row['Blue 2'])

        # Preluăm datele echipelor
        r1_s = get_team_full_metrics(r1, teams_data)
        r2_s = get_team_full_metrics(r2, teams_data)
        b1_s = get_team_full_metrics(b1, teams_data)
        b2_s = get_team_full_metrics(b2, teams_data)

        # Sume alianțe
        red_opr = r1_s['opr'] + r2_s['opr']
        blue_opr = b1_s['opr'] + b2_s['opr']
        red_net = r1_s['net'] + r2_s['net']
        blue_net = b1_s['net'] + b2_s['net']
        red_auto = r1_s['auto'] + r2_s['auto']
        blue_auto = b1_s['auto'] + b2_s['auto']
        red_rs = r1_s['rs'] + r2_s['rs']
        blue_rs = b1_s['rs'] + b2_s['rs']

        # Algoritm predicție winner
        if red_opr > blue_opr:
            winner = "🔴 ROȘU"
            win_margin = abs(red_opr - blue_opr)
        elif blue_opr > red_opr:
            winner = "🔵 ALBASTRU"
            win_margin = abs(red_opr - blue_opr)
        else:
            winner = "⚪ EGAL"
            win_margin = 0

        predictions.append({
            'Match': int(row['Match']),
            'Red 1': r1,
            'Red 1 Name': r1_s['name'],
            'Red 2': r2,
            'Red 2 Name': r2_s['name'],
            'Blue 1': b1,
            'Blue 1 Name': b1_s['name'],
            'Blue 2': b2,
            'Blue 2 Name': b2_s['name'],
            'Red OPR': round(red_opr, 2),
            'Blue OPR': round(blue_opr, 2),
            'Red NET': round(red_net, 2),
            'Blue NET': round(blue_net, 2),
            'Red AUTO': round(red_auto, 2),
            'Blue AUTO': round(blue_auto, 2),
            'Red RS': round(red_rs, 2),
            'Blue RS': round(blue_rs, 2),
            'Winner': winner,
            'Win Margin': round(win_margin, 2)
        })

    return predictions


def calculate_predicted_rankings_stochastic(schedule_df, teams_data):
    """
    Calculează clasament pe baza programului generat
    Logică: Ranking Points din meciuri + Win Bonus + TBP1 (Tiebreaker Points 1 = Auto Points)
    """
    # Mapăm posibilele nume de coloane pentru a fi siguri
    col_map = {
        'goal': 'GoalRP_Rate' if 'GoalRP_Rate' in teams_data.columns else 'GoalRP',
        'pattern': 'PatternRP_Rate' if 'PatternRP_Rate' in teams_data.columns else 'PatternRP',
        'move': 'MovementRP_Rate' if 'MovementRP_Rate' in teams_data.columns else 'MovementRP'
    }

    stats = {int(team): {
        'RP_Sum': 0, 'TBP1_Sum': 0, 'Auto_OPR_Sum': 0, 'Wins': 0, 'Losses': 0, 'Matches': 0
    } for team in teams_data['Team'].tolist()}

    def get_team_stats(team_num):
        row = teams_data[teams_data['Team'] == team_num]
        return row.iloc[0].to_dict() if not row.empty else None

    for _, row in schedule_df.iterrows():
        red_teams = [get_team_stats(int(row['Red 1'])), get_team_stats(int(row['Red 2']))]
        blue_teams = [get_team_stats(int(row['Blue 1'])), get_team_stats(int(row['Blue 2']))]

        def roll_alliance_rp(teams, key_type):
            col_name = col_map[key_type]
            # Media probabilităților celor doi roboți
            p_alliance = sum([t.get(col_name, 0) for t in teams if t]) / len([t for t in teams if t])
            return 1 if random.random() < p_alliance else 0

        # Calculăm RP-urile din task-uri
        r_tasks = roll_alliance_rp(red_teams, 'goal') + \
                  roll_alliance_rp(red_teams, 'pattern') + \
                  roll_alliance_rp(red_teams, 'move')

        b_tasks = roll_alliance_rp(blue_teams, 'goal') + \
                  roll_alliance_rp(blue_teams, 'pattern') + \
                  roll_alliance_rp(blue_teams, 'move')

        # Win Bonus pe baza OPR
        red_opr = sum(t['OPR_Season'] for t in red_teams if t)
        blue_opr = sum(t['OPR_Season'] for t in blue_teams if t)

        red_match_rp, blue_match_rp = r_tasks, b_tasks
        red_auto = sum(t['autoPoints'] for t in red_teams if t)
        blue_auto = sum(t['autoPoints'] for t in blue_teams if t)

        if red_opr > blue_opr:
            red_match_rp += 3
            for n in [row['Red 1'], row['Red 2']]: 
                stats[int(n)]['Wins'] += 1
            for n in [row['Blue 1'], row['Blue 2']]: 
                stats[int(n)]['Losses'] += 1
        elif blue_opr > red_opr:
            blue_match_rp += 3
            for n in [row['Blue 1'], row['Blue 2']]: 
                stats[int(n)]['Wins'] += 1
            for n in [row['Red 1'], row['Red 2']]: 
                stats[int(n)]['Losses'] += 1

        # Update sume pentru medii
        for n in [row['Red 1'], row['Red 2']]:
            stats[int(n)]['RP_Sum'] += red_match_rp
            stats[int(n)]['TBP1_Sum'] += sum(t['totalPointsNp'] for t in red_teams if t)
            stats[int(n)]['Matches'] += 1
            stats[int(n)]['Auto_OPR_Sum'] += sum(t['autoPoints'] for t in red_teams if t)
        for n in [row['Blue 1'], row['Blue 2']]:
            stats[int(n)]['RP_Sum'] += blue_match_rp
            stats[int(n)]['TBP1_Sum'] += sum(t['totalPointsNp'] for t in blue_teams if t)
            stats[int(n)]['Matches'] += 1
            stats[int(n)]['Auto_OPR_Sum'] += sum(t['autoPoints'] for t in blue_teams if t)

    # Construire Rezultat Final
    rank_rows = []
    for team, data in stats.items():
        info = get_team_stats(team)
        m = data['Matches']
        rank_rows.append({
            'Echipa': team, 
            'Nume': info['Name'] if info else "Unknown",
            'Ranking Score': round(data['RP_Sum'] / m, 2) if m > 0 else 0,
            'Wins': data['Wins'],
            'Losses': data['Losses'],
            'TBP1': round(data['TBP1_Sum'] / m, 2) if m > 0 else 0,
            'OPR': round(info['OPR_Season'], 2) if info else 0,
            'Auto OPR': round(data['Auto_OPR_Sum'] / m, 2) if m > 0 else 0
        })

    ranking_df = pd.DataFrame(rank_rows).sort_values(by=['Ranking Score', 'TBP1'], ascending=False)
    ranking_df.insert(0, 'Loc', range(1, len(ranking_df) + 1))
    
    return ranking_df.reset_index(drop=True)


def convert_to_serializable(obj):
    """Convertă numpy/pandas types la Python native types pentru JSON"""
    import numpy as np
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def run_100_regional_simulations(teams_data, target_team, matches_per_team=6):
    """
    Rulează 100 simulări de regionale pentru o echipă țintă
    Returnează statistici: poziție medie, win rate, etc.
    """
    positions = []
    wins = []
    
    print(f"  🔄 Rulează 100 simulări pentru echipa {target_team}...")
    
    for i in range(100):
        try:
            # Generează schedule aleator
            result = generate_ftc_schedule_pro(teams_data, matches_per_team)
            if result is None or not isinstance(result, tuple):
                print(f"    ⚠️ Simulare {i+1}: Nu s-a putut genera schedule")
                continue
            
            schedule_df, _ = result
            
            if schedule_df is None or len(schedule_df) == 0:
                print(f"    ⚠️ Simulare {i+1}: Schedule gol")
                continue
            
            # Calculează clasament
            ranking_df = calculate_predicted_rankings_stochastic(schedule_df, teams_data)
            
            if ranking_df is None or len(ranking_df) == 0:
                print(f"    ⚠️ Simulare {i+1}: Ranking gol")
                continue
            
            # Găsește poziția echipei țintă
            target_row = ranking_df[ranking_df['Echipa'] == target_team]
            if not target_row.empty:
                position = int(target_row.iloc[0]['Loc'])
                team_wins = int(target_row.iloc[0]['Wins'])
                positions.append(position)
                wins.append(team_wins)
        except Exception as e:
            print(f"    ❌ Simulare {i+1}: {e}")
            continue
        
        if (i + 1) % 25 == 0:
            print(f"    ✓ {i+1}/100 simulări complete")
    
    if not positions:
        print(f"  ❌ Nu s-au putut finaliza simulări pentru echipa {target_team}")
        return None
    
    print(f"  ✅ {len(positions)}/100 simulări complete")
    
    return {
        'team': int(target_team),
        'simulations': 100,
        'avg_position': float(round(sum(positions) / len(positions), 2)),
        'min_position': int(min(positions)),
        'max_position': int(max(positions)),
        'avg_wins': float(round(sum(wins) / len(wins), 2)),
        'position_distribution': {
            'top_10': int(len([p for p in positions if p <= 10])),
            'top_20': int(len([p for p in positions if p <= 20])),
            'top_50': int(len([p for p in positions if p <= 50])),
        }
    }


def run_100_team_comparison(teams_data, team1, team2, matches_per_team=6):
    """
    Rulează 100 simulări separatE pentru FIECARE echipă
    Returnează statistici: comparație cu 100 simulări per echipă
    """
    print(f"  🔄 Rulează 100 simulări pentru echipa {team1}...")
    team1_results = run_100_regional_simulations(teams_data, team1, matches_per_team)
    
    print(f"  🔄 Rulează 100 simulări pentru echipa {team2}...")
    team2_results = run_100_team_comparison_helper(teams_data, team2, matches_per_team)
    
    if not team1_results or not team2_results:
        return None
    
    # Calculează cine a fost mai bun pe bază de poziție medie
    team1_better = 1 if team1_results['avg_position'] < team2_results['avg_position'] else 0
    team2_better = 1 if team2_results['avg_position'] < team1_results['avg_position'] else 0
    
    return {
        'team1': int(team1),
        'team2': int(team2),
        'team1_simulations': 100,
        'team2_simulations': 100,
        'team1_avg_position': float(team1_results['avg_position']),
        'team2_avg_position': float(team2_results['avg_position']),
        'team1_better_overall': int(team1_better),
        'team2_better_overall': int(team2_better),
        'team1_avg_wins': float(team1_results['avg_wins']),
        'team2_avg_wins': float(team2_results['avg_wins']),
        'team1_top_10': int(team1_results['position_distribution']['top_10']),
        'team2_top_10': int(team2_results['position_distribution']['top_10']),
        'team1_data': team1_results,
        'team2_data': team2_results
    }

def run_100_team_comparison_helper(teams_data, target_team, matches_per_team=6):
    """Helper pentru run_100_team_comparison - rulează 100 simulări pentru o echipă"""
    positions = []
    wins = []
    
    for i in range(100):
        try:
            result = generate_ftc_schedule_pro(teams_data, matches_per_team)
            if result is None or not isinstance(result, tuple):
                continue
            
            schedule_df, _ = result
            
            if schedule_df is None or len(schedule_df) == 0:
                continue
            
            ranking_df = calculate_predicted_rankings_stochastic(schedule_df, teams_data)
            
            if ranking_df is None or len(ranking_df) == 0:
                continue
            
            target_row = ranking_df[ranking_df['Echipa'] == target_team]
            if not target_row.empty:
                position = int(target_row.iloc[0]['Loc'])
                team_wins = int(target_row.iloc[0]['Wins'])
                positions.append(position)
                wins.append(team_wins)
        except Exception as e:
            continue
    
    if not positions:
        return None
    
    return {
        'team': int(target_team),
        'simulations': len(positions),
        'avg_position': float(round(sum(positions) / len(positions), 2)),
        'min_position': int(min(positions)),
        'max_position': int(max(positions)),
        'avg_wins': float(round(sum(wins) / len(wins), 2)),
        'position_distribution': {
            'top_10': int(len([p for p in positions if p <= 10])),
            'top_20': int(len([p for p in positions if p <= 20])),
            'top_50': int(len([p for p in positions if p <= 50])),
        }
    }


@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de verificare status"""
    return jsonify({"status": "ok", "message": "Server is running"}), 200

@app.route('/api/event/<event_code>', methods=['GET'])
def get_event_data(event_code):
    """
    Endpoint pentru a obține datele unui eveniment
    Parametri query: season (default: 2025)
    """
    try:
        season = request.args.get('season', 2025, type=int)
        report_df, event_name = get_event_season_report(event_code, season)
        
        if report_df is None:
            return jsonify({"error": event_name}), 400
        
        # Convertim DataFrame în JSON
        data = report_df.to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "event": event_code,
            "event_name": event_name,
            "season": season,
            "teams_count": len(data),
            "data": data
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/events', methods=['POST'])
def analyze_multiple_events():
    """Endpoint pentru a analiza multiple evenimente"""
    try:
        event_codes = request.json.get('event_codes', [])
        season = request.json.get('season', 2025)
        
        results = {}
        for event_code in event_codes:
            report_df, event_name = get_event_season_report(event_code, season)
            if report_df is not None:
                results[event_code] = {
                    "event_name": event_name,
                    "data": report_df.to_dict(orient='records')
                }
        
        return jsonify({"success": True, "results": results}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def fetch_event_matches(event_code, season=2025):
    """Fetch-ează meciurile Quals ale unui eveniment din API GraphQL"""
    query = gql("""
    query ExampleQuery($season: Int!, $code: String!) {
      eventByCode(season: $season, code: $code) {
        matches {
          matchNum
          tournamentLevel
          teams {
            teamNumber
            alliance
          }
        }
      }
    }
    """)
    
    try:
        result = client.execute(
            query,
            variable_values={"season": season, "code": event_code}
        )
        all_matches = result.get('eventByCode', {}).get('matches', [])
        
        # Filtrează doar meciurile din Quals
        quals_matches = [m for m in all_matches if m.get('tournamentLevel', '').lower() == 'quals']
        
        print(f"📥 Meciuri găsite: {len(all_matches)} totale, {len(quals_matches)} Quals")
        
        return quals_matches
    except Exception as e:
        print(f"❌ Eroare la fetch meciuri: {e}")
        return None

def convert_real_matches_to_schedule(matches):
    """Convertește lista de meciuri din API în format schedule DataFrame"""
    schedule_data = []
    
    for match in matches:
        match_num = match.get('matchNum', 0)
        teams = match.get('teams', [])
        
        # Separăm echipele roșii și albastre
        red_teams = [t['teamNumber'] for t in teams if t.get('alliance', '').lower() == 'red']
        blue_teams = [t['teamNumber'] for t in teams if t.get('alliance', '').lower() == 'blue']
        
        if len(red_teams) >= 2 and len(blue_teams) >= 2:
            schedule_data.append({
                'Match': match_num,
                'Red 1': red_teams[0],
                'Red 2': red_teams[1],
                'Blue 1': blue_teams[0],
                'Blue 2': blue_teams[1]
            })
    
    return pd.DataFrame(schedule_data)

@app.route('/api/generate-schedule/<event_code>', methods=['GET'])
def generate_schedule(event_code):
    """Generează program FTC pentru un eveniment"""
    try:
        season = request.args.get('season', 2025, type=int)
        matches_per_team = request.args.get('matches_per_team', 6, type=int)
        
        # Preluă datele evenimentului
        report_df, event_name = get_event_season_report(event_code, season)
        
        if report_df is None:
            return jsonify({"error": "Event not found"}), 404
        
        # Generează schedule-ul
        schedule_df, duplicates = generate_ftc_schedule_pro(report_df, matches_per_team)
        
        if len(schedule_df) == 0:
            return jsonify({"error": "Nu s-au putut genera meciuri"}), 400
        
        print(f"📊 Program generat: {len(schedule_df)} meciuri, {duplicates} alianțe duplicate")
        
        return jsonify({
            "success": True,
            "event": event_code,
            "event_name": event_name,
            "season": season,
            "matches_count": len(schedule_df),
            "duplicate_alliances": duplicates,
            "schedule": schedule_df.to_dict(orient='records')
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/import-schedule/<event_code>', methods=['GET'])
def import_schedule(event_code):
    """Importă programul real de meciuri din eveniment"""
    try:
        season = request.args.get('season', 2025, type=int)
        
        # Fetch-ează meciurile din API
        matches = fetch_event_matches(event_code, season)
        
        if not matches:
            return jsonify({"error": "No matches found for this event"}), 404
        
        # Convertește meciurile în format schedule
        schedule_df = convert_real_matches_to_schedule(matches)
        
        if len(schedule_df) == 0:
            return jsonify({"error": "Nu s-au putut procesa meciurile"}), 400
        
        # Preluă și event name-ul
        report_df, event_name = get_event_season_report(event_code, season)
        
        print(f"📥 Program importat: {len(schedule_df)} meciuri din evenimentul real")
        
        return jsonify({
            "success": True,
            "event": event_code,
            "event_name": event_name if report_df is not None else f"Event {event_code}",
            "season": season,
            "matches_count": len(schedule_df),
            "duplicate_alliances": 0,
            "schedule": schedule_df.to_dict(orient='records'),
            "is_real": True
        }), 200
    
    except Exception as e:
        print(f"Eroare import: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict-schedule/<event_code>', methods=['POST'])
def predict_schedule(event_code):
    """Generează predicții pentru meciurile unui program"""
    try:
        season = request.args.get('season', 2025, type=int)
        schedule_data = request.json.get('schedule', [])
        
        if not schedule_data:
            return jsonify({"error": "Schedule data required"}), 400
        
        # Preluă datele evenimentului
        report_df, event_name = get_event_season_report(event_code, season)
        
        if report_df is None:
            return jsonify({"error": "Event not found"}), 404
        
        # Convertim schedule de la dict la DataFrame
        schedule_df = pd.DataFrame(schedule_data)
        
        # Generează predicții
        predictions = run_full_schedule_prediction_v5(schedule_df, report_df)
        
        if not predictions:
            return jsonify({"error": "Nu s-au putut genera predicții"}), 400
        
        print(f"🔮 Predicții generate pentru {len(predictions)} meciuri")
        
        return jsonify({
            "success": True,
            "event": event_code,
            "event_name": event_name,
            "season": season,
            "predictions_count": len(predictions),
            "predictions": predictions
        }), 200
    
    except Exception as e:
        print(f"Eroare predicție: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ranking/<event_code>', methods=['POST'])
def calculate_ranking(event_code):
    """Calculează clasamentul pe baza programului generat"""
    try:
        season = request.args.get('season', 2025, type=int)
        schedule_data = request.json.get('schedule', [])
        
        if not schedule_data:
            return jsonify({"error": "Schedule data required"}), 400
        
        # Preluă datele evenimentului
        report_df, event_name = get_event_season_report(event_code, season)
        
        if report_df is None:
            return jsonify({"error": "Event not found"}), 404
        
        # Convertim schedule de la dict la DataFrame
        schedule_df = pd.DataFrame(schedule_data)
        
        # Calculează clasamentul
        ranking_df = calculate_predicted_rankings_stochastic(schedule_df, report_df)
        
        if ranking_df.empty:
            return jsonify({"error": "Nu s-a putut calcula clasamentul"}), 400
        
        print(f"🏆 Clasament calculat pentru {len(ranking_df)} echipe")
        
        return jsonify({
            "success": True,
            "event": event_code,
            "event_name": event_name,
            "season": season,
            "teams_count": len(ranking_df),
            "ranking": ranking_df.to_dict(orient='records')
        }), 200
    
    except Exception as e:
        print(f"Eroare clasament: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulate-team/<event_code>', methods=['POST'])
def simulate_team(event_code):
    """Simulează 100 regionale pentru o echipă selectată"""
    try:
        season = request.args.get('season', 2025, type=int)
        team_number = request.json.get('team_number', None)
        
        if not team_number:
            return jsonify({"error": "Team number required"}), 400
        
        # Preluă datele evenimentului
        report_df, event_name = get_event_season_report(event_code, season)
        
        if report_df is None:
            return jsonify({"error": "Event not found"}), 404
        
        # Verifică dacă echipa există în date
        if int(team_number) not in report_df['Team'].values:
            return jsonify({"error": "Team not found in event"}), 404
        
        print(f"🎯 Incepe simulare 100 regionale pentru echipa {team_number}...")
        
        # Rulează simulări
        sim_results = run_100_regional_simulations(report_df, int(team_number), matches_per_team=6)
        
        if not sim_results:
            return jsonify({"error": "Simulation failed"}), 500
        
        # Convertește tipuri numpy/pandas la Python native types
        sim_results = convert_to_serializable(sim_results)
        
        return jsonify({
            "success": True,
            "event": event_code,
            "event_name": event_name,
            "season": season,
            "simulation_type": "single_team",
            "results": sim_results
        }), 200
    
    except Exception as e:
        print(f"Eroare simulare: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/compare-teams/<event_code>', methods=['POST'])
def compare_teams(event_code):
    """Compară două echipe în 100 simulări de regionale"""
    try:
        season = request.args.get('season', 2025, type=int)
        team1 = request.json.get('team1', None)
        team2 = request.json.get('team2', None)
        
        if not team1 or not team2:
            return jsonify({"error": "Both team numbers required"}), 400
        
        if team1 == team2:
            return jsonify({"error": "Teams must be different"}), 400
        
        # Preluă datele evenimentului
        report_df, event_name = get_event_season_report(event_code, season)
        
        if report_df is None:
            return jsonify({"error": "Event not found"}), 404
        
        # Verifică dacă ambele echipe există
        if int(team1) not in report_df['Team'].values:
            return jsonify({"error": f"Team {team1} not found in event"}), 404
        if int(team2) not in report_df['Team'].values:
            return jsonify({"error": f"Team {team2} not found in event"}), 404
        
        print(f"⚔️ Incepe comparare 100 regionale: {team1} vs {team2}...")
        
        # Rulează comparație
        comp_results = run_100_team_comparison(report_df, int(team1), int(team2), matches_per_team=6)
        
        if not comp_results:
            return jsonify({"error": "Comparison failed"}), 500
        
        # Convertește tipuri numpy/pandas la Python native types
        comp_results = convert_to_serializable(comp_results)
        
        return jsonify({
            "success": True,
            "event": event_code,
            "event_name": event_name,
            "season": season,
            "simulation_type": "comparison",
            "results": comp_results
        }), 200
    
    except Exception as e:
        print(f"Eroare comparare: {e}")
        return jsonify({"error": str(e)}), 500

# Servește frontend-ul React

@app.route('/')
@app.route('/<path:path>')
def serve_static(path='index.html'):
    """Servește fișierele statice React"""
    if path and os.path.exists(os.path.join(STATIC_DIR, path)):
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)