"""The Arizona opinions API requires pageSize or it answers 404."""

from datetime import date
from urllib.parse import parse_qs, urlsplit

from juriscraper.opinions.united_states.state.ariz import Site
from juriscraper.opinions.united_states.state.arizctapp_div_1 import (
    Site as Div1,
)


def _query(url: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(url).query)


def test_get_opinions_url_includes_the_page_size_the_page_sends():
    start = date(2026, 10, 3)
    end = date(2026, 11, 2)
    supreme = Site()._build_api_url(start, end)
    assert supreme.startswith(
        "https://www.azcourts.gov/API/Azcourts/Opinions/GetOpinions?"
    )
    supreme_query = _query(supreme)
    assert supreme_query["court"] == ["Supreme"]
    assert supreme_query["pageSize"] == ["10"]
    division = Div1()._build_api_url(start, end, page=1)
    assert division.startswith(
        "https://coa1.azcourts.gov/API/Azcourts/Opinions/GetOpinions?"
    )
    division_query = _query(division)
    assert division_query["court"] == ["Division1"]
    assert division_query["page"] == ["1"]
    assert division_query["pageSize"] == ["10"]
