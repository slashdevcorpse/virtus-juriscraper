#!/usr/bin/env python

import unittest

from juriscraper.opinions.united_states.state import mesuperct

# The caller passes backscrape bounds as YYYY/MM/DD dates. The module read
# them with int() and raised ValueError on "2020/01/01". The publisher posts
# decision PDFs only up to 2020, so a backscrape is the way to reach text.


class MesuperctBackscrapeTest(unittest.TestCase):
    def years(self, **kwargs):
        return list(mesuperct.Site(**kwargs).back_scrape_iterable)

    def test_bounds_may_be_dates(self):
        self.assertEqual(
            self.years(
                backscrape_start="2019/01/01", backscrape_end="2020/12/31"
            ),
            [2019, 2020],
        )

    def test_bounds_may_be_years(self):
        self.assertEqual(
            self.years(backscrape_start="2020", backscrape_end=2020), [2020]
        )

    def test_no_bounds_run_from_the_first_year_to_this_year(self):
        years = self.years()
        self.assertEqual(years[0], mesuperct.Site.start_year)
        self.assertEqual(len(years), mesuperct.Site().current_year - 1999)
