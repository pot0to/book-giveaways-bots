import os, time, random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

chrome_install = ChromeDriverManager().install()
folder = os.path.dirname(chrome_install)

chrome_options = Options()
chrome_options.add_argument("--headless=new") # Crucial for Docker
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(f"{folder}/chromedriver.exe") 

credentials_path = "login.json"

def randomWait(seconds):
    driver.implicitly_wait(seconds)
    time.sleep(random.randint(1,10))

def scrollIntoView(enterGiveawayButton):
    desired_y = (enterGiveawayButton.size['height'] / 2) + enterGiveawayButton.location['y']
    window_h = driver.execute_script('return window.innerHeight')
    window_y = driver.execute_script('return window.pageYOffset')
    current_y = (window_h / 2) + window_y
    scroll_y_by = desired_y - current_y
    driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
    randomWait(5)