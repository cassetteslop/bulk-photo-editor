"""Render quickstart.html to ../BulkPhotoEditor-QuickStart.pdf with headless Chromium (Playwright).
    python docs/pdf_src/build_pdf.py        (first: python docs/pdf_src/make_figures.py)"""
import os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "BulkPhotoEditor-QuickStart.pdf")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto("file://" + os.path.join(HERE, "quickstart.html"))
    pg.wait_for_load_state("networkidle")
    pg.pdf(path=OUT, format="Letter", print_background=True, prefer_css_page_size=True,
           margin=dict(top="16mm", bottom="18mm", left="16mm", right="16mm"))
    b.close()
print("wrote", os.path.abspath(OUT))
