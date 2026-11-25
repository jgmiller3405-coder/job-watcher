"""The watch list: one entry per employer job board.

``key`` names the raw file and prefixes every posting_id, so never change it once
data has been collected.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    key: str
    employer: str
    ats: str  # greenhouse, ashby, lever, smartrecruiters, or oracle
    board: str  # board token, company ID, or Oracle site number
    host: str = ""  # Oracle only
    search: str = ""  # search term for boards with more than 5,000 postings


def _oracle(key: str, employer: str, pod: str, site: str, search: str = "") -> Source:
    return Source(key, employer, "oracle", site, host=f"{pod}.oraclecloud.com", search=search)


SOURCES: tuple[Source, ...] = (
    _oracle("americanexpress", "American Express", "egug.fa.us2", "CX_1"),
    _oracle("bny", "BNY", "eofe.fa.us2", "CX_1001"),
    _oracle("citizens", "Citizens", "hcgn.fa.us2", "CX_1001"),
    _oracle("cummins", "Cummins", "fa-espx-saasfaprod1.fa.ocs", "CX_1"),
    _oracle("ford", "Ford", "efds.fa.em5", "CX_1"),
    _oracle("goldmansachs", "Goldman Sachs", "hdpc.fa.us2", "LateralHiring"),
    _oracle("honeywell", "Honeywell", "ibqbjb.fa.ocs", "CX_1"),
    _oracle("jpmorgan", "JPMorgan Chase", "jpmc.fa", "CX_1001", search="analyst"),
    _oracle("texasinstruments", "Texas Instruments", "edbz.fa.us2", "CX"),
    Source("affirm", "Affirm", "greenhouse", "affirm"),
    Source("coinbase", "Coinbase", "greenhouse", "coinbase"),
    Source("point72", "Point72", "greenhouse", "point72"),
    Source("robinhood", "Robinhood", "greenhouse", "robinhood"),
    Source("sofi", "SoFi", "greenhouse", "sofi"),
    Source("stripe", "Stripe", "greenhouse", "stripe"),
    Source("plaid", "Plaid", "ashby", "plaid"),
    Source("ramp", "Ramp", "ashby", "ramp"),
    Source("palantir", "Palantir", "lever", "palantir"),
    Source("abbvie", "AbbVie", "smartrecruiters", "AbbVie"),
    Source("experian", "Experian", "smartrecruiters", "Experian"),
    Source("nbcuniversal", "NBCUniversal", "smartrecruiters", "NBCUniversal3"),
    Source("servicenow", "ServiceNow", "smartrecruiters", "ServiceNow"),
)

BY_KEY: dict[str, Source] = {source.key: source for source in SOURCES}
