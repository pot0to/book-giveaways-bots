import json
from selenium.webdriver.common.by import By

from utils import *

def readLoginInfo():
    try:
        with open(credentials_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        creds = data.get("storygraph", {})
        username = creds.get("username")
        password = creds.get("password")
        return username, password
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON: {e}")
        return None, None

def EmailSignIn():
    username, password = readLoginInfo()

    driver.get("https://app.thestorygraph.com/users/sign_in")
    randomWait(5)
    emailInputBox = driver.find_element(By.XPATH, "//input[@name='user[email]']")
    emailInputBox.send_keys(username)
    passwordInputBox = driver.find_element(By.XPATH, "//input[@name='user[password]']")
    passwordInputBox.send_keys(password)
    loginButton = driver.find_element(By.XPATH, "//button[@id='sign-in-btn']")
    loginButton.click()
    randomWait(25)

def EnterGiveaways():
    driver.get("https://app.thestorygraph.com/giveaways")
    randomWait(5)
    filter_visible = False
    while not filter_visible:
        expand_filter = driver.find_element(By.XPATH, "//form/div/div[@class='toggle-filter-menu cursor-pointer hidden dark:inline']")
        expand_filter.click()
        randomWait(5)
        try:
            want_to_win = driver.find_element(By.XPATH, "//p[text()=\"I want to win a book that's...\"]")
            if want_to_win.is_displayed():
                filter_visible = True
        except:
            pass

    fiction = driver.find_element(By.XPATH, "//input[@name='type_fiction']")
    scrollIntoView(fiction)
    fiction.click()
    randomWait(5)

    # include_genres = driver.find_element(By.XPATH, "//select")
    fantasy = driver.find_element(By.XPATH, "//select[@name='genres_include[]']/option[text()='Fantasy']")
    fantasy.click()
    scifi = driver.find_element(By.XPATH, "//select[@name='genres_include[]']/option[text()='Science Fiction']")
    scifi.click()

    # exclude_genres
    childrens = driver.find_element(By.XPATH, "//select[@name='genres_exclude[]']/option[text()='Childrens']")
    childrens.click()
    ya = driver.find_element(By.XPATH, "//select[@name='genres_exclude[]']/option[text()='Young Adult']")
    ya.click()
    middlegrade = driver.find_element(By.XPATH, "//select[@name='genres_exclude[]']/option[text()='Middle Grade']")
    middlegrade.click()

    print = driver.find_element(By.XPATH, "//input[@id='format_print']")
    scrollIntoView(print)
    print.click()
    randomWait(5)

    submit_filter = driver.find_element(By.XPATH, "//input[@value='Filter']")
    submit_filter.click()

    see_all_giveaways = driver.find_element(By.XPATH, "//input[@value='See all matching giveaways']")
    scrollIntoView(see_all_giveaways)
    see_all_giveaways.click()

    randomWait(5)

    driver.refresh()
    giveawayEntries = driver.find_elements(By.XPATH, "//div[contains(@class, 'giveaway-pane')]")
    for book in giveawayEntries:
        bookNameString = book.find_element(By.XPATH, ".//p[contains(@class, 'text-base')]").text
        enterGiveawaySuccess = enterGiveaway(book)
        foundGiveaway = True
        # if enterGiveawaySuccess:
        #     print(f"Successfully entered giveaway for: {bookNameString}.\n")

def enterGiveaway(book):
    # find the giveaway button, scroll it into view of the page, and click it
    try:
        viewGiveawayButton = book.find_element(By.XPATH, ".//a[text()='View giveaway']")
        scrollIntoView(book)

        # Get the href attribute
        url = viewGiveawayButton.get_attribute("href")

        # Open new tab via JavaScript
        driver.execute_script(f"window.open('{url}', '_blank');")

        # Switch to the new tab
        driver.switch_to.window(driver.window_handles[-1])

        entrySuccess = False

        try:
            randomWait(10)

            try:
                already_entered = driver.find_element(By.XPATH, "//p[@title='You have entered this giveaway']")
            except:
                try:
                    popup = driver.find_element(By.XPATH, "//*[@id='close-cookies-popup']")
                    popup.click()
                except Exception as e:
                    print(e)
                    pass

                enterGiveawayButton = driver.find_element(By.XPATH, "//a[text()='Enter giveaway']")
                scrollIntoView(enterGiveawayButton)
                enterGiveawayButton.click()

                randomWait(5)

                confirm_and_enter = driver.find_element(By.XPATH, "//button[span[text()='Confirm and enter']]")
                scrollIntoView(confirm_and_enter)
                confirm_and_enter.click()

                entrySuccess = True
                # close new tab and switch back to the original
        except Exception as e:
            print(e)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except Exception as e:
        print(e)
        entrySuccess = False
    
    
    return entrySuccess

def storygraph():
    EmailSignIn()
    EnterGiveaways()