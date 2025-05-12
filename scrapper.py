from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def scrape_flashscore_match(match_id):
    url = f"https://www.flashscoreusa.com/game/tennis/{match_id}/#/game-summary/point-by-point"

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path="./chromedriver.exe", options=options)

    driver.get(url)

    try:
        # Wait up to 15 seconds for the point container to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "point__score"))
        )
    except:
        print("⚠️ Timeout: Point data did not load.")
        driver.quit()
        return {"error": "Point data not loaded"}

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    rows = soup.select('.point__score')

    player1_points = 0
    player2_points = 0
    total_points = 0

    for point in rows:
        parent_classes = point.parent.get('class', [])
        if 'point--home' in parent_classes:
            player1_points += 1
        elif 'point--away' in parent_classes:
            player2_points += 1
        total_points += 1

    return {
        "Match ID": match_id,
        "Player 1 Points Won": player1_points,
        "Player 2 Points Won": player2_points,
        "Total Points Played": total_points
    }

# Input match ID dynamically
if __name__ == "__main__":
    match_id = input("Enter the Flashscore match ID (e.g., fZmYVPon): ").strip()
    stats = scrape_flashscore_match(match_id)
    print("\nMatch Stats:")
    for key, value in stats.items():
        print(f"{key}: {value}")