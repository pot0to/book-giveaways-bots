import json
import time, requests
from datetime import datetime
from playwright.sync_api import sync_playwright
import random
import os
from utils import *

# --- Setup constants ---

def get_goodreads_creds():
    username = os.getenv("GOODREADS_USERNAME")
    password = os.getenv("GOODREADS_PASSWORD")
    if username and password:
        return username, password
    config = load_config()
    creds = config.get("credentials", {}).get("goodreads", {})
    return creds.get("username"), creds.get("password")

def email_sign_in(page):
    username, password = get_goodreads_creds()
    page.goto("https://www.goodreads.com/user/sign_in")
    
    # Playwright auto-waits for these buttons to be ready
    page.click("button.authPortalSignInButton")
    page.fill('input[name="email"]', username)
    page.fill('input[name="password"]', password)
    page.click('input[id="signInSubmit"]')
    page.wait_for_selector("img.circularIcon--border", timeout=15000)
    print("Login confirmed: Profile picture found.")

def enter_giveaway(page, book_article):
    # 1. Click the 'Enter Giveaway' button and wait for the new tab to open
    with page.context.expect_page() as new_page_info:
        book_article.locator(".GiveawayMetadata__enterGiveawayButton >> a").click()
    
    new_tab = new_page_info.value
    new_tab.wait_for_load_state()

    try:
        # 2. Select address and submit
        new_tab.click("a.addressLink")
        new_tab.click(".stacked >> input[type='checkbox']")
        new_tab.click("#giveawaySubmitButton")
        new_tab.wait_for_timeout(2000) # Small safety wait
        print("Entry successful.")
        success = True
    except Exception:
        # Check if already entered
        if "already entered" in new_tab.content().lower():
            success = True
        else:
            success = False
    
    new_tab.close()
    return success

def enter_giveaways_for_category(page, giveaways_url):
    entered = []
    giveawayEntriesCount = 1

    foundGiveaway = True
    while giveawayEntriesCount > 0 and foundGiveaway:
        foundGiveaway = False
        # goto/refresh giveaways page to show new giveaways not yet entered
        page.goto(giveaways_url)
        # Selects the H1 with those exact classes
        page.locator("h1.Text.H1Title").wait_for(state="visible")
        print("Giveaways page (re)loaded.")

        # Find all book articles
        giveawayEntries = page.locator("article").all()
        giveawayEntriesCount = len(giveawayEntries)
        print("Number of giveaway books found: " + str(giveawayEntriesCount))
        for book in giveawayEntries:
            tags = book.locator(".GiveawayGenres >> li").all_text_contents()
            if any("children" in t.lower() for t in tags):
                continue
            enterGiveawaySuccess = enter_giveaway(page, book)
            time.sleep(random.randint(2, 5)) # Breath between entries
            foundGiveaway = True
            if enterGiveawaySuccess:
                title = book.locator(".BookListItem__title").inner_text()
                author = book.locator(".BookListItem__authors").inner_text()
                entered.append(f"{title} by {author}")
                print(f"Successfully entered giveaway for: {title} by {author}.\n")
    
    print("All giveaways entered.")
    return entered

def get_recently_closed_giveaways(page):
    won, lost = [], []
    page_number = 1

    while True:
        # Navigate to the page
        url = f"https://www.goodreads.com/giveaway/history?page={page_number}&ref=giv_hist"
        page.goto(url)
        
        # Wait for the table to actually appear instead of randomWait(15)
        # If the table isn't found (maybe no more pages), we break the loop
        try:
            page.locator("table.tableList tr >> nth=1").wait_for(state="visible")
        except:
            break

        # Get all rows in the table body
        # .all() converts the locator into a list of individual row objects
        rows = page.locator("table tbody tr").all()
        
        # If there are no rows (or just the header), we've reached the end
        if len(rows) <= 1:
            break

        # Process each row (skipping header if necessary, though tbody usually excludes it)
        for row in rows:
            try:
                # 1. Check if the book is on the 'Want to Read' shelf
                # .count() is a great way to check if an element exists without crashing
                is_wtr = row.locator("div.wtrStatusToRead").count() > 0
                
                # 2. Get the giveaway status (usually the 3rd column)
                # Playwright uses 1-based indexing for nth-column
                status_cell = row.locator("td:nth-child(3)")
                status_text = status_cell.inner_text().lower()
                is_won = row.locator("td:nth-child(4)").inner_text().lower() == "yes"

                # 3. If closed and I want to read it, grab the title
                if "open" not in status_text and is_wtr:
                    book_title = row.locator("a.bookTitle").inner_text().strip()
                    if is_won:
                        won.append(book_title)
                    else:
                        lost.append(book_title)
                    
            except Exception as e:
                # Log the error but keep processing the rest of the list
                print(f"Error processing row on page {page_number}: {e}")

        page_number += 1
        # Added a small safety break to prevent infinite loops during testing
        if page_number > 20: 
            break
    
    print(f"Won {len(won)} books, lost {len(lost)} books")
    return won, lost

def remove_from_my_books(page, recently_closed_giveaways):
    # Navigate to your 'My Books' page
    page.goto("https://www.goodreads.com/review/list/14039716?ref=nav_mybooks")
    # Wait for the first row
    page.locator("table#books tr >> nth=1").wait_for(state="visible")
    
    # 1. Handle the "Are you sure?" popup automatically
    # This 'listener' stays active and clicks 'OK' every time a delete confirmation appears
    page.on("dialog", lambda dialog: dialog.accept())

    with open("removed.txt", "w+", encoding="utf-8") as f:
        for book_title in recently_closed_giveaways:
            try:
                # 2. Search for the specific book title
                # We use .fill() instead of .send_keys() for cleaner input
                page.fill("input#sitesearch_field", book_title)
                page.click("a.myBooksSearchButton")

                # 3. Wait for the results to load
                # We wait for the delete link to appear (proves the search finished)
                delete_button = page.locator("a.deleteLink").first
                
                # Check if the book was actually found
                if delete_button.is_visible(timeout=5000):
                    delete_button.click()
                    
                    # No need for driver.switch_to.alert.accept()! 
                    # The listener we set up above handles it instantly.

                    print(f"Deleted {book_title} from want to reads list.")
                    f.write(book_title + "\n")
                    
                    # Optional: Small wait to let the UI refresh
                    page.wait_for_timeout(2000)
                else:
                    print(f"Could not find {book_title} on shelf.")

            except Exception as e:
                print(f"Failed to remove {book_title}: {e}")
                continue
    
    print("Finished removing closed giveaways from \"Want to Read\" list.")

def run_goodreads():
    with sync_playwright() as p:
        # Launch browser (Set headless=True for Docker)
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        # Create a context that looks like a real Windows Chrome browser
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        entered, won, lost = [], [], []

        try:
            email_sign_in(page)
            entered += enter_giveaways_for_category(page, r"https://www.goodreads.com/giveaway/genre/Science%20fiction?sort=featured&format=print")
            entered += enter_giveaways_for_category(page, r"https://www.goodreads.com/giveaway/genre/Fantasy?sort=featured&format=print")

            won, lost = get_recently_closed_giveaways(page)

            print("Logging results to JSON and sending Discord report...")

            log_results_to_json("GoodReads", entered, won, lost)

            print("Logged to json")
            remove_from_my_books(page, won + lost)
            return entered, won, lost
        finally:
            browser.close()
            print(f"Finished entering GoodReads giveaways for {datetime.today().strftime('%Y-%m-%d')}")

def send_discord_report(entered, won, lost):
    # --- Configuration ---
    has_won = len(won) > 0
    report_color = 15844367 if has_won else 5814783 # 5814783 is Blue, 15844367 is Gold/Yellow
    report_title = "🏆 GOODREADS WINNER REPORT 🏆" if has_won else "📚 GoodReads Daily Giveaway Report"
    
    # --- Build the Fields dynamically ---
    fields = []
    
    # Only show 'Won' section if you actually won
    if has_won:
        won_list = "\n".join([f"✨ **{title}**" for title in won])
        fields.append({
            "name": "🎊 CONGRATULATIONS! YOU WON: 🎊",
            "value": won_list,
            "inline": False
        })

    # Always show Entered and Lost
    if entered:
        fields.append({
            "name": "✅ Entered Today",
            "value": "\n".join(entered),
            "inline": False
        })
        
    if lost:
        fields.append({
            "name": "❌ Closed (Not Won)",
            "value": "\n".join(lost),
            "inline": False
        })

    # --- Construct and Send ---
    embed = {
        "title": f"{report_title} - {datetime.now().strftime('%Y-%m-%d')}",
        "color": report_color,
        "fields": fields,
        "footer": {"text": "Goodreads Bot Automation"}
    }
    
    data = {"embeds": [embed], "username": "Goodreads Bot"}
    
    requests.post(get_discord_webhook(), json=data)
    print("Discord report sent")

def job():
    print(f"Starting daily GoodReads giveaway check at {time.ctime()}")
    try:
        entered, won, lost = run_goodreads()
        send_discord_report(entered, won, lost)
        return {
            "platform": "goodreads",
            "success": True,
            "entered_count": len(entered),
            "won_count": len(won),
            "lost_count": len(lost),
            "error": None
        }
    except Exception as e:
        print(f"Job failed: {e}")
        return {
            "platform": "goodreads",
            "success": False,
            "entered_count": 0,
            "won_count": 0,
            "lost_count": 0,
            "error": str(e)
        }