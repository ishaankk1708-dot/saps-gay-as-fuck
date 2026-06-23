import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Excel Column Analyser",
    page_icon="📊",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background: #0f1117; }

    .hero {
        background: linear-gradient(135deg, #1a1f2e 0%, #0d1b2a 100%);
        border: 1px solid #2a3550;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
    }
    .hero h1 { color: #e8eaf6; font-size: 2rem; font-weight: 700; margin: 0 0 .4rem; }
    .hero p  { color: #7986cb; font-size: 1rem; margin: 0; }

    .stat-card {
        background: #1a1f2e;
        border: 1px solid #2a3550;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .stat-card .label { color: #7986cb; font-size: .75rem; font-weight: 600;
                        text-transform: uppercase; letter-spacing: .08em; margin-bottom: .3rem; }
    .stat-card .value { color: #e8eaf6; font-size: 1.5rem; font-weight: 700; }

    .forecast-badge {
        background: linear-gradient(135deg, #1b5e20, #2e7d32);
        border: 1px solid #43a047;
        border-radius: 10px;
        padding: .6rem 1.2rem;
        color: #a5d6a7;
        font-weight: 600;
        font-size: .9rem;
        display: inline-block;
        margin-top: .8rem;
    }
    .skew-badge {
        background: #1a1f2e;
        border: 1px solid #37474f;
        border-radius: 10px;
        padding: .5rem 1rem;
        color: #90a4ae;
        font-size: .85rem;
        display: inline-block;
        margin-top: .8rem;
    }

    .col-header {
        color: #c5cae9;
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: .3rem;
        padding-bottom: .3rem;
        border-bottom: 2px solid #3f51b5;
    }

    .stFileUploader { background: transparent !important; }
    [data-testid="stFileUploadDropzone"] {
        background: #1a1f2e !important;
        border: 2px dashed #3f51b5 !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>📊 Excel Column Analyser</h1>
    <p>Upload any Excel file · Auto-detect numerical columns · Histogram + Stats + Forecast signal</p>
</div>
""", unsafe_allow_html=True)

# ── File uploader ─────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Drop your Excel file here", type=["xlsx", "xls"])

if uploaded is None:
    st.info("Waiting for an Excel file…")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if not num_cols:
    st.warning("No numerical columns found in this file.")
    st.stop()

st.markdown(f"**{len(num_cols)} numerical column(s) detected** out of {len(df.columns)} total · {len(df):,} rows")

# ── Threshold slider ──────────────────────────────────────────────────────────
with st.expander("⚙️ Forecast threshold (% difference between mean & median)"):
    threshold = st.slider(
        "If |mean − median| / mean < threshold → data is Forecast-ready",
        min_value=1, max_value=30, value=10, step=1,
        format="%d%%"
    ) / 100

st.markdown("---")

# ── Per-column analysis ───────────────────────────────────────────────────────
for col in num_cols:
    series = df[col].dropna()

    if len(series) == 0:
        continue

    mean_val   = series.mean()
    median_val = series.median()
    std_val    = series.std()
    skew_val   = series.skew()

    # Forecast check
    if mean_val != 0:
        diff_pct = abs(mean_val - median_val) / abs(mean_val)
    else:
        diff_pct = abs(mean_val - median_val)

    forecast_ready = diff_pct < threshold

    # Layout
    st.markdown(f'<div class="col-header">📈 {col}</div>', unsafe_allow_html=True)
    lcol, rcol = st.columns([2, 1])

    with lcol:
        # Histogram
        fig, ax = plt.subplots(figsize=(7, 3.5))
        fig.patch.set_facecolor("#0f1117")
        ax.set_facecolor("#1a1f2e")

        n, bins, patches = ax.hist(series, bins="auto", color="#3f51b5",
                                   edgecolor="#5c6bc0", linewidth=0.6, alpha=0.9)

        # Mean & median lines
        ax.axvline(mean_val,   color="#ef5350", linewidth=1.8,
                   linestyle="--", label=f"Mean  {mean_val:,.2f}")
        ax.axvline(median_val, color="#66bb6a", linewidth=1.8,
                   linestyle="-.",  label=f"Median {median_val:,.2f}")

        ax.legend(fontsize=8, facecolor="#1a1f2e", edgecolor="#2a3550",
                  labelcolor="#e8eaf6")
        ax.set_xlabel(col, color="#90a4ae", fontsize=9)
        ax.set_ylabel("Frequency", color="#90a4ae", fontsize=9)
        ax.tick_params(colors="#546e7a", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#2a3550")

        ax.xaxis.set_major_formatter(ticker.FuncFormatter(
            lambda x, _: f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.2f}"
        ))

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with rcol:
        st.markdown(f"""
        <div class="stat-card">
            <div class="label">Mean</div>
            <div class="value">{mean_val:,.4f}</div>
        </div>
        <div class="stat-card">
            <div class="label">Median</div>
            <div class="value">{median_val:,.4f}</div>
        </div>
        <div class="stat-card">
            <div class="label">Std Dev</div>
            <div class="value">{std_val:,.4f}</div>
        </div>
        <div class="stat-card">
            <div class="label">|Mean − Median| / Mean</div>
            <div class="value">{diff_pct:.1%}</div>
        </div>
        """, unsafe_allow_html=True)

        if forecast_ready:
            st.markdown(
                '<div class="forecast-badge">✅ The data can be used for Forecasting</div>',
                unsafe_allow_html=True
            )
        else:
            direction = "right-skewed (mean > median)" if mean_val > median_val else "left-skewed (mean < median)"
            st.markdown(
                f'<div class="skew-badge">⚠️ Data is {direction} — not ideal for direct Forecasting</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
