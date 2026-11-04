# Scraper for Texas 14th Court of Appeals
# CourtID: txctapp14
# Court Short Name: TX
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-10


from juriscraper.opinions.united_states.state import texapp


class Site(texapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "capp_14"
        self.court_number = "14"
        self.checkbox = 15
        self.coa_code = "coa14"
        self.url = (
            "https://search.txcourts.gov/DocketSrch.aspx?coa=" + self.coa_code
        )
