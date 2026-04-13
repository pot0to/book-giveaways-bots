# Giveaway Bots Status Report Setup

This system provides comprehensive status reporting for your giveaway bots, allowing you to monitor bot health and activity from a homepage or API endpoint.

## Files Created

- **status_report.py** - Core status tracking module
- **status_server.py** - Flask server to serve status as API & dashboard
- **bot_status.json** - Auto-generated status file updated after each run

## Quick Start

### 1. Install Flask Dependency
```bash
pip install Flask==3.0.0
# Or update all dependencies:
pip install -r requirements.txt
```

### 2. Run the Status Server (Optional but Recommended)
```bash
python status_server.py
```

Then visit:
- **Dashboard**: http://localhost:5000/
- **Full API**: http://localhost:5000/status
- **Health Check**: http://localhost:5000/status/health

### 3. The bots automatically update status when running
Your updated `main.py` now automatically tracks:
- Bot execution status (running, success, failed)
- Number of entries for each bot
- Error messages
- Run history and statistics

## Status Report Structure

The `bot_status.json` file looks like this:

```json
{
  "last_updated": "2026-03-26T10:30:45.123456",
  "bot_health": "healthy",
  "bots": {
    "goodreads": {
      "status": "success",
      "last_run": "2026-03-26T10:30:40.123456",
      "last_success": "2026-03-26T10:30:40.123456",
      "error": null,
      "entries_count": 5
    },
    "storygraph": {
      "status": "success",
      "last_run": "2026-03-26T10:30:45.123456",
      "last_success": "2026-03-26T10:30:45.123456",
      "error": null,
      "entries_count": 3
    }
  },
  "summary": {
    "total_runs": 42,
    "successful_runs": 40,
    "failed_runs": 2,
    "consecutive_failures": 0
  }
}
```

## API Endpoints

### GET /status
Returns the full status report with all details.

**Response:**
```json
{
  "last_updated": "...",
  "bot_health": "healthy|degraded|running|initializing",
  "bots": {...},
  "summary": {...}
}
```

### GET /status/health
Simplified health check endpoint (lighter payload).

**Response:**
```json
{
  "bot_health": "healthy",
  "last_updated": "...",
  "bots": {
    "goodreads": {
      "status": "success",
      "last_run": "..."
    },
    ...
  }
}
```

### GET /
Visual dashboard displaying bot status and statistics (HTML).

## Statuses

- **healthy** - All bots successful or pending
- **degraded** - Some bots have failed
- **running** - Bots are currently executing
- **initializing** - First startup

## Bot Status Values

- **success** - Bot ran and completed successfully
- **failed** - Bot encountered an error
- **running** - Bot currently executing
- **pending** - Bot hasn't run yet

## Usage Examples

### In Python Code
```python
from status_report import update_bot_status, record_run_result

# Update single bot
update_bot_status("goodreads", "success", entries_count=5)

# Record complete run
results = {
    "goodreads": {"success": True, "entries": 5, "error": None},
    "storygraph": {"success": False, "entries": 0, "error": "Connection timeout"}
}
record_run_result(results)
```

### From Command Line / Cron
```bash
# Check bot status
curl http://localhost:5000/status | jq

# Quick health check
curl http://localhost:5000/status/health | jq
```

### In JavaScript / Frontend
```javascript
// Fetch status for homepage widget
async function getStatus() {
    const response = await fetch('http://localhost:5000/status');
    const data = await response.json();
    console.log(data);
}
```

## Integration with Homepage

### Option 1: Embed Dashboard iframe
```html
<iframe src="http://localhost:5000/" width="100%" height="600" style="border: none; border-radius: 8px;"></iframe>
```

### Option 2: Fetch and Custom Display
```javascript
fetch('http://localhost:5000/status')
    .then(r => r.json())
    .then(data => {
        console.log(`Bot Health: ${data.bot_health}`);
        console.log(`Last Run: ${data.bots.goodreads.last_run}`);
    });
```

### Option 3: Static JSON File
The `bot_status.json` file is updated after each run and can be served statically:
```
<img src="bot_status.json" style="display:none;" onload="loadStatus()">
```

## Docker Usage (if applicable)

The status server can also run in a separate container. Include this in your `compose.yaml`:

```yaml
status-server:
  build: .
  command: python status_server.py
  ports:
    - "5000:5000"
  volumes:
    - ./bot_status.json:/app/bot_status.json
  depends_on:
    - bot
```

## Troubleshooting

**Status not updating?**
- Ensure Flask is installed: `pip install Flask==3.0.0`
- The main.py bot runner automatically calls the status update functions
- Check that bot_status.json file exists and is writable

**Cannot access dashboard?**
- Make sure status_server.py is running: `python status_server.py`
- Try accessing http://localhost:5000/status/health to confirm server is up
- Check firewall/port availability

**CORS Issues with Homepage?**
If your homepage is on a different domain, you may need to add CORS support to `status_server.py`:
```python
from flask_cors import CORS
CORS(app)
```
Then install: `pip install flask-cors`

---

The status reporting system is now fully integrated with your bot runner!
