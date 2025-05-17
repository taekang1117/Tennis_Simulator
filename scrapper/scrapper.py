from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_recent_stats_selenium(player_name):
    # Format the player's name correctly
    formatted_name = ''.join(part.capitalize() for part in player_name.split())
    url = f"https://www.tennisabstract.com/cgi-bin/player.cgi?p={formatted_name}"

    # Headless Chrome setup
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    print(f" Loading: {url}")
    driver.get(url)
    time.sleep(3)  # Let JavaScript finish loading

    # Use BeautifulSoup on the rendered HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Find the 'recent-results' table directly
    table = soup.find('table', id='recent-results')
    if not table:
        print(" Could not find the recent results table.")
        return

    # Extract all headers
    all_headers = [th.get_text(strip=True) for th in table.find_all('th')]
    desired_cols = ['DR', 'A%', 'DF%', '1stIn', '1st%', '2nd%']
    indices = [all_headers.index(col) for col in desired_cols]

    # Extract rows
    data_rows = []
    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        if len(tds) > max(indices):
            row = [tds[i].get_text(strip=True) for i in indices]
            data_rows.append(row)

    # Save to CSV
    df = pd.DataFrame(data_rows, columns=desired_cols)
    file_name = f"{formatted_name}_recent_stats.csv"
    df.to_csv(file_name, index=False)
    print(f" Stats saved to: {file_name}")
    return df

# Example usage
if __name__ == "__main__":
    player = input("Enter player name (e.g., Francisco Cerundolo): ")
    scrape_recent_stats_selenium(player)
