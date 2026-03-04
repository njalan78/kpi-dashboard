# app.py
# Streamlit KPI Measurement Dashboard for SKIMS (Germany + Spain)

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, List
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -----------------------------
# Config / Defaults
# -----------------------------
DEFAULTS = {
    "paid_sessions": 200_000,
    "aov_eur": 85.0,
    "contribution_margin": 0.65,
    "campaign_cost_eur": 400_000.0,
}

KPI_META = [
    {"kpi": "Reach_3plus", "type": "Formative", "baseline": None, "target": 0.45, "unit": "ratio",
     "definition": "% of target audience exposed ≥3 times"},
    {"kpi": "CTR", "type": "Formative", "baseline": None, "target": 0.015, "unit": "ratio",
     "definition": "Clicks / impressions"},
    {"kpi": "PDP_reach_rate", "type": "Formative", "baseline": None, "target": 0.60, "unit": "ratio",
     "definition": "% sessions reaching Seamless Sculpt PDP"},
    {"kpi": "CVR", "type": "Formative", "baseline": None, "target": 0.035, "unit": "ratio",
     "definition": "Purchases / sessions"},
    {"kpi": "Email_revenue_share", "type": "Formative", "baseline": None, "target": 0.25, "unit": "ratio",
     "definition": "Email/SMS revenue / total revenue"},
    {"kpi": "Marketing_ROMI", "type": "Formative", "baseline": None, "target": 1.8, "unit": "ratio",
     "definition": "(Incremental profit - cost) / cost"},
    {"kpi": "Repeat_purchase_rate_90d", "type": "Summative", "baseline": 0.28, "target": 0.35, "unit": "ratio",
     "definition": "% new customers purchasing again within 90 days"},
    {"kpi": "Time_to_2nd_purchase_days", "type": "Summative", "baseline": 75, "target": 55, "unit": "days",
     "definition": "Avg days from 1st to 2nd purchase"},
    {"kpi": "LTV_6mo_eur", "type": "Summative", "baseline": 120.0, "target": 144.0, "unit": "eur",
     "definition": "Avg revenue per customer within 6 months"},
]

@dataclass
class Scenario:
    name: str
    cvr: float
    repeat_rate_90d: float
    email_rev_share: float
    reach_3plus: float
    ctr: float
    pdp_reach_rate: float
    time_to_2nd_purchase_days: float
    ltv_6mo_eur: float


def calc_business_outputs(
    paid_sessions: float,
    aov_eur: float,
    margin: float,
    campaign_cost_eur: float,
    baseline: Scenario,
    actual: Scenario,
) -> Dict[str, float]:

    def scenario_outputs(s: Scenario) -> Dict[str, float]:
        new_customers = paid_sessions * s.cvr
        second_orders = new_customers * s.repeat_rate_90d
        revenue = (new_customers + second_orders) * aov_eur
        profit = revenue * margin
        email_revenue = revenue * s.email_rev_share
        return {
            "new_customers": new_customers,
            "second_orders": second_orders,
            "revenue_eur": revenue,
            "profit_eur": profit,
            "email_revenue_eur": email_revenue,
        }

    base_out = scenario_outputs(baseline)
    act_out = scenario_outputs(actual)

    incremental_profit = act_out["profit_eur"] - base_out["profit_eur"]

    romi = (
        (incremental_profit - campaign_cost_eur) / campaign_cost_eur
        if campaign_cost_eur != 0
        else math.nan
    )

    return {
        **{f"baseline_{k}": v for k, v in base_out.items()},
        **{f"actual_{k}": v for k, v in act_out.items()},
        "incremental_profit_eur": incremental_profit,
        "romi": romi,
    }


def build_ex_ante_table() -> pd.DataFrame:
    rows = []
    for item in KPI_META:
        if any(r["KPI"] == item["kpi"] for r in rows):
            continue
        rows.append({
            "KPI": item["kpi"],
            "Type": item["type"],
            "Definition": item["definition"],
            "Baseline": item["baseline"],
            "Target": item["target"],
            "Justification": "",
        })
    return pd.DataFrame(rows)


def evaluate_kpis(target: Scenario, actual: Scenario, romi_actual: float) -> pd.DataFrame:

    mapping = {
        "Reach_3plus": (target.reach_3plus, actual.reach_3plus, "higher"),
        "CTR": (target.ctr, actual.ctr, "higher"),
        "PDP_reach_rate": (target.pdp_reach_rate, actual.pdp_reach_rate, "higher"),
        "CVR": (target.cvr, actual.cvr, "higher"),
        "Email_revenue_share": (target.email_rev_share, actual.email_rev_share, "higher"),
        "Repeat_purchase_rate_90d": (target.repeat_rate_90d, actual.repeat_rate_90d, "higher"),
        "Time_to_2nd_purchase_days": (target.time_to_2nd_purchase_days, actual.time_to_2nd_purchase_days, "lower"),
        "LTV_6mo_eur": (target.ltv_6mo_eur, actual.ltv_6mo_eur, "higher"),
        "Marketing_ROMI": (1.8, romi_actual, "higher"),
    }

    rows = []

    for kpi, (t, a, direction) in mapping.items():
        if direction == "higher":
            gap = a - t
        else:
            gap = t - a

        rows.append({
            "KPI": kpi,
            "Target": t,
            "Actual": a,
            "Gap_(+good)": gap,
            "Interpretation": "",
            "Decision": "",
        })

    return pd.DataFrame(rows)


def make_recommendations(actual: Scenario, romi: float) -> List[str]:
    recs = []

    if actual.repeat_rate_90d < 0.35:
        recs.append("Improve post-purchase CRM to increase repeat rate.")
    if actual.time_to_2nd_purchase_days > 55:
        recs.append("Accelerate repeat purchases with bundles and reminder flows.")
    if actual.ltv_6mo_eur < 144:
        recs.append("Improve cross-sell and personalization to lift LTV.")
    if actual.email_rev_share < 0.25:
        recs.append("Strengthen email automation and segmentation.")
    if actual.cvr < 0.035:
        recs.append("Optimize PDP and checkout to improve conversion.")
    if romi < 1.8:
        recs.append("Reallocate budget to higher ROAS channels.")

    if not recs:
        recs.append("All KPIs on track. Scale what works.")

    return recs


def bar_chart(title: str, labels: List[str], values: List[float], y_label: str):
    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel(y_label)
    st.pyplot(fig)


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="SKIMS KPI Measurement Tool", layout="wide")
st.title("SKIMS KPI Measurement Tool")

with st.sidebar:
    paid_sessions = st.number_input("Paid sessions", value=DEFAULTS["paid_sessions"])
    aov_eur = st.number_input("AOV (€)", value=DEFAULTS["aov_eur"])
    margin = st.number_input("Contribution margin", value=DEFAULTS["contribution_margin"])
    campaign_cost = st.number_input("Campaign cost (€)", value=DEFAULTS["campaign_cost_eur"])


st.subheader("Scenario Inputs")

cvr = st.number_input("CVR", value=0.034)
repeat_rate = st.number_input("Repeat rate (90d)", value=0.32)
email_share = st.number_input("Email revenue share", value=0.29)

actual = Scenario(
    name="Actual",
    cvr=cvr,
    repeat_rate_90d=repeat_rate,
    email_rev_share=email_share,
    reach_3plus=0.44,
    ctr=0.016,
    pdp_reach_rate=0.62,
    time_to_2nd_purchase_days=58,
    ltv_6mo_eur=138,
)

baseline = actual  # simple placeholder baseline

biz = calc_business_outputs(
    paid_sessions,
    aov_eur,
    margin,
    campaign_cost,
    baseline,
    actual,
)

st.subheader("Business Output Summary")
st.write(biz)

st.subheader("Recommendations")
for r in make_recommendations(actual, biz["romi"]):
    st.write("- " + r)

bar_chart(
    "6-month LTV",
    ["Actual"],
    [actual.ltv_6mo_eur],
    "€"
)
