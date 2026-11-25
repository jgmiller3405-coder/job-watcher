"""The financial analyst title rule."""

import pytest

from jobwatcher.roles import is_in_role


@pytest.mark.parametrize(
    "title",
    [
        "Financial Analyst",
        "Senior Financial Analyst, FP&A",
        "Finance Analyst",
        "Associate Financial Analyst",
        "Finance & Strategy Analyst",
        "Senior Analyst, Finance Business Partner",
        "Financial Reporting Analyst",
        "Senior Analyst - Corporate Finance",
        "FP&A Analyst",
        "Associate, FP&A Tech & Ops",
        "Associate, Financial Planning & Analysis - Private Markets",
        "Senior Analyst, Financial Planning and Analysis",
        "SENIOR FINANCIAL ANALYSTS",
    ],
)
def test_in_role(title):
    assert is_in_role(title)


@pytest.mark.parametrize(
    "title",
    [
        "Data Analyst",
        "Financial Advisor",
        "Financial Planning Consultant",
        "Finance Manager (FP&A)",
        "Senior Manager, Financial Planning and Analysis",
        "Vice President, Financial Planning & Analysis",
        "Associate Director, FP&A",
        "Financial Crimes Sanctions Analyst",
        "Financial Intelligence Analyst",
        "Prime Financial Services Client Services Analyst",
        "Investment Banking - Leveraged Finance - Analyst",
        "Senior Analyst - Structured Finance",
        "Senior Analyst - US Public Finance, Housing",
        "Asset Management - Financial Advisor Services - Analyst",
        "Sr. Systems Analyst, Finance, Enterprise Apps",
        "Software Engineer, Financial Analyst Tools",
        "Associate Analyst - Financials",
        "Financial Analysis Lead",
        "",
    ],
)
def test_not_in_role(title):
    assert not is_in_role(title)
