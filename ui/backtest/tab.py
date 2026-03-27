from __future__ import annotations

import streamlit as st

from backtest.config import (
    display_backtest_period_label,
    filter_backtest_strategies,
    get_strategy_label,
)

VALID_BACKTEST_STRATEGIES = {"RSI", "MACD", "BREAK_EMA", "BREAK_MA", "PARABOLIC_SAR", "VOLUME_BREAKOUT"}


def render_backtest_tab(has_loaded_data: bool) -> dict[str, bool]:
    """Render the setup-only backtest tab inside the indicator dialog."""
    actions = {
        "open_parameters": False,
        "strategy_changed": False,
        "stop_backtest": False,
    }

    selected_strategy = str(st.session_state.selected_backtest_strategy or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    has_selected_strategy = selected_strategy in VALID_BACKTEST_STRATEGIES
    selected_strategy_label = (
        get_strategy_label(selected_strategy)
        if has_selected_strategy
        else "Belum dipilih"
    )

    st.text_input(
        "Cari strategi backtest",
        key="backtest_search_query",
        placeholder="Cari strategi backtest...",
    )
    search_query = str(st.session_state.backtest_search_query or "").strip()

    with st.container(border=True):
        info_col, action_col = st.columns([5.8, 1.2])
        with info_col:
            st.markdown("**Parameter**")
            st.caption(
                "Atur modal awal, ukuran posisi, fee, stop loss, take profit, "
                "preview indikator, dan parameter strategi."
            )
        with action_col:
            if st.button(
                "Buka",
                key="backtest_open_parameter_button",
                use_container_width=True,
                disabled=not has_selected_strategy,
            ):
                actions["open_parameters"] = True

    period_label = display_backtest_period_label(st.session_state.backtest_period_label)
    st.caption(f"Periode backtest: mengikuti chart aktif ({period_label})")

    if st.session_state.backtest_enabled and has_selected_strategy:
        st.success(
            f"Backtest aktif: {selected_strategy_label}. "
            "Begitu strategi dipilih, disimpan, atau saat kode saham, timeframe, "
            "dan periode chart diganti, backtest akan jalan ulang otomatis."
        )
    elif has_selected_strategy and has_loaded_data:
        st.caption(
            f"Begitu strategi {selected_strategy_label} dipilih, backtest akan langsung jalan otomatis."
        )
    elif has_selected_strategy:
        st.caption(
            f"Strategi {selected_strategy_label} sudah dipilih. "
            "Saat data chart tersedia, backtest akan jalan otomatis."
        )
    else:
        st.caption("Pilih strategi backtest dulu. Begitu dipilih, backtest langsung jalan otomatis.")

    filtered_strategies = filter_backtest_strategies(search_query)
    if not filtered_strategies:
        st.info("Belum ada strategi yang cocok dengan pencarian itu.")
    else:
        for strategy in filtered_strategies:
            is_selected = strategy["key"] == selected_strategy
            with st.container(border=True):
                info_col, action_col = st.columns([6.0, 1.25])
                with info_col:
                    title = f"**{strategy['label']}**"
                    if is_selected:
                        title += "  `Terpilih`"
                    st.markdown(title)
                    st.caption(strategy["description"])
                with action_col:
                    if st.button(
                        "Dipilih" if is_selected else "Pilih",
                        key=f"backtest_strategy_select_{strategy['key']}",
                        use_container_width=True,
                        disabled=is_selected,
                    ):
                        st.session_state.selected_backtest_strategy = strategy["key"]
                        actions["strategy_changed"] = True

    if st.session_state.backtest_enabled:
        if st.button(
            "Matikan Backtest",
            key="stop_backtest_button",
            use_container_width=True,
        ):
            actions["stop_backtest"] = True
        st.caption(
            "Tidak perlu klik tombol jalanin manual. Cukup pilih strategi sekali, lalu "
            "hasil backtest akan ikut diperbarui otomatis."
        )
    elif has_selected_strategy and not has_loaded_data:
        st.caption("Load chart dulu supaya hasil backtest bisa tampil setelah strategi dipilih.")

    return actions





