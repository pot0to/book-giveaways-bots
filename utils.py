from datetime import datetime
import json
import os

CONFIG_PATH = "config.json"
LOCAL_SECRETS_PATH = "secrets.local.json"

def load_json_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def merge_dicts(base, override):
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged

def load_config():
    config_data = load_json_file(CONFIG_PATH)
    local_secrets = load_json_file(LOCAL_SECRETS_PATH)
    return merge_dicts(config_data, local_secrets)

def get_discord_webhook():
    return os.getenv("DISCORD_WEBHOOK_URL") or load_config().get("discord_webhook")

def log_results_to_json(platform, entered, won, lost):
    log_file = "logs/giveaway_history.json"
    os.makedirs("logs", exist_ok=True)
    
    # Create the entry
    new_entry = {
        "platform": platform,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats": {
            "total_entered": len(entered),
            "total_won": len(won),
            "total_lost": len(lost)
        },
        "details": {
            "entered_books": entered,
            "won_books": won,
            "lost_books": lost
        }
    }

    try:
        # 1. Load existing data
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        # 2. Append new entry
        data.append(new_entry)

        # 3. Save back to file
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        print(f"📊 Results logged to {log_file}")
    except Exception as e:
        print(f"⚠️ Failed to write to JSON log: {e}")