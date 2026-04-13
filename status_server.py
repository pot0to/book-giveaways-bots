"""
Simple Flask server to serve the bot status report as JSON.
Optional: Use this to display bot health on a homepage.

Usage:
    python status_server.py
    
Then access:
    http://localhost:5000/status - Get full status report
    http://localhost:5000/status/health - Get bot health summary
"""

from flask import Flask, jsonify, render_template_string
from status_report import get_status_report, get_status_json
import json

app = Flask(__name__)

# Simple HTML dashboard (optional)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Giveaway Bots Status</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .bot-card {
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 8px;
            background: #fafafa;
        }
        .bot-card h3 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 12px;
            margin-bottom: 10px;
        }
        .status-success {
            background-color: #d4edda;
            color: #155724;
        }
        .status-failed {
            background-color: #f8d7da;
            color: #721c24;
        }
        .status-running {
            background-color: #d1ecf1;
            color: #0c5460;
        }
        .status-pending {
            background-color: #e2e3e5;
            color: #383d41;
        }
        .status-healthy {
            background-color: #d4edda;
            color: #155724;
        }
        .status-degraded {
            background-color: #fff3cd;
            color: #856404;
        }
        .info-row {
            margin: 8px 0;
            font-size: 14px;
            color: #555;
        }
        .info-label {
            font-weight: bold;
            display: inline-block;
            width: 120px;
        }
        .error-text {
            color: #d32f2f;
            font-size: 12px;
            margin-top: 5px;
        }
        .summary {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }
        .summary-item {
            text-align: center;
        }
        .summary-number {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }
        .summary-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .last-updated {
            text-align: right;
            font-size: 12px;
            color: #999;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Giveaway Bots Status</h1>
        
        <div id="dashboard">
            <p>Loading dashboard...</p>
        </div>
    </div>

    <script>
        async function loadDashboard() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                let html = '';
                
                // Overall health
                const healthClass = 'status-' + data.bot_health;
                html += `<div style="margin-bottom: 20px;">
                    <span class="status-badge ${healthClass}" style="font-size: 14px;">
                        Overall Health: ${data.bot_health.toUpperCase()}
                    </span>
                </div>`;
                
                // Summary stats
                const summary = data.summary;
                html += `
                    <div class="summary">
                        <h3>Summary Statistics</h3>
                        <div class="summary-grid">
                            <div class="summary-item">
                                <div class="summary-number">${summary.total_runs}</div>
                                <div class="summary-label">Total Runs</div>
                            </div>
                            <div class="summary-item">
                                <div class="summary-number">${summary.successful_runs}</div>
                                <div class="summary-label">Successful Runs</div>
                            </div>
                            <div class="summary-item">
                                <div class="summary-number">${summary.failed_runs}</div>
                                <div class="summary-label">Failed Runs</div>
                            </div>
                            <div class="summary-item">
                                <div class="summary-number">${summary.consecutive_failures}</div>
                                <div class="summary-label">Consecutive Failures</div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Bot cards
                html += '<div class="status-grid">';
                for (const [botName, botData] of Object.entries(data.bots)) {
                    const statusClass = 'status-' + botData.status;
                    html += `
                        <div class="bot-card">
                            <h3>${botName.charAt(0).toUpperCase() + botName.slice(1)}</h3>
                            <span class="status-badge ${statusClass}">${botData.status.toUpperCase()}</span>
                            <div class="info-row">
                                <span class="info-label">Last Run:</span>
                                <span>${botData.last_run ? new Date(botData.last_run).toLocaleString() : 'Never'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Last Success:</span>
                                <span>${botData.last_success ? new Date(botData.last_success).toLocaleString() : 'Never'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Entries:</span>
                                <span>${botData.entries_count}</span>
                            </div>
                            ${botData.error ? `<div class="error-text">Error: ${botData.error}</div>` : ''}
                        </div>
                    `;
                }
                html += '</div>';
                
                html += `<div class="last-updated">Last updated: ${new Date(data.last_updated).toLocaleString()}</div>`;
                
                document.getElementById('dashboard').innerHTML = html;
            } catch (error) {
                console.error('Error loading dashboard:', error);
                document.getElementById('dashboard').innerHTML = '<p style="color: red;">Error loading status. Make sure the server is running.</p>';
            }
        }
        
        // Load on page load and refresh every 30 seconds
        loadDashboard();
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Serve the status dashboard HTML."""
    return render_template_string(DASHBOARD_HTML)

@app.route('/status')
def status():
    """Return the full status report as JSON."""
    return jsonify(get_status_report())

@app.route('/status/health')
def health():
    """Return a simplified health check."""
    report = get_status_report()
    return jsonify({
        "bot_health": report.get("bot_health"),
        "last_updated": report.get("last_updated"),
        "bots": {
            name: {
                "status": bot.get("status"),
                "last_run": bot.get("last_run")
            }
            for name, bot in report.get("bots", {}).items()
        }
    })

@app.route('/status/raw')
def status_raw():
    """Return the raw JSON status as plain text (for direct API access)."""
    return get_status_json(), 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    print("Starting Giveaway Bots Status Server...")
    print("Dashboard: http://localhost:5000/")
    print("API - Full status: http://localhost:5000/status")
    print("API - Health check: http://localhost:5000/status/health")
    app.run(debug=False, host='0.0.0.0', port=5000)
