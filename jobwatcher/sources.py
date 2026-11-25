"""The watch list: one entry per employer job board.

``key`` names the raw file and prefixes every posting_id, so never change it once
data has been collected.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    key: str
    employer: str
    ats: str  # workday, greenhouse, ashby, lever, smartrecruiters, oracle
    board: str  # Workday site, board token, company ID, or Oracle site number
    host: str = ""  # Workday and Oracle only
    tenant: str = ""  # Workday only
    search: str = ""  # search term for boards with more than 5,000 postings


def _workday(key: str, employer: str, tenant: str, pod: int, site: str) -> Source:
    host = f"{tenant}.wd{pod}.myworkdayjobs.com"
    return Source(key, employer, "workday", site, host=host, tenant=tenant)


SOURCES: tuple[Source, ...] = (
    _workday("blackrock", "BlackRock", "blackrock", 1, "BlackRock_Professional"),
    _workday("fidelity", "Fidelity Investments", "fmr", 1, "FidelityCareers"),
    _workday("mastercard", "Mastercard", "mastercard", 1, "CorporateCareers"),
    _workday("morganstanley", "Morgan Stanley", "ms", 5, "External"),
    _workday("nasdaq", "Nasdaq", "nasdaq", 1, "Global_External_Site"),
    _workday("pnc", "PNC", "pnc", 5, "External"),
    _workday("spglobal", "S&P Global", "spgi", 5, "SPGI_Careers"),
    _workday("statestreet", "State Street", "statestreet", 1, "Global"),
    _workday("travelers", "Travelers", "travelers", 5, "External"),
    _workday("troweprice", "T. Rowe Price", "troweprice", 5, "TRowePrice"),
    _workday("truist", "Truist", "truist", 1, "Careers"),
    _workday("vanguard", "Vanguard", "vanguard", 5, "vanguard_external"),
    Source("affirm", "Affirm", "greenhouse", "affirm"),
    Source("coinbase", "Coinbase", "greenhouse", "coinbase"),
    Source("point72", "Point72", "greenhouse", "point72"),
    Source("robinhood", "Robinhood", "greenhouse", "robinhood"),
    Source("stripe", "Stripe", "greenhouse", "stripe"),
    Source("plaid", "Plaid", "ashby", "plaid"),
    Source("ramp", "Ramp", "ashby", "ramp"),
    Source("palantir", "Palantir", "lever", "palantir"),
    Source("experian", "Experian", "smartrecruiters", "Experian"),
    Source(
        "jpmorgan",
        "JPMorgan Chase",
        "oracle",
        "CX_1001",
        host="jpmc.fa.oraclecloud.com",
        search="analyst",
    ),
)

BY_KEY: dict[str, Source] = {source.key: source for source in SOURCES}
