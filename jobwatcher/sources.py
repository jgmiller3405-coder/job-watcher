"""The watch list: one entry per employer job board.

``key`` names the raw file and prefixes every posting_id, so never change it once
data has been collected.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    key: str
    employer: str
    ats: str  # a key of fetch.FETCHERS
    board: str = ""  # board token, company ID, site name or number, or board path
    host: str = ""  # Oracle, Workday, iCIMS, Phenom, and UKG only
    tenant: str = ""  # Workday only
    search: str = ""  # search term for boards with more than 5,000 postings


def _oracle(key: str, employer: str, pod: str, site: str, search: str = "") -> Source:
    return Source(key, employer, "oracle", site, host=f"{pod}.oraclecloud.com", search=search)


def _workday(key: str, employer: str, tenant: str, pod: int, site: str) -> Source:
    host = f"{tenant}.wd{pod}.myworkdayjobs.com"
    return Source(key, employer, "workday", site, host=host, tenant=tenant)


def _icims(key: str, employer: str, host: str, search: str = "") -> Source:
    return Source(key, employer, "icims", host=host, search=search)


def _phenom(key: str, employer: str, host: str) -> Source:
    return Source(key, employer, "phenom", host=host)


def _ukg(key: str, employer: str, board: str) -> Source:
    return Source(key, employer, "ukg", board, host="recruiting2.ultipro.com")


SOURCES: tuple[Source, ...] = (
    # Northwest Arkansas
    _workday("jbhunt", "J.B. Hunt", "jbhunt", 501, "Careers"),
    _ukg("carmart", "America's Car-Mart", "AME1031ACM/JobBoard/9a085139-ceb8-4e6a-a651-272c1c59be0c"),
    # Kansas City
    _icims("garmin", "Garmin", "careers.garmin.com"),
    _icims("hrblock", "H&R Block", "careers.hrblock.com", search="analyst"),
    _ukg("hallmark", "Hallmark", "HAL1009HLLI/JobBoard/1af38e50-bef2-48c7-8919-d646ae0bee65"),
    _phenom("commercebank", "Commerce Bank", "careers.commercebank.com"),
    _oracle("oracle", "Oracle", "eeho.fa.us2", "CX_45001"),
    # Chicago
    _phenom("abbott", "Abbott", "www.jobs.abbott"),
    Source("abbvie", "AbbVie", "smartrecruiters", "AbbVie"),
    _phenom("conagra", "Conagra Brands", "careers.conagrabrands.com"),
    _phenom("united", "United Airlines", "careers.united.com"),
    _icims("exelon", "Exelon", "jobs.exeloncorp.com"),
    _icims("ulta", "Ulta Beauty", "careers.ulta.com", search="analyst"),
    Source("drw", "DRW", "greenhouse", "drweng"),
    Source("imc", "IMC Trading", "greenhouse", "imc"),
    Source("jumptrading", "Jump Trading", "greenhouse", "jumptrading"),
    Source("williamblair", "William Blair", "greenhouse", "williamblair"),
    # Dallas-Fort Worth
    _oracle("texasinstruments", "Texas Instruments", "edbz.fa.us2", "CX"),
    _oracle("tenet", "Tenet Healthcare", "eodr.fa.us2", "CX_1001"),
    _icims("pepsico", "PepsiCo", "www.pepsicojobs.com"),
    _phenom("southwest", "Southwest Airlines", "careers.southwestair.com"),
    _phenom("toyota", "Toyota North America", "careers.toyota.com"),
    Source("matchgroup", "Match Group", "lever", "matchgroup"),
    # New York
    _oracle("americanexpress", "American Express", "egug.fa.us2", "CX_1"),
    _oracle("bny", "BNY", "eofe.fa.us2", "CX_1001"),
    _oracle("goldmansachs", "Goldman Sachs", "hdpc.fa.us2", "LateralHiring"),
    _oracle("jpmorgan", "JPMorgan Chase", "jpmc.fa", "CX_1001", search="analyst"),
    Source("nbcuniversal", "NBCUniversal", "smartrecruiters", "NBCUniversal3"),
    Source("datadog", "Datadog", "greenhouse", "datadog"),
    Source("janestreet", "Jane Street", "greenhouse", "janestreet"),
    Source("mongodb", "MongoDB", "greenhouse", "mongodb"),
    Source("nytimes", "The New York Times", "greenhouse", "thenewyorktimes"),
    Source("oscar", "Oscar Health", "greenhouse", "oscar"),
    Source("spotify", "Spotify", "lever", "spotify"),
    # Other employers on the list
    _oracle("citizens", "Citizens", "hcgn.fa.us2", "CX_1001"),
    _oracle("cummins", "Cummins", "fa-espx-saasfaprod1.fa.ocs", "CX_1"),
    _oracle("ford", "Ford", "efds.fa.em5", "CX_1"),
    _oracle("honeywell", "Honeywell", "ibqbjb.fa.ocs", "CX_1"),
    Source("affirm", "Affirm", "greenhouse", "affirm"),
    Source("coinbase", "Coinbase", "greenhouse", "coinbase"),
    Source("point72", "Point72", "greenhouse", "point72"),
    Source("robinhood", "Robinhood", "greenhouse", "robinhood"),
    Source("sofi", "SoFi", "greenhouse", "sofi"),
    Source("stripe", "Stripe", "greenhouse", "stripe"),
    Source("plaid", "Plaid", "ashby", "plaid"),
    Source("ramp", "Ramp", "ashby", "ramp"),
    Source("palantir", "Palantir", "lever", "palantir"),
    Source("experian", "Experian", "smartrecruiters", "Experian"),
    Source("servicenow", "ServiceNow", "smartrecruiters", "ServiceNow"),
)

BY_KEY: dict[str, Source] = {source.key: source for source in SOURCES}
