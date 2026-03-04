# app.py
# Streamlit KPI Measurement Dashboard for SKIMS (Germany + Spain)
# Run locally: streamlit run app.py
# Deploy (Streamlit Cloud): add requirements.txt (streamlit, pandas, matplotlib)

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


# -----------------------------
# Defaults (edit anytime)
# -----------------------------
DEFAULTS = {
    "paid_sessions": 200_000,
    "aov_eur": 85.0,
    "contribution_margin": 0.65,
    "campaign_cost_eur": 400_000.0,
}

# KPI Dictionary (Formative + Summative) + your new targets/results
# Notes from your Canva:
# Formative Ex-Ante Targets: Reach 0.45, CTR 0.015, PDP reach 0.55, CVR 0.035, Email rev share 0.25, ROMI >= 1.8
# Summative: Repeat baseline 28% target 32% result 32%; LTV baseline 120 target 132 result 130; ROMI target 1.8 result 1.6; Time to 2nd baseline 75 target 60 (result not shown -> we set a default you can edit)
KPI_META = [
    # FORMATIVE
    {"kpi": "Reach_3plus", "type": "Formative", "baseline": None, "target": 0.45, "unit": "ratio",
     "definition": "% of target audience exposed ≥3 times"},
    {"kpi": "CTR", "type": "Formative", "baseline": None, "target": 0.015, "unit": "ratio",
     "definition": "Click-through rate (clicks / impressions)"},
    {"kpi": "PDP_reach_rate", "type": "Formative", "baseline": None, "target": 0.55, "unit": "ratio",
     "definition": "% sessions reaching Seamless Sculpt PDP"},
    {"kpi": "CVR", "type": "Formative", "baseline": None, "target": 0.035, "unit": "ratio",
     "definition": "Conversion rate (purchases / sessions)"},
    {"kpi": "Email_revenue_share", "type": "Formative", "baseline": 0.18, "target": 0.25, "unit": "ratio",
     "definition": "Email/SMS revenue / total revenue"},
    {"kpi": "Marketing_ROMI", "type": "Formative", "baseline": None, "target": 1.8, "unit": "ratio",
     "definition": "(Incremental profit - cost) / cost"},

    # COMMUNICATION (you mentioned earlier)
    {"kpi": "Worth_the_price", "type": "Formative", "baseline": 0.52, "target": 0.58, "unit": "ratio",
     "definition": "% agreeing Seamless Sculpt is worth the price"},
    {"kpi": "Best_shaping_association", "type": "Formative", "baseline": 0.48, "target": 0.53, "unit": "ratio",
     "definition": "% associating SKIMS with best shaping performance"},
    {"kpi": "CSAT", "type": "Summative", "baseline": 0.78, "target": 0.85, "unit": "ratio",
     "definition": "Post-purchase satisfaction score"},

    # SUMMATIVE (business outcomes)
    {"kpi": "Repeat_purchase_rate_90d", "type": "Summative", "baseline": 0.28, "target": 0.32, "unit": "ratio",
     "definition": "% new customers purchasing again within 90 days"},
    {"kpi": "Time_to_2nd_purchase_days", "type": "Summative", "baseline": 75, "target": 60, "unit": "days",
     "definition": "Avg days from 1st to 2nd purchase"},
    {"kpi": "LTV_6mo_eur", "type": "Summative", "baseline": 120.0, "target": 132.0, "unit": "eur",
     "definition": "Avg revenue per customer within 6 months"},
    {"kpi": "Marketing_ROMI", "type": "Summative", "baseline": None, "target": 1.8, "unit": "ratio",
     "definition": "(Incremental profit - cost) / cost"},
]


@dataclass
class Scenario:
    name: str

    # Core business drivers
    cvr: float
    repeat_rate_90d: float
    email_rev_share: float

    # Funnel / media
    reach_3plus: float
    ctr: float
    pdp_reach_rate: float

    # Outcomes
    time_to_2nd_purchase_days: float
    ltv_6mo_eur: float

    # Communication / experience
    worth_the_price: float
    best_shaping_association: float
    csat: float


def calc_business_outputs(
    paid_sessions: float,
    aov_eur: float,
    margin: float,
    campaign_cost_eur: float,
    baseline: Scenario,
    actual: Scenario,
) -> Dict[str, float]:
    """
    Required business model:
    new_customers = paid_sessions * CVR
    second_orders = new_customers * repeat_purchase_rate_90d
    revenue = (new_customers + second_orders) * aov
    profit = revenue * margin
    incremental_profit = profit_actual - profit_baseline
    ROMI = (incremental_profit - campaign_cost) / campaign_cost
    """

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
    romi = (incremental_profit - campaign_cost_eur) / campaign_cost_eur if campaign_cost_eur != 0 else math.nan

    return {
        **{f"baseline_{k}": v for k, v in base_out.items()},
        **{f"actual_{k}": v for k, v in act_out.items()},
        "incremental_profit_eur": incremental_profit,
        "romi": romi,
    }


def build_ex_ante_table() -> pd.DataFrame:
    rows = []
    seen = set()
    for item in KPI_META:
        if item["kpi"] in seen:
            continue
        seen.add(item["kpi"])
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

        "Worth_the_price": (target.worth_the_price, actual.worth_the_price, "higher"),
        "Best_shaping_association": (target.best_shaping_association, actual.best_shaping_association, "higher"),
        "CSAT": (target.csat, actual.csat, "higher"),

        "Repeat_purchase_rate_90d": (target.repeat_rate_90d, actual.repeat_rate_90d, "higher"),
        "Time_to_2nd_purchase_days": (target.time_to_2nd_purchase_days, actual.time_to_2nd_purchase_days, "lower"),
        "LTV_6mo_eur": (target.ltv_6mo_eur, actual.ltv_6mo_eur, "higher"),
        "Marketing_ROMI": (1.8, romi_actual, "higher"),
    }

    def gap_calc(t, a, direction: str):
        if t is None or a is None:
            return None
        # Gap_(+good): always positive = good
        if direction == "higher":
            return a - t
        return t - a  # lower is better

    rows = []
    for kpi, (t, a, direction) in mapping.items():
        rows.append({
            "KPI": kpi,
            "Target": t,
            "Actual": a,
            "Gap_(+good)": gap_calc(t, a, direction),
            "Interpretation": "",
            "Decision": "",
        })
    return pd.DataFrame(rows)


def make_recommendations(actual: Scenario, romi: float) -> List[str]:
    recs: List[str] = []

    # Business outcomes
    if actual.repeat_rate_90d < 0.32:
        recs.append("Repeat purchase rate below target → strengthen post-purchase CRM (education, sizing/fit, replenishment reminders).")
    if actual.time_to_2nd_purchase_days > 60:
        recs.append("Time to 2nd purchase above target → add reminder sequence + bundles + limited-time offers to accelerate repeat.")
    if actual.ltv_6mo_eur < 132:
        recs.append("6-month LTV below target → improve cross-sell personalization (bundles, best-seller combos) + test offers.")
    if actual.email_rev_share < 0.25:
        recs.append("Email revenue share below target → improve segmentation + automate journeys (welcome, post-purchase, win-back).")
    if actual.cvr < 0.035:
        recs.append("CVR below target → optimize PDP/checkout (fit guidance, trust signals, shipping/returns clarity).")
    if romi < 1.8:
        recs.append("ROMI below target → reallocate spend away from low-performing ads; shift budget to highest ROAS/retention drivers.")

    # Communication / experience
    if actual.worth_the_price < 0.58:
        recs.append("Worth-the-price perception below target → strengthen value proof (durability, cost-per-wear, testimonials).")
    if actual.best_shaping_association < 0.53:
        recs.append("Best-shaping association below target → increase creator try-ons + before/after proof + fit education.")
    if actual.csat < 0.85:
        recs.append("CSAT below target → improve post-purchase support, sizing guidance, and reduce friction in returns/exchanges.")

    if not recs:
        recs.append("All key KPIs meet or exceed targets → scale what works and run controlled tests to push LTV further.")

    return recs


def bar_chart(title: str, labels: List[str], values: List[float], y_label: str, target_line: float | None = None):
    # Graph always works: labels/values must match
    if len(labels) != len(values):
        st.error(f"Chart error: labels ({len(labels)}) and values ({len(values)}) mismatch.")
        return

    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel(y_label)
    ax.set_ylim(bottom=0)

    if target_line is not None and isinstance(target_line, (int, float)) and not math.isnan(float(target_line)):
        ax.axhline(target_line, linestyle="--")
        ax.text(
            0.02,
            target_line,
            f"Target: {target_line}",
            va="bottom",
            ha="left",
            transform=ax.get_yaxis_transform()
        )

    st.pyplot(fig, clear_figure=True)


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="SKIMS KPI Measurement Tool", layout="wide")
st.title("SKIMS — KPI Measurement Tool (Germany + Spain)")
st.caption("Campaign: 8-week “Try → Love → Repeat” • North Star: 6-month LTV • Funnel: Exposure → Intent → 1st → 2nd → LTV → ROMI")

with st.sidebar:
    st.header("Business Assumptions")
    paid_sessions = st.number_input("Paid sessions", min_value=0, value=DEFAULTS["paid_sessions"], step=10_000)
    aov_eur = st.number_input("AOV (€)", min_value=0.0, value=float(DEFAULTS["aov_eur"]), step=1.0)
    contribution_margin = st.number_input("Contribution margin (0–1)", 0.0, 1.0, float(DEFAULTS["contribution_margin"]), 0.01)
    campaign_cost_eur = st.number_input("Campaign cost (€)", min_value=0.0, value=float(DEFAULTS["campaign_cost_eur"]), step=10_000.0)

st.subheader("1) Scenarios: Baseline • Ex-Ante Target • Ex-Post Actual")
col1, col2, col3 = st.columns(3)

# -----------------------------
# Inputs (defaults = your new numbers)
# -----------------------------
with col1:
    st.markdown("### Baseline")

    base_reach3 = st.number_input("Reach 3+ (baseline)", 0.0, 1.0, 0.40, 0.01)
    base_ctr = st.number_input("CTR (baseline)", 0.0, 1.0, 0.012, 0.001)
    base_pdp = st.number_input("PDP reach rate (baseline)", 0.0, 1.0, 0.50, 0.01)

    base_cvr = st.number_input("CVR (baseline)", 0.0, 1.0, 0.035, 0.001)
    base_repeat = st.number_input("Repeat rate 90d (baseline)", 0.0, 1.0, 0.28, 0.01)
    base_email_share = st.number_input("Email revenue share (baseline)", 0.0, 1.0, 0.18, 0.01)

    base_time2 = st.number_input("Time to 2nd purchase days (baseline)", min_value=0.0, value=75.0, step=1.0)
    base_ltv = st.number_input("6-mo LTV € (baseline)", min_value=0.0, value=120.0, step=1.0)

    base_worth = st.number_input("Worth the price (baseline)", 0.0, 1.0, 0.52, 0.01)
    base_shape = st.number_input("Best shaping assoc (baseline)", 0.0, 1.0, 0.48, 0.01)
    base_csat = st.number_input("CSAT (baseline)", 0.0, 1.0, 0.78, 0.01)

with col2:
    st.markdown("### Ex-Ante Target")

    tgt_reach3 = st.number_input("Reach 3+ (target)", 0.0, 1.0, 0.45, 0.01)
    tgt_ctr = st.number_input("CTR (target)", 0.0, 1.0, 0.015, 0.001)
    tgt_pdp = st.number_input("PDP reach rate (target)", 0.0, 1.0, 0.55, 0.01)

    tgt_cvr = st.number_input("CVR (target)", 0.0, 1.0, 0.035, 0.001)
    tgt_repeat = st.number_input("Repeat rate 90d (target)", 0.0, 1.0, 0.32, 0.01)
    tgt_email_share = st.number_input("Email revenue share (target)", 0.0, 1.0, 0.25, 0.01)

    tgt_time2 = st.number_input("Time to 2nd purchase days (target)", min_value=0.0, value=60.0, step=1.0)
    tgt_ltv = st.number_input("6-mo LTV € (target)", min_value=0.0, value=132.0, step=1.0)

    tgt_worth = st.number_input("Worth the price (target)", 0.0, 1.0, 0.58, 0.01)
    tgt_shape = st.number_input("Best shaping assoc (target)", 0.0, 1.0, 0.53, 0.01)
    tgt_csat = st.number_input("CSAT (target)", 0.0, 1.0, 0.85, 0.01)

with col3:
    st.markdown("### Ex-Post Actual")

    # If you want: adjust these to match your chosen ex-post values
    act_reach3 = st.number_input("Reach 3+ (actual)", 0.0, 1.0, 0.44, 0.01)
    act_ctr = st.number_input("CTR (actual)", 0.0, 1.0, 0.016, 0.001)
    act_pdp = st.number_input("PDP reach rate (actual)", 0.0, 1.0, 0.55, 0.01)

    act_cvr = st.number_input("CVR (actual)", 0.0, 1.0, 0.034, 0.001)
    act_repeat = st.number_input("Repeat rate 90d (actual)", 0.0, 1.0, 0.32, 0.01)  # from your slide
    act_email_share = st.number_input("Email revenue share (actual)", 0.0, 1.0, 0.29, 0.01)

    # Your summative slide did not show ex-post for time to 2nd purchase.
    # Set a default here (edit if you have the real number).
    act_time2 = st.number_input("Time to 2nd purchase days (actual)", min_value=0.0, value=65.0, step=1.0)
    act_ltv = st.number_input("6-mo LTV € (actual)", min_value=0.0, value=130.0, step=1.0)  # from your slide

    act_worth = st.number_input("Worth the price (actual)", 0.0, 1.0, 0.56, 0.01)
    act_shape = st.number_input("Best shaping assoc (actual)", 0.0, 1.0, 0.51, 0.01)
    act_csat = st.number_input("CSAT (actual)", 0.0, 1.0, 0.82, 0.01)

baseline = Scenario(
    name="Baseline",
    cvr=base_cvr,
    repeat_rate_90d=base_repeat,
    email_rev_share=base_email_share,
    reach_3plus=base_reach3,
    ctr=base_ctr,
    pdp_reach_rate=base_pdp,
    time_to_2nd_purchase_days=base_time2,
    ltv_6mo_eur=base_ltv,
    worth_the_price=base_worth,
    best_shaping_association=base_shape,
    csat=base_csat,
)

target = Scenario(
    name="Target",
    cvr=tgt_cvr,
    repeat_rate_90d=tgt_repeat,
    email_rev_share=tgt_email_share,
    reach_3plus=tgt_reach3,
    ctr=tgt_ctr,
    pdp_reach_rate=tgt_pdp,
    time_to_2nd_purchase_days=tgt_time2,
    ltv_6mo_eur=tgt_ltv,
    worth_the_price=tgt_worth,
    best_shaping_association=tgt_shape,
    csat=tgt_csat,
)

actual = Scenario(
    name="Actual",
    cvr=act_cvr,
    repeat_rate_90d=act_repeat,
    email_rev_share=act_email_share,
    reach_3plus=act_reach3,
    ctr=act_ctr,
    pdp_reach_rate=act_pdp,
    time_to_2nd_purchase_days=act_time2,
    ltv_6mo_eur=act_ltv,
    worth_the_price=act_worth,
    best_shaping_association=act_shape,
    csat=act_csat,
)

# -----------------------------
# Outputs
# -----------------------------
st.subheader("2) KPI Dictionary + Ex-Ante Target Table")
st.dataframe(build_ex_ante_table(), use_container_width=True)

st.subheader("3) Traffic-to-Profit Summary (Baseline vs Actual)")
biz = calc_business_outputs(
    paid_sessions=paid_sessions,
    aov_eur=aov_eur,
    margin=contribution_margin,
    campaign_cost_eur=campaign_cost_eur,
    baseline=baseline,
    actual=actual,
)

summary_df = pd.DataFrame([
    {"Metric": "New customers", "Baseline": biz["baseline_new_customers"], "Actual": biz["actual_new_customers"]},
    {"Metric": "Second orders", "Baseline": biz["baseline_second_orders"], "Actual": biz["actual_second_orders"]},
    {"Metric": "Revenue (€)", "Baseline": biz["baseline_revenue_eur"], "Actual": biz["actual_revenue_eur"]},
    {"Metric": "Profit (€)", "Baseline": biz["baseline_profit_eur"], "Actual": biz["actual_profit_eur"]},
    {"Metric": "Email revenue (€)", "Baseline": biz["baseline_email_revenue_eur"], "Actual": biz["actual_email_revenue_eur"]},
    {"Metric": "Incremental profit (€)", "Baseline": 0.0, "Actual": biz["incremental_profit_eur"]},
    {"Metric": "ROMI", "Baseline": None, "Actual": biz["romi"]},
])
st.dataframe(summary_df, use_container_width=True)

st.subheader("4) Ex-Post Evaluation Table (Target vs Actual)")
eval_df = evaluate_kpis(target=target, actual=actual, romi_actual=biz["romi"])
st.dataframe(eval_df, use_container_width=True)

st.subheader("5) Automatic Recommendations")
for r in make_recommendations(actual=actual, romi=biz["romi"]):
    st.write(f"- {r}")

st.subheader("6) Charts (working)")
c1, c2, c3 = st.columns(3)

with c1:
    bar_chart(
        title="6-month LTV (€)",
        labels=["Baseline", "Target", "Actual"],
        values=[baseline.ltv_6mo_eur, target.ltv_6mo_eur, actual.ltv_6mo_eur],
        y_label="€",
        target_line=target.ltv_6mo_eur,
    )

with c2:
    bar_chart(
        title="Repeat Purchase Rate (90d)",
        labels=["Baseline", "Target", "Actual"],
        values=[baseline.repeat_rate_90d, target.repeat_rate_90d, actual.repeat_rate_90d],
        y_label="Rate",
        target_line=target.repeat_rate_90d,
    )

with c3:
    # ROMI uses formula from baseline vs actual; show target line 1.8
    bar_chart(
        title="Marketing ROMI",
        labels=["Actual ROMI"],
        values=[biz["romi"]],
        y_label="ROMI",
        target_line=1.8,
    )

st.caption("All % KPIs are entered as decimals (example: 0.32 = 32%).")
