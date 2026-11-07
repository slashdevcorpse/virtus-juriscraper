"""lactapp_4 posts the month search with the LinkButton as __EVENTTARGET."""

import unittest
from pathlib import Path
from urllib.parse import parse_qs

import httpx

from juriscraper.opinions.united_states.state import lactapp_4

RESULTS = (
    Path(__file__).parents[1]
    / "examples"
    / "opinions"
    / "united_states"
    / "lactapp_4_example_search.html"
).read_bytes()
SEARCH_BUTTON = "ctl00$Main$btnOpMonthYearSearch"
# The hidden fields Search.aspx serves, as on 2026-11-07.
FORM = b"""<html><body><form method="post" action="./Search.aspx">
<input type="hidden" name="__EVENTTARGET" id="__EVENTTARGET" value="" />
<input type="hidden" name="__EVENTARGUMENT" id="__EVENTARGUMENT" value="" />
<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="state" />
<input type="hidden" name="__EVENTVALIDATION" value="valid" />
</form></body></html>"""


def search_aspx(posts: list[dict[str, list[str]]]) -> httpx.MockTransport:
    """Answer the form to a GET, and results only to a POST that names the
    search button, as the real page does."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, content=FORM)
        form = parse_qs(request.content.decode(), keep_blank_values=True)
        posts.append(form)
        body = RESULTS if form["__EVENTTARGET"] == [SEARCH_BUTTON] else FORM
        return httpx.Response(200, content=body)

    return httpx.MockTransport(handler)


class Lactapp4SearchPostbackTest(unittest.IsolatedAsyncioTestCase):
    async def test_the_month_search_names_the_search_button(self):
        posts: list[dict[str, list[str]]] = []
        site = lactapp_4.Site(transport=search_aspx(posts))
        async with site:
            await site.parse()
        (form,) = posts
        self.assertEqual(form["__EVENTTARGET"], [SEARCH_BUTTON])
        self.assertEqual(form["__VIEWSTATE"], ["state"])
        self.assertTrue(site.case_names)
