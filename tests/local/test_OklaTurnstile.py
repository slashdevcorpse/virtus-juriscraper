#!/usr/bin/env python

import os
import unittest

from juriscraper.lib.exceptions import InvalidDocumentError
from juriscraper.opinions.united_states.state import (
    okla,
    oklaag,
    oklacivapp,
    oklacrimapp,
)

# On 2026-11-07 www.oscn.net answered opinion requests from AWS egress with
# this Cloudflare Turnstile page (HTTP 200). The client IP is replaced with a
# documentation address.
FIXTURE = os.path.join(
    "tests",
    "examples",
    "opinions",
    "invalid_document",
    "okla_turnstile.html",
)


class OklaTurnstileTest(unittest.TestCase):
    def test_the_turnstile_page_is_an_invalid_document(self):
        with open(FIXTURE, "rb") as fixture_file:
            content = fixture_file.read()
        for module in (okla, oklaag, oklacivapp, oklacrimapp):
            with (
                self.subTest(module=module.__name__),
                self.assertRaises(InvalidDocumentError),
            ):
                module.Site().cleanup_content(content)
