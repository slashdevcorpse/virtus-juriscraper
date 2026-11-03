"""Alabama API releases are not always opinion releases."""

import json
import unittest

from juriscraper.opinions.united_states.state import alacivapp


class TestAlaPublicationSkip(unittest.TestCase):
    def test_order_only_release_yields_no_cases(self) -> None:
        site = alacivapp.Site()
        site.json = json.loads(
            """
            {
              "publicationDate": "2026-10-30T21:58:31.924+00:00",
              "publicationItems": [
                {
                  "title": "Example v. Example",
                  "caseNumber": "CL-2026-0001",
                  "caseInstanceUUID": "00000000-0000-0000-0000-000000000001",
                  "groupName": "Judge",
                  "documents": [{"documentLinkUUID": "00000000-0000-0000-0000-000000000002", "documentName": "Order"}]
                }
              ]
            }
            """
        )
        site._process_html()
        self.assertEqual(site.cases, [])

    def test_opinion_release_is_kept(self) -> None:
        site = alacivapp.Site()
        site.json = json.loads(
            """
            {
              "publicationDate": "2026-10-23T21:58:31.924+00:00",
              "publicationItems": [
                {
                  "title": "Example v. Example (Appeal from Mobile Circuit Court: DR-24-1).",
                  "caseNumber": "CL-2026-0002",
                  "caseInstanceUUID": "00000000-0000-0000-0000-000000000003",
                  "groupName": "Judge",
                  "documents": [{"documentLinkUUID": "00000000-0000-0000-0000-000000000004", "documentName": "Opinion"}]
                }
              ]
            }
            """
        )
        site._process_html()
        self.assertEqual(len(site.cases), 1)
        self.assertEqual(site.cases[0]["docket"], "CL-2026-0002")
