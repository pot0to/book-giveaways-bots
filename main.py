import argparse
import time
from goodreads_playwright import job as goodreads_job
from storygraph_playwright import job as storygraph_job
from status_report import initialize_status_report, update_bot_status, record_run_result

def run_all_bots():
    print("--- Starting Daily Sweep ---")
    results = {}
    
    # Goodreads
    try:
        update_bot_status("goodreads", "running")
        result = goodreads_job()
        success = bool(result.get("success", False))
        entries_count = int(result.get("entered_count", 0))
        error = result.get("error")
        results["goodreads"] = {
            "success": success,
            "entries": entries_count,
            "error": error
        }
        print("Goodreads completed successfully" if success else f"Goodreads failed: {error}")
    except Exception as e:
        error_msg = f"Goodreads failed: {e}"
        print(error_msg)
        results["goodreads"] = {
            "success": False,
            "entries": 0,
            "error": str(e)
        }
    
    # StoryGraph
    try:
        update_bot_status("storygraph", "running")
        result = storygraph_job()
        success = bool(result.get("success", False))
        entries_count = int(result.get("entered_count", 0))
        error = result.get("error")
        results["storygraph"] = {
            "success": success,
            "entries": entries_count,
            "error": error
        }
        print("StoryGraph completed successfully" if success else f"StoryGraph failed: {error}")
    except Exception as e:
        error_msg = f"StoryGraph failed: {e}"
        print(error_msg)
        results["storygraph"] = {
            "success": False,
            "entries": 0,
            "error": str(e)
        }
    
    # Record overall results
    record_run_result(results)
    print("--- Sweep Complete ---")
    return results

def run_scheduler(run_time):
    import schedule

    print(f"Scheduling daily sweep at {run_time}")
    schedule.every().day.at(run_time).do(run_all_bots)
    while True:
        schedule.run_pending()
        time.sleep(60)

def parse_args():
    parser = argparse.ArgumentParser(description="Run giveaway bots once or on a local daily schedule.")
    parser.add_argument(
        "--mode",
        choices=["once", "schedule"],
        default="once",
        help="Run once (default, CI-friendly) or run continuously on a local schedule."
    )
    parser.add_argument(
        "--time",
        default="05:00",
        help="Daily time for schedule mode in HH:MM format."
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print("Global Bot Runner Initialized...")
    initialize_status_report()

    if args.mode == "schedule":
        run_scheduler(args.time)
    else:
        results = run_all_bots()
        all_successful = all(r.get("success", False) for r in results.values())
        raise SystemExit(0 if all_successful else 1)