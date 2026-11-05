#!/usr/bin/env python

import os
import unittest

from juriscraper.lib.exceptions import InvalidDocumentError
from juriscraper.opinions.united_states.state import (
    ny,
    nyappdiv_1st,
    nyappterm_2nd,
)

# The Law Reporting Bureau search lists a slip opinion hours before the
# reporter posts it. On 2026-11-05 the listed link
# reporter/3dseries/2026/2026_06530.htm answered HTTP 200 with this page.
FIXTURE = os.path.join(
    "tests",
    "examples",
    "opinions",
    "invalid_document",
    "ny_reporter_not_posted.html",
)


class NyReporterNotPostedTest(unittest.TestCase):
    def test_the_reporter_not_found_page_is_an_invalid_document(self):
        with open(FIXTURE, "rb") as fixture_file:
            content = fixture_file.read()
        for module in (ny, nyappdiv_1st, nyappterm_2nd):
            with (
                self.subTest(module=module.__name__),
                self.assertRaises(InvalidDocumentError),
            ):
                module.Site().cleanup_content(content)
