"""Recorded cut of the 2026 RecentOpinionsHTML.php card layout (Division 2).

Provenance: tests/examples/opinions/united_states/arizctapp_div_2_recent_cut.RECORDED.md
"""

from pathlib import Path

from lxml import html

from juriscraper.opinions.united_states.state import arizctapp_div_2

EXAMPLE = (
    Path(__file__).resolve().parents[1]
    / "examples/opinions/united_states/arizctapp_div_2_recent_cut.html"
)


def test_recent_cut_parses_one_card() -> None:
    site = arizctapp_div_2.Site()
    site.url = "https://www.appeals2.az.gov/RecentOpinionsHTML.php"
    site.html = html.fromstring(EXAMPLE.read_text(encoding="utf-8"))
    site._process_html()
    assert len(site.cases) == 1
    case = site.cases[0]
    assert case["docket"] == "2 CA-CR 2026-0088-PR"
    assert case["date"] == "10/26/2026"
    assert "McCutcheon" in case["name"]
    assert case["url"].endswith("CR20260088Opinion.pdf")
