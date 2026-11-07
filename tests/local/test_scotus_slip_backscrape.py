import unittest
from datetime import date

import httpx

from juriscraper.opinions.united_states.federal_appellate import (
    scotus_slip,
)

BASE = "https://www.supremecourt.gov/opinions/slipopinion"


def recorder(seen: list[str]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(
            200,
            content=b"<html><body><table></table></body></html>",
            headers={"Content-Type": "text/html"},
        )

    return httpx.MockTransport(handler)


class ScotusSlipBackscrapeTest(unittest.IsolatedAsyncioTestCase):
    async def urls_for(self, start: str, end: str) -> list[str]:
        seen: list[str] = []
        site = scotus_slip.Site(
            transport=recorder(seen),
            backscrape_start=start,
            backscrape_end=end,
        )
        async with site:
            for item in list(site.back_scrape_iterable):
                await site._download_backwards(item)
        return seen

    async def test_a_window_across_october_asks_for_both_terms(self):
        self.assertEqual(scotus_slip.Site.get_term(date(2026, 5, 11)), 25)
        self.assertEqual(scotus_slip.Site.get_term(date(2026, 11, 7)), 26)
        self.assertEqual(
            await self.urls_for("2026/05/11", "2026/11/07"),
            [f"{BASE}/25", f"{BASE}/26"],
        )

    async def test_a_window_inside_one_term_asks_for_that_term(self):
        self.assertEqual(scotus_slip.Site.get_term(date(2026, 5, 1)), 25)
        self.assertEqual(scotus_slip.Site.get_term(date(2026, 9, 1)), 25)
        self.assertEqual(
            await self.urls_for("2026/05/01", "2026/09/01"),
            [f"{BASE}/25"],
        )
