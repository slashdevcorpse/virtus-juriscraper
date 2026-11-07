"""mesuperct keeps only the cases whose PDF the legacy file host serves."""

import unittest
from pathlib import Path

import httpx

from juriscraper.opinions.united_states.state import mesuperct

LISTING = (
    Path(__file__).parents[1]
    / "examples"
    / "opinions"
    / "united_states"
    / "mesuperct_example.html"
).read_bytes()
POSTED = "/library/SuperiorCourt/decisions/CUMbcd-cv-22-66.pdf"


def maine(seen_heads: list[str]) -> httpx.MockTransport:
    """The listing, one posted PDF, and a 404 for every other PDF."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "apps.maine.edu":
            return httpx.Response(
                200, content=LISTING, headers={"Content-Type": "text/html"}
            )
        seen_heads.append(request.method)
        return httpx.Response(200 if request.url.path == POSTED else 404)

    return httpx.MockTransport(handler)


class MesuperctPostedPdfTest(unittest.IsolatedAsyncioTestCase):
    async def test_a_case_without_a_posted_pdf_is_skipped(self):
        heads: list[str] = []
        site = mesuperct.Site(transport=maine(heads))
        async with site:
            await site.parse()
        self.assertEqual(list(site.docket_numbers), ["CUMbcd-cv-22-66"])
        self.assertEqual(heads, ["HEAD", "HEAD"])

    async def test_a_backscrape_year_is_filtered_too(self):
        site = mesuperct.Site(
            transport=maine([]), backscrape_start="2022", backscrape_end="2022"
        )
        async with site:
            await site._download_backwards(2022)
        self.assertEqual(
            [case["docket"] for case in site.cases], ["CUMbcd-cv-22-66"]
        )
