import json
from selenium.webdriver.common.by import By

from utils import *

openGiveawaysLog = "open_giveaways.txt"
successfullyRemovedGiveawaysLog = "removed_giveaways.txt"
failedToRemoveGiveawaysLog = "failed_giveaways.txt"

pastEnteredBooks = []
wantToReadTitles = []

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

def readLoginInfo():
    # with open("login.txt") as f:
    #     lines = f.readlines()
    #     username = lines[0][lines[0].index('=')+1:].strip()
    #     password = lines[1][lines[1].index('=')+1:].strip()
    # return username, password

    try:
        with open(credentials_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        creds = data.get("goodreads", {})
        username = creds.get("username")
        password = creds.get("password")
        return username, password
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON: {e}")
        return None, None

def EmailSignIn():
    username, password = readLoginInfo()

    driver.get("https://www.goodreads.com/user/sign_in")
    randomWait(5)
    emailLogin = driver.find_element(By.XPATH, "//button[contains(@class, 'authPortalSignInButton')]")
    emailLogin.click()
    emailInputBox = driver.find_element(By.XPATH, "//input[@name='email']")
    emailInputBox.send_keys(username)
    passwordInputBox = driver.find_element(By.XPATH, "//input[@name='password']")
    passwordInputBox.send_keys(password)
    loginButton = driver.find_element(By.XPATH, "//input[@id='signInSubmit']")
    loginButton.click()
    randomWait(25)

def readWantToReadShelf():
    booksOnPage = 1
    pageNumber = 1
    while booksOnPage > 0:
        driver.get(f"https://www.goodreads.com/review/list/14039716-emma?page={pageNumber}&per_page=50&ref=nav_mybooks&shelf=to-read&utf8=%E2%9C%93&view=table")
        randomWait(5)
        bookTitleElements = driver.find_elements(By.XPATH, "//tbody[@id='booksBody']/tr/td[@class='field title']/div/a")
        for bookTitleElement in bookTitleElements:
            wantToReadTitles.append(bookTitleElement.text)
        booksOnPage = len(bookTitleElements)
        pageNumber += 1

def getImmediateText(element):
    OWN_TEXT_SCRIPT = "if(arguments[0].hasChildNodes()){var r='';var C=arguments[0].childNodes;for(var n=0;n<C.length;n++){if(C[n].nodeType==Node.TEXT_NODE){r+=' '+C[n].nodeValue}}return r.trim()}else{return arguments[0].innerText}"
    parent_text = driver.execute_script(OWN_TEXT_SCRIPT, element)
    return parent_text

def getDate(book):
    dates = book.find_element(By.XPATH, ".//span[@class='GiveawayMetadata__timeLeft']")
    datesText = getImmediateText(dates)
    datesText = ' '.join(datesText.split())
    return datesText

def enterGiveaway(book):
    # find the giveaway button, scroll it into view of the page, and click it
    enterGiveawayButton = book.find_element(By.XPATH, ".//div[@class='GiveawayMetadata__enterGiveawayButton']/a")
    scrollIntoView(enterGiveawayButton)
    enterGiveawayButton.click()
    randomWait(10)
    
    # switch to newly opened tab
    driver.switch_to.window(driver.window_handles[1])

    try:
        address = driver.find_element(By.XPATH, "//div[@class='addressOptions']/a[@class='addressLink']")
        address.click()
        randomWait(5)
        tosCheckbox = driver.find_element(By.XPATH, "//div[@class='stacked']/input")
        tosCheckbox.click()
        submitButton = driver.find_element(By.XPATH, "//input[@id='giveawaySubmitButton']")
        submitButton.click()
        randomWait(10)

        entrySuccess = True
    except:
        try:
            errorBox = driver.find_element(By.XPATH, "//div[@class='box noticeBox errorBox']")
            return "You have already entered this giveaway!" in errorBox.text
        except:
            entrySuccess = False
    
    # close new tab and switch back to the original
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return entrySuccess

def EnterAllGiveawaysForCategory(giveaways_url):
    giveawayEntriesCount = 1

    foundGiveaway = True
    while giveawayEntriesCount > 0 and foundGiveaway:
        foundGiveaway = False
        # navigate to giveaways page
        driver.get(giveaways_url)
        randomWait(15)

        # read all the giveawayEntries
        giveawayEntries = driver.find_elements(By.XPATH, "//div[@class='BookList']/article")
        giveawayEntriesCount = len(giveawayEntries)
        print("Number of giveaway books found: " + str(giveawayEntriesCount))
        for book in giveawayEntries:
            tags = book.find_elements(By.XPATH, ".//div[@class='GiveawayGenres']/ul/li")
            isChildrens = False
            for tag in tags:
                if "children" in tag.text.lower():
                    isChildrens = True
                    break
            if not isChildrens:
                enterGiveawaySuccess = enterGiveaway(book)
                foundGiveaway = True
                if enterGiveawaySuccess:
                    print(f"Successfully entered giveaway for: {book}.\n")

def GetRecentlyClosedGiveaways():
    recentlyClosedGiveaways = []

    pageNumber = 1
    giveawayEntries = ["dummy"]
    while len(giveawayEntries) > 0:
        # navigate to recently entered giveaways page
        driver.get(f"https://www.goodreads.com/giveaway/history?page={pageNumber}&ref=giv_hist")
        randomWait(15)
        giveawayEntries = driver.find_elements(By.XPATH, "//table/tbody/tr")
        randomWait(5)
        giveawayEntries = giveawayEntries[1:]
        for entry in giveawayEntries:
            try:
                wantToReadStatus = entry.find_element(By.XPATH, ".//div[contains(@class, 'wtrStatusToRead')]").text
                giveawayStatus = entry.find_element(By.XPATH, ".//td[3]").text
                if giveawayStatus != "open" and wantToReadStatus != None:
                    bookName = entry.find_element(By.XPATH, ".//a[@class='bookTitle']").text
                    recentlyClosedGiveaways.append(bookName)
            except Exception as e:
                print(entry.text)
                print(e)
        pageNumber += 1
    
    return recentlyClosedGiveaways

def RemoveFromMyBooks(recentlyClosedGiveaways):
    driver.get("https://www.goodreads.com/review/list/14039716?ref=nav_mybooks")
    randomWait(15)
    with open("removed.txt", "w+") as f:
        try:
            for bookTitle in recentlyClosedGiveaways:
                searchBox = driver.find_element(By.XPATH, "//input[@id='sitesearch_field']")
                searchButton = driver.find_element(By.XPATH, "//a[@class='myBooksSearchButton']")
                searchBox.send_keys(bookTitle)
                searchButton.click()
                deleteButton = driver.find_element(By.XPATH, "//a[contains(@class, 'deleteLink')]")
                deleteButton.click()
                driver.switch_to.alert.accept()
                randomWait(5)
                print(f"Deleted {bookTitle} from want to reads list.\n")
                f.write(bookTitle + "\n")
        except:
            pass

def goodreads():
    try:
        EmailSignIn()
        EnterAllGiveawaysForCategory(r"https://www.goodreads.com/giveaway/genre/Science%20fiction?sort=featured&format=print")
        EnterAllGiveawaysForCategory(r"https://www.goodreads.com/giveaway/genre/Fantasy?sort=featured&format=print")
        recentlyClosedGiveaways = GetRecentlyClosedGiveaways()
        RemoveFromMyBooks(recentlyClosedGiveaways)
    except Exception as e:
        print(e)
    finally:
        # close the drivers
        driver.quit()