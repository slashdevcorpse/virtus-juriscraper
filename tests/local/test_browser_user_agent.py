"""The default agent is the Chrome 151 desktop string (D-240)."""

import unittest

import httpx

from juriscraper.AbstractSite import (
    VIRTUS_ACCEPT,
    VIRTUS_ACCEPT_LANGUAGE,
    VIRTUS_USER_AGENT,
    AbstractSite,
    browser_request_headers,
)
from juriscraper.lasc.http import LASCSession
from juriscraper.opinions.united_states.state.mich import Site as Mich
from juriscraper.opinions.united_states.state.minn import Site as Minn
from juriscraper.opinions.united_states.state.tenn import Site as Tenn

_BROWSER = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)


class BrowserUserAgentTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.site = AbstractSite()

    async def asyncTearDown(self):
        await self.site.request["session"].aclose()

    def test_the_string_matches_chrome_151(self):
        self.assertEqual(VIRTUS_USER_AGENT, _BROWSER)
        self.assertEqual(AbstractSite.chrome_user_agent, _BROWSER)
        self.assertEqual(
            AbstractSite.chrome_user_agent,
            browser_request_headers(VIRTUS_USER_AGENT)["User-Agent"],
        )
        self.assertNotIn("virtusrt.com", VIRTUS_USER_AGENT)

    def test_the_session_sends_the_browser_headers(self):
        headers = self.site.request["headers"]
        self.assertEqual(headers["User-Agent"], _BROWSER)
        self.assertEqual(headers["Accept"], VIRTUS_ACCEPT)
        self.assertEqual(headers["Accept-Language"], VIRTUS_ACCEPT_LANGUAGE)

    async def test_a_download_sends_the_browser_headers(self):
        seen: dict[str, str] = {}

        async def fake_get(
            url: str,
            headers: dict[str, str],
            cookies: dict[str, str],
            timeout: int,
        ) -> httpx.Response:
            del url, cookies, timeout
            seen.update(headers)
            return httpx.Response(200, content=b"opinion-bytes")

        self.site.request["session"].get = fake_get
        got = await self.site.download_content(
            "https://example.gov/a.pdf", doctor_is_available=False
        )
        self.assertEqual(got, b"opinion-bytes")
        self.assertEqual(seen["User-Agent"], _BROWSER)
        self.assertEqual(seen["Accept"], VIRTUS_ACCEPT)
        self.assertEqual(seen["Accept-Language"], VIRTUS_ACCEPT_LANGUAGE)

    def test_kept_site_overrides(self):
        mich = Mich()
        tenn = Tenn()
        minn = Minn()
        lasc = LASCSession()
        self.addAsyncCleanup(mich.request["session"].aclose)
        self.addAsyncCleanup(tenn.request["session"].aclose)
        self.addAsyncCleanup(minn.request["session"].aclose)
        self.addAsyncCleanup(lasc.aclose)
        self.assertEqual(mich.request["headers"]["User-Agent"], "")
        self.assertEqual(tenn.request["headers"]["User-Agent"], "Juriscraper")
        self.assertIn("Safari/", minn.request["headers"]["User-Agent"])
        self.assertNotIn("Chrome/151", minn.request["headers"]["User-Agent"])
        self.assertEqual(lasc.user_agent, "Juriscraper")
