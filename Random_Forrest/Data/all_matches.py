import os
import time
import random
import datetime
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import unicodedata

# ------------------ PLAYER LIST ------------------
top_atp_players = top_atp_players = [
    "Jannik Sinner",
    "Carlos Alcaraz",
    "Novak Djokovic",
    "Jack Draper",
    "Alexander Zverev",
    "Taylor Fritz",
    "Daniil Medvedev",
    "Alex De Minaur",
    "Lorenzo Musetti",
    "Grigor Dimitrov",
    "Casper Ruud",
    "Tommy Paul",
    "Holger Rune",
    "Stefanos Tsitsipas",
    "Matteo Berrettini",
    "Arthur Fils",
    "Jakub Mensik",
    "Francisco Cerundolo",
    "Tomas Machac",
    "Gael Monfils",
    "Joao Fonseca",
    "Ben Shelton",
    "Hubert Hurkacz",
    "Ugo Humbert",
    "Tallon Griekspoor",
    "Alejandro Davidovich Fokina",
    "Andrey Rublev",
    "Jiri Lehecka",
    "Karen Khachanov",
    "Sebastian Korda",
    "Denis Shapovalov",
    "Thanasi Kokkinakis",
    "Rafael Nadal",
    "Jordan Thompson",
    "Alex Michelsen",
    "Matteo Arnaldi",
    "Frances Tiafoe",
    "Felix Auger Aliassime",
    "Jacob Fearnley",
    "Brandon Nakashima",
    "Marcos Giron",
    "Alexei Popyrin",
    "Nuno Borges",
    "Jenson Brooksby",
    "Colton Smith",
    "Zizou Bergs",
    "Hamad Medjedovic",
    "Flavio Cobolli",
    "Borna Coric",
    "Gabriel Diallo",
    "Yoshihito Nishioka",
    "Miomir Kecmanovic",
    "Fabian Marozsan",
    "Laslo Djere",
    "Roman Safiullin",
    "Reilly Opelka",
    "Ethan Quinn",
    "Marin Cilic",
    "Alexander Bublik",
    "Kamil Majchrzak",
    "David Goffin",
    "Juncheng Shang",
    "Kei Nishikori",
    "Marton Fucsovics",
    "Christopher Oconnell",
    "Cameron Norrie",
    "Roberto Bautista Agut",
    "Giovanni Mpetshi Perricard",
    "Lorenzo Sonego",
    "Alexandre Muller",
    "Sebastian Baez",
    "Pablo Carreno Busta",
    "Quentin Halys",
    "Lucas Pouille",
    "Learner Tien",
    "Jason Kubler",
    "Mariano Navone",
    "Luciano Darderi",
    "Alejandro Tabilo",
    "Tomas Martin Etcheverry",
    "Raphael Collignon",
    "Jan Lennard Struff",
    "Roberto Carballes Baena",
    "Stan Wawrinka",
    "Camilo Ugo Carabelli",
    "Benjamin Bonzi",
    "Borna Gojo",
    "Nicolas Jarry",
    "Jaume Munar",
    "Zhizhen Zhang",
    "Francisco Comesana",
    "Corentin Moutet",
    "Daniel Altmaier",
    "Dominik Koepfer",
    "Botic Van De Zandschulp",
    "Yibing Wu",
    "Nishesh Basavareddy",
    "Bu Yunchaokete",
    "Elmer Moller",
    "Damir Dzumhur",
    "Vit Kopriva",
    "Mackenzie Mcdonald",
    "Max Purcell",
    "Adam Walton",
    "Aleksandar Kovacevic",
    "Cristian Garin",
    "Arthur Cazaux",
    "Yosuke Watanuki",
    "Pedro Martinez",
    "Soon Woo Kwon",
    "Arthur Rinderknech",
    "Marc Andrea Huesler",
    "Dalibor Svrcina",
    "Dusan Lajovic",
    "Valentin Royer",
    "Emil Ruusuvuori",
    "Hugo Gaston",
    "Valentin Vacherot",
    "Sebastian Ofner",
    "Francesco Passaro",
    "Aleksandar Vukic",
    "Andrea Vavassori",
    "Emilio Nava",
    "Diego Schwartzman",
    "Brandon Holt",
    "Jesper De Jong",
    "Aslan Karatsev",
    "Juan Manuel Cerundolo",
    "Alexander Blockx",
    "Tristan Schoolkate",
    "Lloyd Harris",
    "Leandro Riedi",
    "Fabio Fognini",
    "Terence Atmane",
    "Rinky Hijikata",
    "Mattia Bellucci",
    "Pierre Hugues Herbert",
    "Richard Gasquet",
    "Luca Nardi",
    "Kyrian Jacquet",
    "Eliot Spizzirri",
    "Thiago Monteiro",
    "Zsombor Piros",
    "Nicolas Moreno De Alboran",
    "Facundo Bagnis",
    "Harold Mayot",
    "Felipe Meligeni Alves",
    "Hugo Dellien",
    "Facundo Diaz Acosta",
    "Yannick Hanfmann",
    "James Duckworth",
    "Daniel Elahi Galan",
    "Christopher Eubanks",
    "Alex Molcan",
    "Matteo Gigante",
    "Tomas Barrios Vera",
    "Filip Misolic",
    "Michael Mmoh",
    "Pavel Kotov",
    "Jerome Kym",
    "Liam Draxl",
    "Jaime Faria",
    "Alibek Kachmazov",
    "Nikoloz Basilashvili",
    "Tristan Boyer",
    "Federico Coria",
    "Adrian Mannarino",
    "Arthur Bouquier",
    "Daniel Evans",
    "Alexander Shevchenko",
    "Vilius Gaubas",
    "Carlos Taberner",
    "Andrea Pellegrino",
    "Ignacio Buse",
    "Thiago Seyboth Wild",
    "Gregoire Barrere",
    "Lukas Klein",
    "Hady Habib",
    "Thiago Agustin Tirante",
    "Maximilian Marterer",
    "Giulio Zeppieri",
    "J J Wolf",
    "Constant Lestienne",
    "Taro Daniel",
    "Mikhail Kukushkin",
    "Kyle Edmund",
    "Gustavo Heide",
    "Roman Andres Burruchaga",
    "Otto Virtanen",
    "Dino Prizmic",
    "Chun Hsin Tseng",
    "Luca Van Assche",
    "Seong Chan Hong",
    "Albert Ramos",
    "Shintaro Mochizuki",
    "Daniel Rincon",
    "Mark Lajal",
    "Billy Harris",
    "Hugo Grenier",
    "Liam Broady",
]

# ------------------ LOGGING FUNCTION ------------------
def log(message, level="INFO", logfile="scrape_log.txt"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tag = f"[{level}]"
    full = f"{timestamp} {tag} {message}"
    print(full)
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(full + "\n")

# ------------------ NAME CLEANER ------------------
def clean_name(name):
    return unicodedata.normalize("NFKD", name).replace("\xa0", " ").strip()

# ------------------ CORE FUNCTIONS ------------------
def get_soup(url, retries=3):
    for attempt in range(retries):
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            time.sleep(random.uniform(2, 4))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
            return soup
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(2)

def scrape_serve_tab(formatted_name, player_name):
    url = f"https://www.tennisabstract.com/cgi-bin/player-classic.cgi?p={formatted_name}&f=ACareerqq"
    soup = get_soup(url)
    table = soup.find('table', id='matches')
    if not table:
        return None

    headers = []
    for i, th in enumerate(table.find_all('th')):
        text = th.get_text(strip=True)
        headers.append('Opp' if text == '' and i == 6 else text)

    desired = ['Date', 'Surface', 'Rd', 'Opp', 'Score', 'DR', 'A%', 'DF%', '1stIn', '1st%', '2nd%']
    try:
        indices = {col: headers.index(col) for col in desired}
    except ValueError:
        return None

    data = []
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) < max(indices.values()) + 1:
            continue
        entry = {}
        for col, idx in indices.items():
            if col == 'Opp':
                link = cols[idx].find('a')
                opponent = link.get_text(strip=True) if link else cols[idx].get_text(strip=True)
                entry['Opponent'] = clean_name(opponent)
            else:
                entry[col] = cols[idx].get_text(strip=True)
        entry['Player'] = player_name
        data.append(entry)

    return pd.DataFrame(data)

def scrape_return_tab(formatted_name):
    url = f"https://www.tennisabstract.com/cgi-bin/player-classic.cgi?p={formatted_name}&f=ACareerqqr1"
    soup = get_soup(url)
    table = soup.find('table', id='matches')
    if not table:
        return None

    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    desired = ['TPW', 'RPW', 'vA%', 'v1st%', 'v2nd%', 'BPCnv', 'Time']
    try:
        indices = {col: headers.index(col) for col in desired}
    except ValueError:
        return None

    data = []
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) < max(indices.values()) + 1:
            continue
        entry = {f"Ret_{col}": cols[idx].get_text(strip=True) for col, idx in indices.items()}
        data.append(entry)

    return pd.DataFrame(data)

def scrape_full_stats(player_name):
    formatted_name = player_name.strip().replace(" ", "")
    df_serve = scrape_serve_tab(formatted_name, player_name)
    df_return = scrape_return_tab(formatted_name)
    if df_serve is None or df_return is None:
        return None

    min_len = min(len(df_serve), len(df_return))
    df_combined = pd.concat([
        df_serve.iloc[:min_len].reset_index(drop=True),
        df_return.iloc[:min_len].reset_index(drop=True)
    ], axis=1)

    df_combined.replace('', pd.NA, inplace=True)
    df_combined.dropna(inplace=True)
    return df_combined

# ------------------ MAIN SCRAPING LOOP ------------------
checkpoint_dir = "checkpoints"
os.makedirs(checkpoint_dir, exist_ok=True)
failed_log_path = "failed_players.txt"
failed_players = []

for player in tqdm(top_atp_players, desc="Scraping players", unit="player"):
    formatted_name = player.replace(" ", "")
    checkpoint_path = os.path.join(checkpoint_dir, f"{formatted_name}.csv")

    if os.path.exists(checkpoint_path):
        log(f"Already scraped {player}, skipping...", "SUCCESS")
        continue

    try:
        df = scrape_full_stats(player)
        if df is not None:
            df.to_csv(checkpoint_path, index=False, encoding='utf-8')
            log(f"Saved {player}'s stats to {checkpoint_path}", "SUCCESS")
        else:
            log(f"No data for {player}.", "WARNING")
            failed_players.append(player)
    except Exception as e:
        log(f"Error scraping {player}: {e.__class__.__name__} - {e}", "ERROR")
        failed_players.append(player)

# ------------------ LOG FAILED PLAYERS ------------------
if failed_players:
    with open(failed_log_path, 'w', encoding='utf-8') as f:
        for p in failed_players:
            f.write(p + "\n")
    log(f"Logged {len(failed_players)} failed players to {failed_log_path}", "WARNING")
else:
    log("All players scraped successfully.", "SUCCESS")

# ------------------ MERGE CHECKPOINTS ------------------
log("Merging all checkpoint CSVs...", "INFO")

all_dfs = []
for file in os.listdir(checkpoint_dir):
    if file.endswith(".csv"):
        df = pd.read_csv(os.path.join(checkpoint_dir, file))
        all_dfs.append(df)

if all_dfs:
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_csv("top200_combined_stats.csv", index=False, encoding='utf-8')
    log("Final CSV saved as 'top200_combined_stats.csv'", "SUCCESS")
else:
    log("No data found to merge.", "WARNING")
