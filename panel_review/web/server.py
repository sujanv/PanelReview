"""
Built-in local web dashboard server for PanelReview.
Provides zero-dependency live UI inspection, real-time filtering, and report downloads.
"""

import os
import json
import http.server
import socketserver
from typing import Optional
from panel_review.config import PanelConfig, load_config
from panel_review.scanner.repo_scanner import RepoScanner
from panel_review.engine.reviewer import ReviewEngine
from panel_review.engine.report import ReportGenerator


class PanelDashboardHandler(http.server.SimpleHTTPRequestHandler):
    config: Optional[PanelConfig] = None
    latest_report_html: str = ""

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if self.latest_report_html:
                self.wfile.write(self.latest_report_html.encode("utf-8"))
            elif os.path.exists("panel_review_report.html"):
                with open("panel_review_report.html", "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                html = "<html><body style='font-family:sans-serif;background:#0f172a;color:#f8fafc;padding:2rem;'><h2>🏛️ PanelReview Server Ready</h2><p>No report generated yet. Run <code>python3 -m panel_review.cli review</code> or invoke a scan.</p></body></html>"
                self.wfile.write(html.encode("utf-8"))
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            cfg = self.config or load_config()
            data = {
                "status": "online",
                "default_provider": cfg.default_provider,
                "default_model": cfg.default_model,
                "personas_count": len(cfg.get_enabled_personas()),
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def start_dashboard_server(port: int = 8080, config: Optional[PanelConfig] = None):
    """
    Starts the dashboard web server on specified port.
    """
    PanelDashboardHandler.config = config or load_config()
    with socketserver.TCPServer(("", port), PanelDashboardHandler) as httpd:
        print(f"\n🌐 PanelReview Live Dashboard listening on http://localhost:{port}")
        print("Press Ctrl+C to stop server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
