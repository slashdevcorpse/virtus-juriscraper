"""Scraper for Louisiana Court of Appeal, Fourth Circuit
CourtID: lactapp_4
Court Short Name: La. Ct. App. 4th Cir.
Author: Luis-manzur
History:
  2025-04-22: Created by Luis-manzur
  2026-11-05: The opinion search lives on Search.aspx. Each result
    labels Parties, Decree, Opinion Date and Document.
"""

import re
from datetime import date, datetime

from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.type_utils import OpinionType
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


def _field_text(node: HtmlElement) -> str:
    """Field text without the label or the screen-reader duplicate."""
    chunks = node.xpath(
        ".//text()[not(ancestor::strong) and "
        "not(ancestor::span[contains(@class, 'sr-only')])]"
    )
    return " ".join(part.strip() for part in chunks if part.strip())


def _paragraph(result: HtmlElement, label: str) -> HtmlElement | None:
    nodes = result.xpath(f".//p[strong[contains(., '{label}')]]")
    return nodes[0] if nodes else None


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(1992, 1, 1)
    days_interval = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.la4th.org/Search.aspx"
        self.search_date = datetime.today()
        self.make_backscrape_iterable(kwargs)
        self.status = "Published"
        self.parameters = {
            "__EVENTTARGET": "ctl00$Main$btnOpMonthYearSearch",
        }

    @override
    def _process_html(self) -> None:
        """Process the HTML to extract case details.

        :return None
        """

        results = self.html.xpath("//div[contains(@class, 'opinion-result')]")

        self.cases = []
        for result in results:
            if result.xpath(".//strong[contains(., 'Parties')]"):
                try:
                    self.cases.append(self._labeled_case(result))
                except ValueError as error:
                    logger.error("lactapp_4: skipping result: %s", error)
            else:
                self.cases.append(self._plain_case(result))

    def _labeled_case(self, result: HtmlElement) -> dict[str, str]:
        docket = result.xpath("./p[1]/strong/text()")[0]
        parties = _paragraph(result, "Parties")
        decree = _paragraph(result, "Decree")
        filed = _paragraph(result, "Opinion Date")
        if filed is None:
            filed = _paragraph(result, "Decision Date")
        if parties is None or filed is None:
            raise ValueError("opinion result has no parties or date")
        if decree is None:
            disposition = ""
        else:
            disposition = titlecase(_field_text(decree))
        return {
            "docket": docket.strip(),
            "name": titlecase(_field_text(parties)),
            "disposition": disposition,
            "date": _field_text(filed),
            "url": result.xpath(".//a[contains(@href, '.pdf')]/@href")[0],
        }

    def _plain_case(self, result: HtmlElement) -> dict[str, str]:
        docket = result.xpath(".//strong/text()")[0]
        name = (
            result.xpath(".//p[not(strong)]/text()")[0]
            .replace(" VS. .", ".")
            .strip()
        )
        decree = result.xpath(
            ".//p[strong[contains(text(), 'Decree')]]/text()"
        )[0]
        date = result.xpath(
            ".//p[strong[contains(text(), 'Opinion Date')]]/text()"
        )[0]
        download_url = result.xpath(
            ".//p/a[contains(text(), 'View Document')]/@href"
        )[0]
        return {
            "docket": docket,
            "name": titlecase(name),
            "disposition": titlecase(decree),
            "date": date,
            "url": download_url,
        }

    def update_parameters(self) -> None:
        """Set year and month values in the parameters for the search.

        Updates the parameters for the search request with the current search date.

        :return None
        """
        self.parameters.update(
            {
                "ctl00$Main$ddlOpMonth": self.search_date.strftime("%B"),
                "ctl00$Main$ddlOpYear": self.search_date.strftime("%Y"),
            }
        )

        for input in self.html.xpath('//input[@type="hidden"][@name]'):
            name = input.get("name")
            value = input.get("value", "")

            self.parameters[name] = value

    async def _download_backwards(self, search_date: date) -> None:
        """Download and process HTML for a given target date.

        :param search_date (date): The date for which to download and process opinions.
        :return: None; sets the target date, downloads the corresponding HTML
        and processes the HTML to extract case details.
        """
        self.search_date = search_date
        self.html = await self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )

    async def _download(self, request_dict=None) -> HtmlElement:
        """Download the HTML content for the current search state.

        :param request_dict (dict, optional): Additional request parameters.
        :return lxml.html.HtmlElement: The downloaded HTML content.
        """
        if not self.test_mode_enabled():
            if not self.html:
                self.html = await super()._download()

            self.update_parameters()
            self.method = "POST"
        return await super()._download()

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extracts structured metadata from the provided opinion text.

        :param scraped_text: The content of the document downloaded
        :return Metadata to be added to the case
        """
        metadata: dict[str, dict] = {
            "OpinionCluster": {},
            "Opinion": {},
            "Docket": {},
        }
        pattern = r"^\s+[*]{6,}\n(?P<judge>.*)\s+[*]{6,}$"
        pattern2 = r"\s+\*{5,}(?:.*\n)*?\s+(\s+(?P<judge>.*)[,.] J\..*(RESULT|REASON|CONCUR))"
        pattern3 = r"\(Court composed of (?P<judges>.*?)\)"

        m = re.search(pattern, scraped_text, flags=re.MULTILINE)
        m2 = re.search(pattern2, scraped_text, flags=re.MULTILINE)
        m3 = re.search(pattern3, scraped_text, flags=re.DOTALL)

        if m:
            metadata["Opinion"]["author_str"] = titlecase(
                m.groups()[0].strip().replace("\n", "").capitalize()
            )
            metadata["Opinion"]["type"] = OpinionType.MAJORITY.value

        elif m2:
            metadata["Opinion"]["author_str"] = titlecase(
                m2.group("judge").split(" ")[-1].strip()
            )

            match = re.search(r"\*{7,}\s*(.*)", scraped_text, flags=re.DOTALL)

            text = match.group(1).lower() if match else ""
            if "in part" in text:
                metadata["Opinion"]["type"] = (
                    OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART.value
                )
            elif "concurs" in text or "concurring" in text:
                metadata["Opinion"]["type"] = OpinionType.CONCURRENCE.value
            elif "dissents" in text or "dissenting" in text:
                metadata["Opinion"]["type"] = OpinionType.DISSENT.value

        if m3:
            judges = (
                m3.groups()[0]
                .strip()
                .replace("\n", " ")
                .replace(", ", "; ")
                .replace(",", "; ")
            )

            metadata["OpinionCluster"]["judges"] = judges
            metadata["Docket"]["panel_str"] = judges

        return metadata
