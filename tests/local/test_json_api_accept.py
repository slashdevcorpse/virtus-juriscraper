"""JSON API scrapers ask for JSON, not the browser Accept."""

import importlib
import json
import unittest
from pathlib import Path

import httpx

from juriscraper.AbstractSite import VIRTUS_ACCEPT

EXAMPLES = (
    Path(__file__).parents[1] / "examples" / "opinions" / "united_states"
)

SITES = {
    "state.ind": "ind_example",
    "state.indctapp": "indctapp_example",
    "state.indtc": "indtc_example",
    "administrative_agency.ttab": "ttab_example",
    "federal_special.nmcca": "nmcca_example",
}


def negotiating_server(example: str) -> httpx.MockTransport:
    """Answer JSON to `Accept: application/json` and a 500 to anything else."""
    body = (EXAMPLES / f"{example}.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("Accept") == "application/json":
            return httpx.Response(
                200, content=body, headers={"Content-Type": "application/json"}
            )
        return httpx.Response(
            500,
            content=b"<Error/>",
            headers={"Content-Type": "application/xml"},
        )

    return httpx.MockTransport(handler)


class JsonApiAcceptTest(unittest.IsolatedAsyncioTestCase):
    async def scrape(
        self, module: str, example: str, accept: str | None = None
    ):
        site = importlib.import_module(
            f"juriscraper.opinions.united_states.{module}"
        ).Site(transport=negotiating_server(example))
        if accept is not None:
            site.request["headers"]["Accept"] = accept
        async with site:
            await site.parse()
        return site

    async def test_each_site_gets_its_cases_from_the_json_api(self):
        for module, example in SITES.items():
            with self.subTest(module=module):
                expected = json.loads(
                    (EXAMPLES / f"{example}.compare.json").read_text()
                )
                site = await self.scrape(module, example)
                self.assertEqual(
                    sorted(site.case_names),
                    sorted(case["case_names"] for case in expected),
                )

    async def test_the_browser_accept_fails_on_the_same_server(self):
        with self.assertRaises(httpx.HTTPStatusError):
            await self.scrape("state.ind", "ind_example", accept=VIRTUS_ACCEPT)
