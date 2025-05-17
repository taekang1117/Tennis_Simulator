from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

def get_soup(url):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(random.uniform(2, 4))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    return soup

def scrape_main_stats(formatted_name):
    url = f"https://www.tennisabstract.com/cgi-bin/player-classic.cgi?p={formatted_name}"
    soup = get_soup(url)

    table = soup.find('table', id='matches')
    if not table:
        print("Could not find the recent results table.")
        return None

    all_headers = [th.get_text(strip=True) for th in table.find_all('th')]
    desired_cols = ['DR', 'A%', 'DF%', '1stIn', '1st%', '2nd%']
    try:
        indices = [all_headers.index(col) for col in desired_cols]
    except ValueError as e:
        print(f"Column not found: {e}")
        return None

    data_rows = []
    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        if len(tds) >= max(indices) + 1:
            row = [tds[i].get_text(strip=True) for i in indices]
            data_rows.append(row)

    df = pd.DataFrame(data_rows, columns=desired_cols)
    df.replace('', pd.NA, inplace=True)
    df.dropna(inplace=True)

    return df

def scrape_tpw(formatted_name):
    url = f"https://www.tennisabstract.com/cgi-bin/player-classic.cgi?p={formatted_name}&f=r1"
    soup = get_soup(url)

    table = soup.find('table', id='matches')
    if not table:
        print("Could not find return stats table.")
        return []

    all_headers = [th.get_text(strip=True) for th in table.find_all('th')]
    try:
        tpw_index = all_headers.index('TPW')
    except ValueError:
        print("TPW column not found.")
        return []

    tpw_values = []
    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        if len(tds) >= tpw_index + 1:
            value = tds[tpw_index].get_text(strip=True)
            if value != '':
                tpw_values.append(value)

    return tpw_values

def scrape_player_stats(player_name):
    formatted_name = player_name.strip().replace(" ", "")
    print(f"Scraping stats for: {formatted_name}")

    df_main = scrape_main_stats(formatted_name)
    if df_main is None or df_main.empty:
        print("No valid main stats to process.")
        return

    tpw_list = scrape_tpw(formatted_name)

    # Match lengths to avoid mismatch
    min_len = min(len(df_main), len(tpw_list))
    df_main = df_main.iloc[:min_len].copy()
    df_main['TPW'] = tpw_list[:min_len]

    # Remove rows with any blank values
    df_main.replace('', pd.NA, inplace=True)
    df_main.dropna(inplace=True)

    file_name = f"{formatted_name}_tpw.csv"
    df_main.to_csv(file_name, index=False)
    print(f"Cleaned stats saved to: {file_name}")
    return df_main

# Run interactively
if __name__ == "__main__":
    player = input("Enter the full name of the tennis player (e.g., Alexander Zverev): ")
    scrape_player_stats(player)
