import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time

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
            print(f"Could not find table with ID: {table_id}")
            continue

        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if not set(desired_cols).issubset(headers):
            print(f"Skipping {table_id}: Missing desired columns")
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
            print(f"Saved: {csv_path}")
            all_dataframes[table_id] = df
        else:
            print(f"No complete rows found in {table_id}.")

    return all_dataframes

# Example usage
if __name__ == "__main__":
    player = input("Enter player name (e.g., Francisco Cerundolo): ")
    scrape_recent_tables(player)
