"""The title rule for the watched role: financial analyst.

A title is in the role when it names an analyst job in finance:

1. It is not an investment banking, engineering, developer, or systems job.
2. If it says "FP&A" or "financial planning and analysis", it also says
   "analyst", or says "associate" without "director", "manager", or
   "vice president".
3. Otherwise it says "analyst" and also "finance" or "financial". That word does
   not count inside "financial crime(s)", "financial intelligence", "financial
   services", "financial institutions", "financial sponsors", "financial
   advisor", or leveraged, structured, public, project, trade, vendor, or
   investment grade finance.
"""

import re

NOT_ROLE = re.compile(r"\b(investment banking|engineer|engineering|developer|systems?)\b")
FPA = re.compile(r"\bfp ?(&|and) ?a\b|\bfinancial planning (&|and) analysis\b")
ANALYST = re.compile(r"\banalysts?\b")
ASSOCIATE = re.compile(r"\bassociate\b")
SENIOR_LEVEL = re.compile(r"\b(director|manager|vice president|vp|avp)\b")
FINANCE = re.compile(r"\b(finance|financial)\b")
OTHER_FIELD = re.compile(
    r"\bfinancial (crimes?|intelligence|services?|institutions?|sponsors?|advisors?)\b"
    r"|\b(leveraged|structured|public|project|trade|vendor|investment grade) finance\b"
)


def is_in_role(title: str) -> bool:
    text = " ".join(title.lower().split())
    if NOT_ROLE.search(text):
        return False
    if FPA.search(text):
        if ANALYST.search(FPA.sub(" ", text)):
            return True
        return bool(ASSOCIATE.search(text)) and not SENIOR_LEVEL.search(text)
    if not ANALYST.search(text):
        return False
    return bool(FINANCE.search(OTHER_FIELD.sub(" ", text)))
