import re
import time
import random
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

successfullyRemovedGiveawaysLog = "removed.txt"
failedToRemoveGiveawaysLog = "failed.txt"

driver = webdriver.Chrome(ChromeDriverManager().install())
pastEnteredBooks = []
wantToReadTitles = []

def randomWait(seconds):
    driver.implicitly_wait(seconds)
    time.sleep(random.randint(1,10))

def readLoginInfo():
    with open("login.txt") as f:
        lines = f.readlines()
        username = lines[0][lines[0].index('=')+1:].strip()
        password = lines[1][lines[1].index('=')+1:].strip()
    return username, password

def facebookSignIn():
    username, password = readLoginInfo()

    driver.get("https://www.goodreads.com/user/sign_in")
    randomWait(5)
    facebookLogin = driver.find_element(By.XPATH, "//button[contains(@class, 'fbSignInButton')]")
    facebookLogin.click()
    randomWait(5)
    emailInputBox = driver.find_element(By.XPATH, "//input[@id='email']")
    emailInputBox.send_keys(username)
    passwordInputBox = driver.find_element(By.XPATH, "//input[@id='pass']")
    passwordInputBox.send_keys(password)
    loginButton = driver.find_element(By.XPATH, "//button[@id='loginbutton']")
    loginButton.click()
    randomWait(25)


def cleanWantToReadShelf():
    # check each title and remove from my "Want To Read Shelf" if it wasn't originally there
    with open(successfullyRemovedGiveawaysLog, "w+") as f_successful:
        with open(failedToRemoveGiveawaysLog, "w+") as f_failed:
            numBooksOnPreviousPages = 1
            pageNumber = 1
            nextPage = True
            while numBooksOnPreviousPages > 0:
                driver.get(f"https://www.goodreads.com/review/list/14039716-emma?page={pageNumber}&per_page=50&ref=nav_mybooks&shelf=to-read&utf8=%E2%9C%93&view=table")
                randomWait(5)
                numBooksOnPreviousPages = len(driver.find_elements_by_xpath("//tbody[@id='booksBody']/tr/td[@class='field title']/div/a"))
                bookElements = driver.find_elements_by_xpath("//tbody[@id='booksBody']/tr[@class='bookalike review']")

                i = 0
                while i < len(bookElements):
                    bookElement = bookElements[i]
                    bookTitle = bookElement.find_element_by_xpath(".//td[@class='field title']/div[@class='value']/a").get_attribute("title")
                    dateAdded = datetime.datetime.strptime(
                        bookElement.find_element_by_xpath(".//td[@class='field date_added']/div[@class='value']/span").text,
                        "%b %d, %Y").date()
                    if dateAdded == datetime.date(2023, 7, 30) or dateAdded == datetime.date(2023, 3, 11) or dateAdded == datetime.date(2023, 3, 12):
                        try:
                            deleteButton = bookElement.find_element_by_xpath(".//a[@class='actionLinkLite smallText deleteLink']")
                            deleteButton.click()
                            randomWait(5)

                            # hit enter on the popup
                            # actions = ActionChains(driver)
                            # actions.send_keys(Keys.ENTER)
                            # actions.perform()
                            WebDriverWait(driver, 10).until(EC.alert_is_present())
                            driver.switch_to.alert.accept()

                            print(f"{bookTitle} removed from 'Want to Read list'")
                            f_successful.write(bookTitle + "\n")
                            nextPage = False # stay on this page until you've gone through the list once and not found any books

                            randomWait(5)

                            bookElements = driver.find_elements_by_xpath("//tbody[@id='booksBody']/tr[@class='bookalike review']")
                        except:
                            f_failed.write(bookTitle + "\n")
                    else:
                        i += 1
                            
                if nextPage:
                    pageNumber += 1

def main():
    try:
        facebookSignIn()
        cleanWantToReadShelf()
    except Exception as e:
        print(e)
    finally:
        # close the drivers
        driver.quit()

if __name__=="__main__":
    main()