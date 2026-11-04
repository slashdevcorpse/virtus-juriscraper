"""Texas courts of appeals found through the released docket.

Since December 2024 the TAMES Document Search "Opinion" index holds no
documents for the 5th, 8th, 12th and 14th courts, so the scraper reads each
court's "Released Orders & Opinions" page for every day of the range instead.
"""

import importlib
import os
import unittest
from datetime import date

from lxml import html as lxml_html

from juriscraper.opinions.united_states.state import texapp

EXAMPLES = os.path.join("tests", "examples", "opinions", "united_states")
DOCKET_COURTS = {
    "txctapp5": "coa05",
    "txctapp8": "coa08",
    "txctapp12": "coa12",
    "txctapp14": "coa14",
}
SEARCH_COURTS = [
    "txctapp1",
    "txctapp2",
    "txctapp3",
    "txctapp4",
    "txctapp6",
    "txctapp7",
    "txctapp9",
    "txctapp10",
    "txctapp11",
    "txctapp13",
    "txctapp15",
    "texapp",
]


def _site(module: str) -> texapp.Site:
    return importlib.import_module(
        f"juriscraper.opinions.united_states.state.{module}"
    ).Site()


class ReleasedDocketCourtsTest(unittest.TestCase):
    def test_courts_without_opinion_index_use_released_docket(self):
        for module, coa in DOCKET_COURTS.items():
            with self.subTest(module=module):
                site = _site(module)
                self.assertEqual(site.coa_code, coa)
                self.assertIn(f"coa={coa}", site.url)

    def test_other_courts_keep_document_search(self):
        for module in SEARCH_COURTS:
            with self.subTest(module=module):
                self.assertIsNone(_site(module).coa_code)


class ReleasedDocketRequestsTest(unittest.IsolatedAsyncioTestCase):
    async def test_one_page_per_day_then_case_pages(self):
        site = _site("txctapp5")
        site.start_date, site.end_date = date(2026, 8, 12), date(2026, 8, 14)
        requested: list[str] = []

        async def fake_get(url: str):
            requested.append(url)
            name = (
                "txctapp5_example.html"
                if "Docket.aspx" in url
                else url.rsplit("/", 1)[1]
            )
            with open(os.path.join(EXAMPLES, name), encoding="utf8") as f:
                return lxml_html.fromstring(f.read())

        site._get_html_tree_by_url = fake_get
        await site._process_released_docket()

        self.assertEqual(
            [u for u in requested if "Docket.aspx" in u],
            [
                "https://search.txcourts.gov/Docket.aspx?coa=coa05"
                f"&FullDate=8/{day}/2026"
                for day in (12, 13, 14)
            ],
        )
        # The same two cases are on each page; each is parsed once.
        self.assertEqual(len(site.cases), 2)
        self.assertEqual({c["date"] for c in site.cases}, {"8/13/2026"})
