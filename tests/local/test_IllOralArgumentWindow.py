#!/usr/bin/env python


import unittest
from datetime import datetime

from juriscraper.oral_args.united_states.state import (
    ill,
    illappct_1st_dist,
    illappct_3rd_dist,
    illappct_workers_comp,
)

# Supreme Court arguments: 2026-05-20, then none until 2026-09-15 (118 days).
# On 2026-11-05 the 30-day form returned "No listings were found" for the
# supreme court, the third district, and workers' compensation.
MIN_WINDOW_DAYS = 150
MAX_WINDOW_DAYS = 200

_SITES = (
    ill,
    illappct_1st_dist,
    illappct_3rd_dist,
    illappct_workers_comp,
)


def _window_days(site):
    parameters = site.parameters
    start = datetime.strptime(
        parameters["ctl00$ctl04$txtFilterDateFrom"], "%m/%d/%Y"
    ).date()
    end = datetime.strptime(
        parameters["ctl00$ctl04$txtFilterDateTo"], "%m/%d/%Y"
    ).date()
    return (end - start).days


class IllOralArgumentWindowTest(unittest.TestCase):
    def test_request_covers_a_term_gap(self):
        short = []
        for module in _SITES:
            span = _window_days(module.Site())
            if span < MIN_WINDOW_DAYS or span > MAX_WINDOW_DAYS:
                short.append(f"{module.__name__} asks for {span} days")
        self.assertEqual(short, [])
