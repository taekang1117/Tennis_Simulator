from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_top_atp_players(limit=200, output_file="top_atp_players.txt"):
    # Setup Selenium with headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    url = "https://www.tennisabstract.com/reports/atp_elo_ratings.html"
    driver.get(url)
    time.sleep(3)  # Allow JavaScript to load

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Locate the target table
    table = soup.find('table', id='reportable')
    if not table:
        print("Table with id='reportable' not found.")
        return

    player_names = []
    rows = table.find_all('tr')[1:]  # Skip header row
    for row in rows:
        link_cell = row.find_all('td')[1]  # Player name is in the 2nd column
        name_tag = link_cell.find('a')
        if name_tag:
            name = name_tag.get_text(strip=True).replace('\xa0', ' ')
            player_names.append(name)
            if len(player_names) >= limit:
                break

    # Save to pandas DataFrame and export
    df = pd.DataFrame(player_names, columns=["Player"])
    df.to_csv("top_atp_players.csv", index=False)

    # Also save as Python list format in text file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("top_atp_players = [\n")
        for name in player_names:
            f.write(f'    "{name}",\n')
        f.write("]")

    print(f"✅ Scraped and saved top {len(player_names)} ATP players to '{output_file}' and 'top_atp_players.csv'.")
scrape_top_atp_players()
