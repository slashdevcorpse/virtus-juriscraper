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
ALL = ["CUMbcd-cv-22-66", "CUMcv-20-537"]


def maine(seen_heads: list[str], other=None) -> httpx.MockTransport:
    """The listing, one posted PDF, and `other` (default a 404) for every
    other PDF. `other` is a status code or an exception to raise."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "apps.maine.edu":
            return httpx.Response(
                200, content=LISTING, headers={"Content-Type": "text/html"}
            )
        seen_heads.append(request.method)
        if request.url.path == POSTED:
            return httpx.Response(200)
        if isinstance(other, Exception):
            raise other
        return httpx.Response(other or 404)

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

    async def test_a_gone_pdf_is_skipped_but_an_error_keeps_the_case(self):
        cases = {
            410: ["CUMbcd-cv-22-66"],
            429: ALL,
            503: ALL,
            httpx.ConnectError("refused"): ALL,
        }
        for other, expected in cases.items():
            with self.subTest(other=other):
                site = mesuperct.Site(transport=maine([], other))
                async with site:
                    await site.parse()
                self.assertEqual(sorted(site.docket_numbers), expected)
