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


class ConsolidatedCaseTest(unittest.IsolatedAsyncioTestCase):
    """03-26-00672-CV lists two "Memorandum opinion issued" events on one day.

    Recorded from the live case page on 2026-11-04. Before the split, the
    cluster held two majority opinions and the sanity check raised
    InsanityException, which failed the whole txctapp3 scrape.
    """

    async def test_each_majority_opinion_gets_its_own_cluster(self):
        site = _site("txctapp3")
        path = os.path.join(EXAMPLES, "txctapp3_consolidated_case.html")
        with open(path, encoding="utf8") as f:
            tree = lxml_html.fromstring(f.read())

        async def fake_get(url: str):
            return tree

        site._get_html_tree_by_url = fake_get
        await site._add_case(
            "https://search.txcourts.gov/Case.aspx?cn=03-26-00672-CV",
            "10/30/2026",
            "03-26-00672-CV",
        )

        self.assertEqual(len(site.cases), 2)
        urls = [op["url"] for c in site.cases for op in c["sub_opinions"]]
        self.assertEqual(len(set(urls)), 2)
        for case in site.cases:
            self.assertEqual(
                [op["type"] for op in case["sub_opinions"]], ["020lead"]
            )
            self.assertEqual(case["docket"], "03-26-00672-CV")
            for op in case["sub_opinions"]:
                self.assertNotIn("disposition", op)
        self.assertEqual(
            [c["disposition"] for c in site.cases], ["Abated", "Consolidated"]
        )

    async def test_single_majority_keeps_last_majority_disposition(self):
        case = {
            "disposition": "Affirmed",
            "sub_opinions": [
                {"url": "a", "type": "020lead", "disposition": "Affirmed"},
                {"url": "b", "type": "040dissent"},
            ],
        }
        (out,) = texapp.Site._split_majorities(case)
        self.assertEqual(out["disposition"], "Affirmed")
        self.assertNotIn("disposition", out["sub_opinions"][0])


class CriminalAppealsOrderTest(unittest.IsolatedAsyncioTestCase):
    """WR-97,994-01 issues its opinion as one document typed "Order".

    Recorded from the live case page on 2026-11-05. The document type was
    none of the four that texcrimapp knew, so the opinion had no type and
    the majority split raised KeyError, which failed the whole scrape.
    """

    async def test_order_document_is_the_lead_opinion(self):
        site = _site("texcrimapp")
        path = os.path.join(EXAMPLES, "texcrimapp_order_case.html")
        with open(path, encoding="utf8") as f:
            tree = lxml_html.fromstring(f.read())

        async def fake_get(url: str):
            return tree

        site._get_html_tree_by_url = fake_get
        await site._add_case(
            "https://search.txcourts.gov/Case.aspx?cn=WR-97,994-01",
            "10/22/2026",
            "WR-97,994-01",
        )

        (case,) = site.cases
        self.assertEqual(
            [op["type"] for op in case["sub_opinions"]], ["020lead"]
        )
        self.assertIn(
            "MediaVersionID=53773e95-e312-4da1-b679-b544edb3c73c",
            case["sub_opinions"][0]["url"],
        )
        self.assertEqual(case["disposition"], "Out of Time Appeal Granted")
