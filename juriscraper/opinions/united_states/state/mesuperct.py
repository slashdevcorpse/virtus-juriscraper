"""Scraper for Superior Court of Maine
CourtID: mesuperct
Court Short Name: Me. Super Ct
Author: William E. Palin
Date created: December 28, 2023

History:
  2023-12-28: Created
  2025-02-25: Implement backscraper
  2026-11-06: Backscrape bounds take a YYYY/MM/DD date, as the caller passes
  2026-11-07: Skip cases whose PDF is not on the legacy file host
"""

import asyncio
from datetime import date

import httpx
from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://apps.maine.edu/SuperiorCourt/show_list.jsp?plaintiff=&defendant=&year={}&code=&rule=&title=&number=&section=&Search=Search"
    start_year = 1999

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.current_year = date.today().year
        self.make_backscrape_iterable(kwargs)
        self.url = self.base_url.format(self.current_year)

    async def _download_backwards(self, year: int) -> None:
        """Sets the URL for the backwards download based on the given year.

        :param year: year to scrape
        :return: None
        """
        self.url = self.base_url.format(year)
        self.html = await self._download()
        await self._process_html()

    @override
    async def _process_html(self) -> None:
        """Processes the HTML content and extracts case information.

        Maine publishes decision PDFs only on request since about 2021. The
        legacy file host still serves older ones, so a listed case is kept
        only when its PDF answers 200.

        :return: None
        """
        cases = self._listed_cases()
        if not self.test_mode_enabled():
            limit = asyncio.Semaphore(4)
            present = await asyncio.gather(
                *(self._pdf_is_posted(case["url"], limit) for case in cases)
            )
            skipped = len(cases) - sum(present)
            if skipped:
                logger.info(
                    "mesuperct: skipped %s of %s cases with no posted PDF",
                    skipped,
                    len(cases),
                )
            cases = [case for case, ok in zip(cases, present) if ok]
        self.cases.extend(cases)

    async def _pdf_is_posted(self, url: str, limit: asyncio.Semaphore) -> bool:
        """Whether the decision PDF answers 200. A transport error keeps the
        case, so the document fetch can retry it."""
        async with limit:
            try:
                response = await self.request["session"].head(
                    url, headers=self.request["headers"], timeout=30
                )
            except httpx.HTTPError as error:
                logger.warning("mesuperct: HEAD %s failed: %s", url, error)
                return True
        return response.status_code == 200

    def _listed_cases(self) -> list[dict]:
        """Read the case rows of the listing table."""
        cases = []
        for row in self.html.xpath("//tr")[1:]:
            docket_number = row.xpath(".//td//a/text()")[0].strip()
            date = row.xpath(".//td/text()")[-1].strip()
            plaintiff = row.xpath(".//td/a/text()")[1].strip()
            defendant = row.xpath(".//td/a/text()")[2].strip()
            url = f"https://files.mainelaw.maine.edu/library/SuperiorCourt/decisions/{docket_number}.pdf"
            author = row.xpath(".//td/a/text()")[3].strip()
            cases.append(
                {
                    "date": date,
                    "docket": docket_number,
                    "url": url,
                    "name": f"{plaintiff} v. {defendant}",
                    "status": "Unpublished",
                    "judge": author,
                }
            )
        return cases

    @staticmethod
    def _year(value: str | int) -> int:
        """Read the year of a backscrape bound: 2020, "2020" or "2020/12/31"."""
        return int(str(value).split("/")[0])

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = self._year(start) if start else self.start_year
        end = self._year(end) + 1 if end else self.current_year

        self.back_scrape_iterable = range(start, end)
