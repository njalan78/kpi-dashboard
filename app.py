# app.py (CLEAN VERSION)
# Streamlit KPI Measurement Tool — SKIMS (Germany + Spain)
# Run: streamlit run app.py

from __future__ import annotations
from dataclasses import dataclass
import math
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


DEFAULTS = {
    "paid_sessions": 200_000,
    "aov_eur": 85.0,
    "contribution_margin": 0.65,
    "campaign_cost_eur": 400_000.0,
}

# Only useful KPIs (not cluttered)
KPI_META = [
    {"kpi": "Reach_3plus", "type": "Formative", "baseline": None, "target": 0.45, "definition": "% exposed ≥3 times"},
    {"kpi": "CTR", "type": "Formative", "baseline": None, "target": 0.015, "definition": "Clicks / impressions"},
    {"kpi": "PDP_reach_rate", "type": "Formative", "baseline": None, "target": 0.55, "definition": "% sessions reaching PDP"},
    {"kpi": "CVR", "type": "Formative", "baseline": None, "target": 0.035, "definition": "Purchases / sessions"},
    {"kpi": "Email_revenue_share", "type": "Formative", "baseline": 0.18, "target": 0.25, "definition": "Email revenue / total revenue"},

    {"kpi": "Repeat_purchase_rate_90d", "type": "Summative", "baseline": 0.28, "target": 0.32, "definition": "% repeat within 90 days"},
    {"kpi": "Time_to_2nd_purchase_days", "type": "Summative", "baseline": 75, "target": 60, "definition": "Avg days to 2nd purchase"},
    {"kpi": "LTV_6mo_eur", "type": "Summative", "baseline": 120.0, "target": 132.0, "definition": "Avg 6-month revenue per customer"},
    {"kpi": "Marketing_ROMI", "type": "Summative", "baseline": None, "target": 1.8, "definition": "(Incremental profit - cost) / cost"},
]


@dataclass
class Scenario:
    name: str
    reach_3plus: float
    ctr: float
    pdp_reach_rate: float
    cvr: float
    email_rev_share: float
    repeat_rate_90d: float
    time_to_2nd_purchase_days: float
    ltv_6mo_eur: float


def business_outputs(paid_sessions: float, aov: float, margin: float, baseline: Scenario, actual: Scenario):
    def calc(s: Scenario):
        new_customers = paid_sessions * s.cvr
        second_orders = new_customers * s.repeat_rate_90d
        revenue = (new_customers + second_orders) * aov
        profit = revenue * margin
        email_revenue = revenue * s.email_rev_share
        return new_customers, second_orders, revenue, profit, email_revenue

    b = calc(baseline)
    a = calc(actual)

    return {
        "baseline_new_customers": b[0],
        "baseline_second_orders": b[1],
        "baseline_revenue": b[2],
        "baseline_profit": b[3],
        "baseline_email_revenue": b[4],
        "actual_new_customers": a[0],
        "actual_second_orders": a[1],
        "actual_revenue": a[2],
        "actual_profit": a[3],
        "actual_email_revenue": a[4],
    }


def calc_romi(baseline_profit: float, actual_profit: float, campaign_cost: float) -> float:
    inc_profit = actual_profit - baseline_profit
    if campaign_cost == 0:
        return float("nan")
    return (inc_profit - campaign_cost) / campaign_cost


def bar_chart(title: str, labels, values, y_label: str, target_line=None):
    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel(y_label)
    ax.set_ylim(bottom=0)
    if target_line is not None and not math.isnan(float(target_line)):
        ax.axhline(target_line, linestyle="--")
    st.pyplot(fig, clear_figure=True)


st.set_page_config(page_title="SKIMS KPI Tool", layout="wide")
st.title("SKIMS — KPI Measurement Tool (Clean Version)")
st.caption("Only the KPIs that matter for ex-ante/ex-post measurement + ROMI (no clutter).")

with st.sidebar:
    st.header("Business Assumptions")
    paid_sessions = st.number_input("Paid sessions", min_value=0, value=DEFAULTS["paid_sessions"], step=10_000)
    aov_eur = st.number_input("AOV (€)", min_value=0.0, value=float(DEFAULTS["aov_eur"]), step=1.0)
    margin = st.number_input("Contribution margin (0–1)", 0.0, 1.0, float(DEFAULTS["contribution_margin"]), 0.01)
    campaign_cost = st.number_input("Campaign cost (€)", min_value=0.0, value=float(DEFAULTS["campaign_cost_eur"]), step=10_000.0)

st.subheader("1) Baseline • Target • Actual inputs")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### Baseline")
    b = Scenario(
        "Baseline",
        reach_3plus=st.number_input("Reach 3+", 0.0, 1.0, 0.40, 0.01, key="b_reach"),
        ctr=st.number_input("CTR", 0.0, 1.0, 0.012, 0.001, key="b_ctr"),
        pdp_reach_rate=st.number_input("PDP reach rate", 0.0, 1.0, 0.50, 0.01, key="b_pdp"),
        cvr=st.number_input("CVR", 0.0, 1.0, 0.035, 0.001, key="b_cvr"),
        email_rev_share=st.number_input("Email rev share", 0.0, 1.0, 0.18, 0.01, key="b_email"),
        repeat_rate_90d=st.number_input("Repeat rate 90d", 0.0, 1.0, 0.28, 0.01, key="b_repeat"),
        time_to_2nd_purchase_days=st.number_input("Time to 2nd (days)", 0.0, 365.0, 75.0, 1.0, key="b_time2"),
        ltv_6mo_eur=st.number_input("LTV 6mo (€)", 0.0, 10000.0, 120.0, 1.0, key="b_ltv"),
    )

with c2:
    st.markdown("### Target (Ex-Ante)")
    t = Scenario(
        "Target",
        reach_3plus=st.number_input("Reach 3+ (target)", 0.0, 1.0, 0.45, 0.01, key="t_reach"),
        ctr=st.number_input("CTR (target)", 0.0, 1.0, 0.015, 0.001, key="t_ctr"),
        pdp_reach_rate=st.number_input("PDP reach rate (target)", 0.0, 1.0, 0.55, 0.01, key="t_pdp"),
        cvr=st.number_input("CVR (target)", 0.0, 1.0, 0.035, 0.001, key="t_cvr"),
        email_rev_share=st.number_input("Email rev share (target)", 0.0, 1.0, 0.25, 0.01, key="t_email"),
        repeat_rate_90d=st.number_input("Repeat rate 90d (target)", 0.0, 1.0, 0.32, 0.01, key="t_repeat"),
        time_to_2nd_purchase_days=st.number_input("Time to 2nd (target)", 0.0, 365.0, 60.0, 1.0, key="t_time2"),
        ltv_6mo_eur=st.number_input("LTV 6mo (target)", 0.0, 10000.0, 132.0, 1.0, key="t_ltv"),
    )

with c3:
    st.markdown("### Actual (Ex-Post)")
    a = Scenario(
        "Actual",
        reach_3plus=st.number_input("Reach 3+ (actual)", 0.0, 1.0, 0.44, 0.01, key="a_reach"),
        ctr=st.number_input("CTR (actual)", 0.0, 1.0, 0.016, 0.001, key="a_ctr"),
        pdp_reach_rate=st.number_input("PDP reach rate (actual)", 0.0, 1.0, 0.55, 0.01, key="a_pdp"),
        cvr=st.number_input("CVR (actual)", 0.0, 1.0, 0.034, 0.001, key="a_cvr"),
        email_rev_share=st.number_input("Email rev share (actual)", 0.0, 1.0, 0.29, 0.01, key="a_email"),
        repeat_rate_90d=st.number_input("Repeat rate 90d (actual)", 0.0, 1.0, 0.32, 0.01, key="a_repeat"),
        time_to_2nd_purchase_days=st.number_input("Time to 2nd (actual)", 0.0, 365.0, 65.0, 1.0, key="a_time2"),
        ltv_6mo_eur=st.number_input("LTV 6mo (actual)", 0.0, 10000.0, 130.0, 1.0, key="a_ltv"),
    )

st.subheader("2) KPI Target Table (Ex-Ante)")
ex_ante = pd.DataFrame([{
    "KPI": k["kpi"],
    "Type": k["type"],
    "Baseline": k["baseline"],
    "Target": k["target"],
    "Definition": k["definition"],
    "Justification": "",
} for k in KPI_META if k["kpi"] != "Marketing_ROMI"])
st.dataframe(ex_ante, use_container_width=True)

st.subheader("3) Business Outputs + ROMI (Baseline vs Actual)")
biz = business_outputs(paid_sessions, aov_eur, margin, b, a)
romi_actual = calc_romi(biz["baseline_profit"], biz["actual_profit"], campaign_cost)

summary = pd.DataFrame([
    {"Metric": "New customers", "Baseline": biz["baseline_new_customers"], "Actual": biz["actual_new_customers"]},
    {"Metric": "Second orders", "Baseline": biz["baseline_second_orders"], "Actual": biz["actual_second_orders"]},
    {"Metric": "Revenue (€)", "Baseline": biz["baseline_revenue"], "Actual": biz["actual_revenue"]},
    {"Metric": "Profit (€)", "Baseline": biz["baseline_profit"], "Actual": biz["actual_profit"]},
    {"Metric": "Email revenue (€)", "Baseline": biz["baseline_email_revenue"], "Actual": biz["actual_email_revenue"]},
    {"Metric": "ROMI", "Baseline": None, "Actual": romi_actual},
])
st.dataframe(summary, use_container_width=True)

st.subheader("4) Ex-Post Evaluation (Target vs Actual)")
eval_df = pd.DataFrame([
    {"KPI": "Reach_3plus", "Target": t.reach_3plus, "Actual": a.reach_3plus, "Gap_(+good)": a.reach_3plus - t.reach_3plus},
    {"KPI": "CTR", "Target": t.ctr, "Actual": a.ctr, "Gap_(+good)": a.ctr - t.ctr},
    {"KPI": "PDP_reach_rate", "Target": t.pdp_reach_rate, "Actual": a.pdp_reach_rate, "Gap_(+good)": a.pdp_reach_rate - t.pdp_reach_rate},
    {"KPI": "CVR", "Target": t.cvr, "Actual": a.cvr, "Gap_(+good)": a.cvr - t.cvr},
    {"KPI": "Email_revenue_share", "Target": t.email_rev_share, "Actual": a.email_rev_share, "Gap_(+good)": a.email_rev_share - t.email_rev_share},
    {"KPI": "Repeat_purchase_rate_90d", "Target": t.repeat_rate_90d, "Actual": a.repeat_rate_90d, "Gap_(+good)": a.repeat_rate_90d - t.repeat_rate_90d},
    {"KPI": "Time_to_2nd_purchase_days", "Target": t.time_to_2nd_purchase_days, "Actual": a.time_to_2nd_purchase_days, "Gap_(+good)": t.time_to_2nd_purchase_days - a.time_to_2nd_purchase_days},
    {"KPI": "LTV_6mo_eur", "Target": t.ltv_6mo_eur, "Actual": a.ltv_6mo_eur, "Gap_(+good)": a.ltv_6mo_eur - t.ltv_6mo_eur},
    {"KPI": "Marketing_ROMI", "Target": 1.8, "Actual": romi_actual, "Gap_(+good)": romi_actual - 1.8},
])
st.dataframe(eval_df, use_container_width=True)

st.subheader("5) Charts (clean + meaningful)")
g1, g2 = st.columns(2)
with g1:
    bar_chart("6-month LTV (€)", ["Baseline", "Target", "Actual"], [b.ltv_6mo_eur, t.ltv_6mo_eur, a.ltv_6mo_eur], "€", target_line=t.ltv_6mo_eur)
with g2:
    bar_chart("Marketing ROMI", ["Target", "Actual"], [1.8, romi_actual], "ROMI", target_line=1.8)
