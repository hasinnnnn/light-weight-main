from __future__ import annotations

import streamlit as st

APP_GLOBAL_STYLES = """
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 100% !important;
}
.stApp iframe {
    width: 100% !important;
    min-width: 100% !important;
}
.insight-card {
    background: linear-gradient(180deg, #071426 0%, #0a1b30 100%);
    border: 1px solid rgba(56, 189, 248, 0.28);
    border-radius: 18px;
    margin: 0.85rem 0 1.05rem 0;
    padding: 1.2rem 1rem 1.35rem 1rem;
    text-align: center;
}
.insight-header {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    justify-content: center;
}
.insight-title {
    color: #ffffff;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: 0.02em;
    line-height: 1.1;
}
.insight-price {
    color: #f8fafc;
    font-size: 1.45rem;
    font-weight: 700;
    line-height: 1.1;
}
.insight-change {
    font-size: 1.1rem;
    font-weight: 700;
    line-height: 1.1;
}
.change-up {
    color: #4ade80;
}
.change-down {
    color: #f87171;
}
.change-flat {
    color: #cbd5e1;
}
.insight-subtitle {
    color: #9fb9d9;
    font-size: 0.95rem;
    margin-top: 0.35rem;
}
.insight-stats-grid {
    background: rgba(8, 15, 28, 0.52);
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 13px;
    display: grid;
    column-gap: 0.95rem;
    row-gap: 0.25rem;
    grid-template-columns: repeat(var(--insight-stat-columns, 3), max-content);
    justify-content: center;
    margin: 0.75rem auto 0.85rem auto;
    max-width: min(100%, 560px);
    padding: 0.62rem 0.8rem;
    text-align: left;
    width: fit-content;
}
.insight-stats-column {
    display: flex;
    flex-direction: column;
    gap: 0.28rem;
    min-width: 112px;
}
.insight-stat-item {
    align-items: center;
    display: flex;
    gap: 0.45rem;
    justify-content: space-between;
}
.insight-stat-label {
    color: #98abc5;
    font-size: 0.8rem;
    line-height: 1.1;
}
.insight-stat-value {
    font-size: 0.92rem;
    font-weight: 700;
    line-height: 1.1;
}
.stat-up {
    color: #4ade80;
}
.stat-down {
    color: #f87171;
}
.stat-neutral {
    color: #e2e8f0;
}
.stat-soft {
    color: #fca5a5;
}
.insight-pill-row {
    display: flex;
    justify-content: center;
    gap: 0.85rem;
    flex-wrap: wrap;
    margin: 1rem 0 0.95rem 0;
}
.insight-pill {
    border-radius: 999px;
    display: inline-flex;
    font-size: 1rem;
    font-weight: 700;
    padding: 0.55rem 1rem;
}
.trend-up {
    background: rgba(16, 185, 129, 0.18);
    border: 1px solid rgba(52, 211, 153, 0.45);
    color: #86efac;
}
.trend-down {
    background: rgba(239, 68, 68, 0.16);
    border: 1px solid rgba(248, 113, 113, 0.4);
    color: #fca5a5;
}
.risk-low {
    background: rgba(59, 130, 246, 0.16);
    border: 1px solid rgba(96, 165, 250, 0.4);
    color: #93c5fd;
}
.risk-high {
    background: rgba(244, 63, 94, 0.16);
    border: 1px solid rgba(251, 113, 133, 0.4);
    color: #fda4af;
}
.insight-reason {
    color: #dcecff;
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.45;
}
.indicator-row-title {
    color: #ffffff;
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.2;
}
.indicator-row-status {
    color: #90a7c6;
    font-size: 0.82rem;
    margin-top: 0.15rem;
}
.indicator-note-card {
    background: linear-gradient(180deg, #06111f 0%, #0a1728 100%);
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 18px;
    margin: 0.95rem 0 1rem 0;
    padding: 1rem;
}
.indicator-note-card-title {
    color: #f8fafc;
    font-size: 1.05rem;
    font-weight: 800;
    line-height: 1.15;
}
.indicator-note-section {
    border-top: 1px solid rgba(148, 163, 184, 0.14);
    margin-top: 0.8rem;
    padding-top: 0.8rem;
}
.indicator-note-section:first-of-type {
    border-top: none;
    margin-top: 0.6rem;
    padding-top: 0;
}
.indicator-note-section-title {
    color: #f8fafc;
    font-size: 0.96rem;
    font-weight: 700;
}
.indicator-note-section-summary {
    color: #dce7f7;
    font-size: 0.88rem;
    line-height: 1.5;
    margin-top: 0.25rem;
}
.indicator-note-section-context {
    color: #8fa7c5;
    font-size: 0.8rem;
    margin-top: 0.3rem;
}
.indicator-note-grid {
    align-items: stretch;
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin-top: 0.65rem;
}
.indicator-note-box {
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.84) 0%, rgba(10, 17, 28, 0.94) 100%);
    border: 1px solid var(--indicator-note-accent);
    border-radius: 14px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
    flex: 0 1 280px;
    max-width: 340px;
    min-width: 210px;
    padding: 0.7rem 0.78rem;
}
.indicator-note-box-empty {
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.78) 0%, rgba(10, 17, 28, 0.94) 100%);
    border-color: rgba(148, 163, 184, 0.22);
}
.indicator-note-box-label {
    color: #f8fafc;
    font-size: 0.88rem;
    font-weight: 700;
    margin-bottom: 0.18rem;
}
.indicator-note-box-value {
    color: #ffffff;
    font-size: 0.98rem;
    font-weight: 800;
    line-height: 1.28;
}
.indicator-note-box-meta {
    color: #cdd8e8;
    font-size: 0.77rem;
    line-height: 1.4;
    margin-top: 0.18rem;
}
.indicator-note-box-empty-text {
    color: #93a4bb;
    font-size: 0.78rem;
    line-height: 1.4;
}
@media (max-width: 720px) {
    .insight-stats-grid {
        gap: 0.7rem;
        grid-template-columns: 1fr;
        max-width: 100%;
        width: 100%;
    }
    .insight-stats-column {
        min-width: 0;
    }
}
</style>
"""


def render_app_styles() -> None:
    """Inject the shared CSS used across the Streamlit app."""
    st.markdown(APP_GLOBAL_STYLES, unsafe_allow_html=True)
