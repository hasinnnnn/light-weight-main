from __future__ import annotations

import streamlit as st

from state.app_state import build_effective_indicator_configs, initialize_session_state, run_selected_backtest
from charts.chart_service import ChartServiceError, render_candlestick_chart, render_indicator_charts
from data.market_data_service import DataServiceError, load_market_data
from ui.backtest_result_card import render_backtest_result_card
from ui.market_insight import render_indicator_explanation_card, render_market_insight_card
from ui.theme import render_app_styles
from ui.top_toolbar import render_top_toolbar


def attempt_data_load() -> None:
    """Fetch and store the latest requested market data."""
    with st.spinner("Loading market data..."):
        try:
            result = load_market_data(
                symbol=st.session_state.symbol_input,
                interval_label=st.session_state.interval_option,
                period_label=st.session_state.period_option,
            )
        except DataServiceError as exc:
            st.session_state.last_error = str(exc)
        else:
            st.session_state.loaded_result = result
            st.session_state.last_error = ""
            st.session_state.selected_company_name = result.company_name
            st.session_state.backtest_period_label = result.period_label
            if st.session_state.backtest_enabled:
                run_selected_backtest(show_spinner=False)


def main() -> None:
    """Run the Streamlit application."""
    st.set_page_config(page_title="Chart Hasin", layout="wide")
    initialize_session_state()
    render_app_styles()

    st.title("Chart Hasin")

    if st.session_state.pending_load:
        attempt_data_load()
        st.session_state.pending_load = False

    if (
        st.session_state.backtest_enabled
        and st.session_state.backtest_refresh_requested
        and st.session_state.loaded_result is not None
    ):
        run_selected_backtest(show_spinner=False)

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    result = st.session_state.loaded_result
    if result is not None:
        render_market_insight_card()

    render_top_toolbar(result)

    if result is None:
        st.info("Ketik kode saham seperti IHSG, BBCA, PADI, AAPL, atau BTC-USD lalu tekan Enter.")
        return

    for message in result.warnings:
        st.warning(message)

    if st.session_state.backtest_last_error:
        st.error(st.session_state.backtest_last_error)

    indicator_configs = build_effective_indicator_configs()

    try:
        render_candlestick_chart(
            data=result.data,
            symbol=result.symbol,
            interval_label=result.interval_label,
            display_name=result.company_name,
            indicator_configs=indicator_configs,
            use_bei_price_fractions=result.uses_bei_price_fractions,
            backtest_trade_log=(
                st.session_state.backtest_result.trade_log
                if st.session_state.backtest_result is not None
                else None
            ),
        )
        render_indicator_charts(
            data=result.data,
            indicator_configs=indicator_configs,
        )
        if st.session_state.backtest_result is not None:
            render_backtest_result_card(st.session_state.backtest_result)
        render_indicator_explanation_card()
    except (ChartServiceError, ModuleNotFoundError) as exc:
        st.error(str(exc))
        st.code("pip install -r requirements.txt")


if __name__ == "__main__":
    main()

