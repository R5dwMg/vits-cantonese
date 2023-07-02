"""
Get list of character from CUHK
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

# Set up Selenium options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode, no browser window

# Set up the Selenium driver
webdriver_service = Service('/path/to/chromedriver')  # Replace with the path to your chromedriver executable
driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

# Load the webpage
url = "https://humanum.arts.cuhk.edu.hk/Lexis/lexi-can/faq.php?s={0}"
url_seg = [
    1, 501, 1001, 1501, 2001, 2501, 3001, 3501,
    4001, 4501, 5001, 5501, 6001, 6501,
    7001
]
url_list = []
# Create empty lists to store the data
rank_list = []
text_list = []

for i in url_seg:
    u = url.replace("{0}", str(i))
    print("start on", u)
    driver.get(u)

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find the table containing the desired data
    table = soup.find('table')

    # Extract the frequency and text values from each table row
    data = []
    for row in table.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) >= 3:
            rank = cols[0].text.strip()
            text = cols[2].text.strip()
            rank_list.append(rank)
            text_list.append(text)

            rank = cols[3].text.strip()
            text = cols[5].text.strip()
            rank_list.append(rank)
            text_list.append(text)

data = {
    'rank': rank_list,
    'char': text_list
}

# Create a pandas DataFrame from the collected data
df = pd.DataFrame(data)

df.to_csv("cuhk_char_rank.csv")

# Quit the Selenium driver
driver.quit()
