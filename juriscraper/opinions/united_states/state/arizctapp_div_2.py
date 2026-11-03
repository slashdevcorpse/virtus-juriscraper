"""
Scraper for Court of Appeals of Arizona, Division 2
CourtID: arizctapp_div_2
Court Short Name: arizctapp_div_2
Author: Andrei Chelaru
Reviewer: mlr
History:
    2014-07-23: Created by Andrei Chelaru
    2021-12-10: URL changed to recent opinions page, satsuki-chan
"""

import re
from urllib.parse import urljoin

from typing_extensions import override

from juriscraper.lib.string_utils import clean_if_py3, titlecase
from juriscraper.opinions.united_states.state import ariz
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    extract_from_text = ariz.Site.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # recentOpinionsHTML.cfm 301s to RecentOpinionsHTML.php; follow is not guaranteed.
        self.url = "https://www.appeals2.az.gov/RecentOpinionsHTML.php"
        self.cases = []
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        for item in self.html.xpath("//table//a[contains(@href, '.pdf')]"):
            self._append_table_row(item)
        for block in self.html.xpath("//div[contains(@class, 'gray-border-thick')]"):
            self._append_card_block(block)

    def _append_table_row(self, item) -> None:
        docket = item.xpath("./text()")[0]
        url = item.xpath("./@href")[0]
        names = item.xpath("./following::td[1]/*/text()")
        if not names:
            return
        name = names[0]
        date_string = item.xpath("./following::td[2]/text()")[0].strip()
        date = clean_if_py3(date_string).rsplit(":", 1)[1].strip()
        summary_list = item.xpath("./following::tr[1]//text()")
        summary = "".join(summary_list).strip()
        self._append_case(name, date, docket, url, summary)

    def _append_card_block(self, block) -> None:
        link = block.xpath(".//a[contains(@href, 'Opinion.pdf')]")
        if not link:
            return
        anchor = link[0]
        docket = anchor.text_content().strip()
        url = urljoin(self.url, anchor.get("href", ""))
        title = block.xpath(
            "normalize-space(.//div[./p[contains(normalize-space(.), 'Case Title')]])"
        )
        name = re.sub(r"^Case Title:\s*", "", title).strip()
        filed = block.xpath(
            "normalize-space(.//div[./p[contains(normalize-space(.), 'Opinion Filed')]])"
        )
        date = re.sub(r"^Opinion Filed:\s*", "", filed).strip()
        summary = block.xpath("string(.//div[contains(@class, 'py-20')])").strip()
        self._append_case(name, date, docket, url, summary)

    def _append_case(
        self, name: str, date: str, docket: str, url: str, summary: str
    ) -> None:
        if not (name and docket and url):
            return
        self.cases.append(
            {
                "name": titlecase(name),
                "date": date,
                "docket": docket,
                "url": url,
                "summary": summary,
                "status": "Published",
            }
        )
