from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class StrategyPreparation:
    """Prepared indicator dataframe and rule summaries used by the engine."""

    frame: pd.DataFrame
    warmup_bars: int
    entry_rule_summary: str
    exit_rule_summary: str
