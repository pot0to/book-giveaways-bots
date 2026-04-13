import json
import os
from datetime import datetime
from pathlib import Path

STATUS_FILE = "bot_status.json"

def initialize_status_report():
    """Initialize the status report file if it doesn't exist."""
    default_status = {
        "last_updated": datetime.now().isoformat(),
        "bot_health": "initializing",
        "bots": {
            "goodreads": {
                "status": "pending",
                "last_run": None,
                "last_success": None,
                "error": None,
                "entries_count": 0
            },
            "storygraph": {
                "status": "pending",
                "last_run": None,
                "last_success": None,
                "error": None,
                "entries_count": 0
            }
        },
        "summary": {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "consecutive_failures": 0
        }
    }
    
    if not os.path.exists(STATUS_FILE):
        save_status_report(default_status)
    return load_status_report()

def load_status_report():
    """Load the current status report from file."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return initialize_status_report()

def save_status_report(status):
    """Save the status report to file."""
    status["last_updated"] = datetime.now().isoformat()
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)

def update_bot_status(bot_name, status_state, error=None, entries_count=None):
    """
    Update the status of a single bot.
    
    Args:
        bot_name: 'goodreads' or 'storygraph'
        status_state: 'running', 'success', 'failed', 'pending'
        error: Error message if failed
        entries_count: Number of giveaways entered
    """
    report = load_status_report()
    now = datetime.now().isoformat()
    
    if bot_name not in report["bots"]:
        print(f"Unknown bot: {bot_name}")
        return
    
    bot_info = report["bots"][bot_name]
    bot_info["status"] = status_state
    bot_info["last_run"] = now
    
    if status_state == "success":
        bot_info["last_success"] = now
        bot_info["error"] = None
        if entries_count is not None:
            bot_info["entries_count"] = entries_count
    elif status_state == "failed":
        bot_info["error"] = error
    
    # Update overall health
    all_bots = report["bots"].values()
    all_statuses = [b["status"] for b in all_bots]
    
    if all(s in ["success", "pending"] for s in all_statuses):
        if any(s == "success" for s in all_statuses):
            report["bot_health"] = "healthy"
    elif any(s == "running" for s in all_statuses):
        report["bot_health"] = "running"
    elif any(s == "failed" for s in all_statuses):
        report["bot_health"] = "degraded"
    
    save_status_report(report)

def record_run_result(bots_results):
    """
    Record the result of a complete run.
    
    Args:
        bots_results: Dict with {bot_name: {'success': bool, 'entries': int, 'error': str}}
    """
    report = load_status_report()
    summary = report["summary"]
    
    all_successful = all(r.get("success", False) for r in bots_results.values())
    
    summary["total_runs"] += 1
    if all_successful:
        summary["successful_runs"] += 1
        summary["consecutive_failures"] = 0
    else:
        summary["failed_runs"] += 1
        summary["consecutive_failures"] += 1
    
    now = datetime.now().isoformat()
    for bot_name, result in bots_results.items():
        if bot_name not in report["bots"]:
            continue

        bot_info = report["bots"][bot_name]
        bot_info["last_run"] = now

        if result.get("success"):
            bot_info["status"] = "success"
            bot_info["last_success"] = now
            bot_info["error"] = None
            bot_info["entries_count"] = int(result.get("entries", 0))
        else:
            bot_info["status"] = "failed"
            bot_info["error"] = result.get("error", "Unknown error")

    all_statuses = [b["status"] for b in report["bots"].values()]
    if all(s in ["success", "pending"] for s in all_statuses) and any(s == "success" for s in all_statuses):
        report["bot_health"] = "healthy"
    elif any(s == "running" for s in all_statuses):
        report["bot_health"] = "running"
    elif any(s == "failed" for s in all_statuses):
        report["bot_health"] = "degraded"

    save_status_report(report)

def get_status_report():
    """Get the current status report as a dict."""
    return load_status_report()

def get_status_json():
    """Get the status report as a JSON string."""
    return json.dumps(get_status_report(), indent=2)
