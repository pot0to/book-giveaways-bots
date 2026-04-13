import json
import time, requests
from datetime import datetime
from playwright.sync_api import sync_playwright
import random
import os
from utils import *

def get_storygraph_creds():
    username = os.getenv("STORYGRAPH_USERNAME")
    password = os.getenv("STORYGRAPH_PASSWORD")
    if username and password:
        return username, password
    config = load_config()
    creds = config.get("credentials", {}).get("storygraph", {})
    return creds.get("username"), creds.get("password")

def email_sign_in(page):
    username, password = get_storygraph_creds()
    if not username: return

    page.goto("https://app.thestorygraph.com/users/sign_in")
    page.fill("input[name='user[email]']", username)
    page.fill("input[name='user[password]']", password)
    page.click("button#sign-in-btn")
    
    # Wait for the dashboard to load (checking for a common logged-in element)
    page.locator("nav#navbar").wait_for(state="visible")
    print("Logged into StoryGraph successfully.")

def enter_all_giveaways(page):
    page.goto("https://app.thestorygraph.com/giveaways")
    page.locator("nav#navbar").wait_for(state="visible")
    
    # 1. Expand Filters
    # StoryGraph uses specific dark/light mode classes, we use a more robust selector
    page.locator(".toggle-filter-menu:visible").click()
    
    # 2. Set Genres (Fiction, Fantasy, Sci-Fi)
    page.check("input[name='type_fiction']")
    
    # Multi-select genres. Playwright's .select_option() handles multiple values easily
    page.select_option("select[name='genres_include[]']", label=["Fantasy", "Science Fiction"])
    
    # Exclude genres
    page.select_option("select[name='genres_exclude[]']", label=["Childrens", "Young Adult", "Middle Grade"])

    # 3. Format and Submit
    page.check("input#format_print")
    page.click("input[value='Filter']")
    
    # Wait for results and click "See all matching"
    see_all = page.locator("input[value='See all matching giveaways']")
    see_all.wait_for()
    see_all.click()
    page.wait_for_selector(".giveaway-pane")

    # 4. Loop through Giveaway Panes
    giveaway_data = []
    panes = page.locator(".giveaway-pane").all()
    
    giveawaysEntered = 0
    entered_titles = []
    while giveawaysEntered > 0:
        giveawaysEntered = 0
        for pane in panes:
            # Check the entire text of the pane for the 'Entered' status
            # This prevents us from even adding the book to our list
            pane_text = pane.inner_text()
            if "Entered" in pane_text:
                continue # Skip to the next giveaway immediately
            
            # Title is always the first bolded-style text
            title_node = pane.locator("p.text-base").first
            
            # Target the author specifically
            author_node = pane.locator("p.text-sm").first 
            
            link_node = pane.locator("a:has-text('View giveaway')")
            
            if title_node.count() > 0 and link_node.count() > 0:
                title = title_node.inner_text().strip()
                raw_author = author_node.inner_text().strip()
                
                # Cleaner logic to handle 'by' and 'Hosted by'
                author = raw_author.split("Hosted by")[0].replace("by ", "").strip()
                
                rel_url = link_node.get_attribute("href")
                
                giveaway_data.append({
                    "display_name": f"**{title}** by {author}",
                    "url": f"https://app.thestorygraph.com{rel_url}"
                })

        print(f"🎯 Found {len(giveaway_data)} matching giveaways.")
        
        for item in giveaway_data:
            if enter_single_giveaway(page.context, item):
                giveawaysEntered += 1
                entered_titles.append(item['display_name'])
            time.sleep(random.randint(2, 5)) # Breath between entries

    print("All giveaways entered.")
    return entered_titles

def enter_single_giveaway(browser_context, book_item):
    giveaway_page = None
    try:
        # Ensure we don't double up the https:// if your collector already added it
        url = book_item['url']
        full_url = url if url.startswith('http') else f"https://app.thestorygraph.com{url}"

        # 1. Create a new tab directly from the context
        giveaway_page = browser_context.new_page() 
        giveaway_page.goto(full_url, wait_until="domcontentloaded", timeout=30000)

        # 2. Check if already entered (Saves time/resources)
        if "You've entered this giveaway" in giveaway_page.content():
            giveaway_page.close()
            return False

        # 3. Entry Logic
        enter_btn = giveaway_page.get_by_role("link", name="Enter giveaway")
        
        if enter_btn.is_visible(timeout=5000):
            classes = enter_btn.get_attribute("class") or ""
            if "cursor-not-allowed" in classes or "opacity-50" in classes:
                giveaway_page.close()
                return False

            enter_btn.click()
            
            # 4. Confirm Modal
            confirm_btn = giveaway_page.locator("button:has-text('Confirm and enter')")
            confirm_btn.wait_for(state="visible", timeout=5000)
            confirm_btn.click()
            
            # Wait for success state
            giveaway_page.wait_for_timeout(2000)
            
            print(f"Successfully entered: {book_item['display_name']}")
            giveaway_page.close()
            return True

        if giveaway_page:
            giveaway_page.close()
        return False

    except Exception as e:
        print(f"⚠️ Error processing {book_item['display_name']}: {e}")
        if giveaway_page:
            giveaway_page.close()
        return False

def run_storygraph():
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
            entered = enter_all_giveaways(page)
            return entered, won, lost
        finally:
            browser.close()
            print(f"Finished entering StoryGraph giveaways for {datetime.today().strftime('%Y-%m-%d')}")

def send_discord_report(entered, won, lost):
    # --- Configuration ---
    has_won = len(won) > 0
    report_color = 15844367 if has_won else 5814783 # 5814783 is Blue, 15844367 is Gold/Yellow
    report_title = "🏆 STORYGRAPH WINNER REPORT 🏆" if has_won else "📚 StoryGrpah Daily Giveaway Report"
    
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
        "footer": {"text": "StoryGraph Bot Automation"}
    }
    
    data = {"embeds": [embed], "username": "StoryGraph Bot"}
    
    requests.post(get_discord_webhook(), json=data)
    print("Discord report sent")

def job():
    print(f"Starting daily StoryGraph giveaway check at {time.ctime()}")
    try:
        entered, won, lost = run_storygraph()
        send_discord_report(entered, won, lost)
        return {
            "platform": "storygraph",
            "success": True,
            "entered_count": len(entered),
            "won_count": len(won),
            "lost_count": len(lost),
            "error": None
        }
    except Exception as e:
        print(f"Job failed: {e}")
        return {
            "platform": "storygraph",
            "success": False,
            "entered_count": 0,
            "won_count": 0,
            "lost_count": 0,
            "error": str(e)
        }