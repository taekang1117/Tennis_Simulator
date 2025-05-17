import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd

def scrape_recent_tables(player_name):
    formatted_name = ''.join(part.capitalize() for part in player_name.split())
    url = f"https://www.tennisabstract.com/cgi-bin/player.cgi?p={formatted_name}"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    print(f"Loading: {url}")
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    table_folders = {
        'recent-events': 'folder_events',
        'recent-results': 'folder_results'
    }

    desired_cols = ['DR', 'A%', 'DF%', '1stIn', '1st%', '2nd%']
    all_dataframes = {}

    for table_id, folder in table_folders.items():
        table = soup.find('table', id=table_id)
        if not table:
            print(f"  [!] Table not found: {table_id}")
            continue

        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if not set(desired_cols).issubset(headers):
            print(f"  [!] Skipping {table_id}: Missing desired columns")
            continue

        indices = [headers.index(col) for col in desired_cols]
        rows = []

        for tr in table.find_all('tr')[1:]:
            tds = tr.find_all('td')
            if len(tds) > max(indices):
                row = [tds[i].get_text(strip=True) for i in indices]
                if any(cell == '' for cell in row):
                    continue
                rows.append(row)

        if rows:
            df = pd.DataFrame(rows, columns=desired_cols)
            os.makedirs(folder, exist_ok=True)
            csv_path = os.path.join(folder, f"{formatted_name}_{table_id}.csv")
            df.to_csv(csv_path, index=False)
            print(f"  [+] Saved: {csv_path}")
            all_dataframes[table_id] = df
        else:
            print(f"  [!] No complete rows found in {table_id}")

    return all_dataframes

# Example: List of Top ATP players (sample for demo)
top_atp_players = [
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

if __name__ == "__main__":
    for name in top_atp_players:
        print(f"\n--- Scraping: {name} ---")
        try:
            scrape_recent_tables(name)
        except Exception as e:
            print(f"  [X] Failed for {name}: {e}")
