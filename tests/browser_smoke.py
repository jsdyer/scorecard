"""Exercise the built starter at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=os.environ.get("BROWSER_EXECUTABLE") or None)
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.wait_for_selector("#rows tr")
                assert "decision" in page.locator("#headline").inner_text()
                assert page.locator("#rows tr a").first.get_attribute("href").startswith("https://www.bankofcanada.ca/")
                page.locator("#view").select_option("latest")
                assert "matched" in page.locator("#headline").inner_text()
                assert page.locator("#target").is_disabled()
                assert page.locator("#rows tr").count() >= 12
                with page.expect_download() as event:
                    page.locator("#download").click()
                assert event.value.suggested_filename == "policy-rate-history.csv"
                page.locator("#view").select_option("target")
                page.locator("#target").select_option(index=0)
                assert "Pending" in page.locator("#rows").inner_text()
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: project subpath, date filters, pending records, CSV export and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
