#!/usr/bin/env python


import unittest

from lxml import html

from juriscraper.oral_args.united_states.state import ill

# The court puts "ex rel" in an <em> inside the case-name span.
# The first text node of that span is only "People".
ROW = """
<table>
  <tr><th>Date</th><th>Docket</th><th>Name</th><th>Audio</th></tr>
  <tr>
    <td><span>09/23/2026</span></td>
    <td><span>132312</span></td>
    <td>
      <span class="case-name">People <em>ex rel</em> Mosser v. Kliment</span>
    </td>
    <td>
      <a data-audio="https://ilcourtsaudio.blob.core.windows.net/x/132312.mp3"></a>
    </td>
  </tr>
  <tr>
    <td><span>09/22/2026</span></td>
    <td><span>132234</span></td>
    <td><span class="case-name">People v. Vargas</span></td>
    <td>
      <a data-audio="https://ilcourtsaudio.blob.core.windows.net/x/132234.mp3"></a>
    </td>
  </tr>
</table>
"""


class IllOralArgumentCaseNameTest(unittest.TestCase):
    def test_case_name_keeps_italic_words(self):
        site = ill.Site()
        site.html = html.fromstring(ROW)
        site._process_html()
        names = [case["name"] for case in site.cases]
        self.assertEqual(
            names,
            [
                "People ex rel Mosser v. Kliment",
                "People v. Vargas",
            ],
        )
