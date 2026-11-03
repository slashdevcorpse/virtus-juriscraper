"""Iowa reads one opinions page and leaves the Next link for the caller."""

import asyncio

from lxml import html

from juriscraper.AbstractSite import AbstractSite
from juriscraper.opinions.united_states.state.iowa import Site
from juriscraper.opinions.united_states.state.iowactapp import (
    Site as Appeals,
)

PAGE = """
<html><body>
<h3>Case No. 25-0001: Alpha v. Beta</h3>
<p>Filed January 2, 2026</p>
<p><a href="/courtcases/1/embed/SupremeCourtOpinion">PDF</a></p>
<div class="pagination-next-page">
<a href="/iowa-courts/supreme-court/supreme-court-opinions/page/2">Next</a>
</div>
</body></html>
"""


def test_download_reads_one_page_and_exposes_the_next_url(monkeypatch):
    tree = html.fromstring(PAGE)
    walked: list[str] = []

    async def parent(self, request_dict=None):
        return tree

    async def walk(self, url):
        walked.append(url)
        raise AssertionError(url)

    monkeypatch.setattr(AbstractSite, "_download", parent)
    monkeypatch.setattr(Site, "_get_html_tree_by_url", walk)
    site = Site()

    async def run():
        await asyncio.wait_for(site._download(), timeout=2)

    asyncio.run(run())
    assert walked == []
    assert site.next_page_url == (
        "/iowa-courts/supreme-court/supreme-court-opinions/page/2"
    )
    assert len(site.cases) == 1
    assert Appeals._download is Site._download
