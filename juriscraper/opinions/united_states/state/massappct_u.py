"""
Scraper for Massachusetts Appeals Court Rule 23.0 (formerly Rule 1:28)
CourtID: massappct
Court Short Name: Mass App Ct
Author: William Palin
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer:
Date: 2020-02-27
"""

from datetime import date, timedelta
from urllib.parse import urlencode

from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


def _labeled(row: HtmlElement, prefix: str) -> str:
    """The value next to a heading such as case-heading-1."""
    chunks = row.xpath(
        f".//div[starts-with(@aria-labelledby, '{prefix}')]/text()"
    )
    return " ".join(part.strip() for part in chunks if part.strip())


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_date = date.today()
        self.backwards_days = 14
        self.base = "https://128archive.com"
        self.url = self.make_url()
        self.court_id = self.__module__
        self.expected_content_types = ["text"]

    def make_url(self) -> str:
        """Build the urls to query

        :return: The url parameters (encoded)
        """
        start_date = self.case_date - timedelta(days=self.backwards_days)
        first_date = start_date.strftime("%m/%d/%Y")
        end_date = self.case_date.strftime("%m/%d/%Y")
        self.parameters = (
            ("Action", "search"),
            ("DocketNumber", ""),
            ("PartyName", ""),
            ("ReleaseDateFrom", first_date),
            ("ReleaseDateTo", end_date),
            ("Keywords", ""),
            (
                "SortColumnName",
                [
                    "Release Date Descending Order",
                    "Release Date Descending Order",
                ],
            ),
            ("SortOrder", ""),
            ("CurrentPageNo", "1"),
            ("Pages", "1"),
            ("PageSize", "100"),
        )
        return f"{self.base}/?{urlencode(self.parameters)}"

    @override
    def _process_html(self) -> None:
        """Process the data.

        The 2020 page uses a div row and a ``col-md-7`` value. The current
        page uses an li row and a labeled ``col-md-9`` value.

        :return: None
        """
        rows = self.html.xpath("//div[@data-rowtype]")
        if rows:
            for row in rows:
                docket, name, filed = row.xpath(
                    ".//div[@class='col-md-7 font-bold']/text()"
                )
                path = row.xpath(".//div/div/a/@href")[0]
                self.cases.append(
                    {
                        "date": filed.strip(),
                        "docket": docket.strip(),
                        "name": titlecase(name.strip()),
                        "url": path,
                        "status": "Unpublished",
                    }
                )
            return
        for row in self.html.xpath("//li[@data-rowtype]"):
            self.cases.append(
                {
                    "date": _labeled(row, "release-heading"),
                    "docket": _labeled(row, "docket-heading"),
                    "name": titlecase(_labeled(row, "case-heading")),
                    "url": row.xpath(
                        ".//a[contains(@href, 'DownloadDisposition')]/@href"
                    )[0],
                    "status": "Unpublished",
                }
            )
