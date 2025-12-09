import json
import sys
import time
import traceback
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def fetch_essay_links(base_url: str) -> list[dict[str, str]]:
    """Fetch all essay links from Paul Graham's website."""
    articles_url = f"{base_url}/articles.html"
    response = requests.get(articles_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    essays = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and href.endswith(".html") and href != "articles.html":
            essays.append(
                {"url": f"{base_url}/{href}", "filename": href.replace(".html", ".pdf")}
            )
    return essays


def convert_essay_to_pdf(essay: dict[str, str], output_dir: Path, page) -> None:
    """Convert a single essay to PDF using Playwright."""
    output_path = output_dir / essay["filename"]
    page.goto(essay["url"], wait_until="networkidle")
    page.pdf(path=str(output_path), format="A4", print_background=True)


def scrape_pg_essays():
    """Main function to scrape and convert Paul Graham essays to PDF."""
    BASE_URL = "http://www.paulgraham.com"
    OUTPUT_DIR = Path("pg_essays")

    # Fetch essay links
    essays = fetch_essay_links(BASE_URL)
    print(f"\nFound {len(essays)} essays")

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Track progress
    errors = []
    successful = 0

    # Use Playwright for PDF conversion
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        # Process each essay
        for idx, essay in enumerate(essays, 1):
            try:
                print(f"[{idx}/{len(essays)}] Processing: {essay['filename']}")
                convert_essay_to_pdf(essay, OUTPUT_DIR, page)
                successful += 1
                time.sleep(0.5)  # Rate limiting

            except KeyboardInterrupt:
                print(f"\n⚠️  Interrupted at: {essay['filename']}")
                break
            except Exception as e:
                error_info = {
                    "filename": essay["filename"],
                    "url": essay["url"],
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                }
                errors.append(error_info)
                print(f"\n❌ ERROR: {essay['filename']} - {e}", file=sys.stderr)

        browser.close()

    # Print summary
    print(f"\n{'='*60}")
    print(
        f"Summary: ✅ {successful}/{len(essays)} successful | ❌ {len(errors)} errors"
    )

    if errors:
        print(f"\n{'='*60}")
        print("Failed essays:")
        for error in errors:
            print(f"  • {error['filename']}: {error['error']}")

        error_file = Path("pg_essays_errors.json")
        error_file.write_text(json.dumps(errors, indent=2))
        print(f"\nFull error log: {error_file}")


if __name__ == "__main__":
    scrape_pg_essays()
