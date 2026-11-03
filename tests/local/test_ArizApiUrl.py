"""The Arizona opinions API requires pageSize or it answers 404."""

from datetime import date

from juriscraper.opinions.united_states.state.ariz import Site
from juriscraper.opinions.united_states.state.arizctapp_div_1 import (
    Site as Div1,
)


def test_get_opinions_url_includes_the_page_size_the_page_sends():
    start = date(2026, 10, 3)
    end = date(2026, 11, 2)
    supreme = Site()._build_api_url(start, end)
    assert supreme.startswith(
        "https://www.azcourts.gov/API/Azcourts/Opinions/GetOpinions?"
    )
    assert "court=Supreme" in supreme
    assert "pageSize=10" in supreme
    division = Div1()._build_api_url(start, end, page=1)
    assert division.startswith(
        "https://coa1.azcourts.gov/API/Azcourts/Opinions/GetOpinions?"
    )
    assert "court=Division1" in division
    assert "page=1" in division
    assert "pageSize=10" in division
