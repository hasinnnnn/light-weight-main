from __future__ import annotations

import streamlit as st

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - transitively installed by yfinance in normal use
    requests = None

from data.models import SymbolSuggestion

INDONESIA_SYMBOL_SUFFIX = ".JK"
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
SEARCHABLE_QUOTE_TYPES = {"EQUITY", "ETF", "INDEX", "MUTUALFUND", "WARRANT"}
SYMBOL_ALIASES = {
    "IHSG": "^JKSE",
}
LOCAL_SYMBOL_CATALOG = [
    ("IHSG", "Indeks Harga Saham Gabungan", "^JKSE", "INDEX", "Indonesia"),
    ("PADI", "Minna Padi Investama Sekuritas Tbk.", "PADI.JK", "EQUITY", "Indonesia"),
    ("MGNA", "Magna Investama Mandiri Tbk", "MGNA.JK", "EQUITY", "Indonesia"),
    ("BISI", "BISI International Tbk.", "BISI.JK", "EQUITY", "Indonesia"),
    ("BBCA", "Bank Central Asia Tbk.", "BBCA.JK", "EQUITY", "Indonesia"),
    ("BIPI", "Astrindo Nusantara Infrastruktur Tbk.", "BIPI.JK", "EQUITY", "Indonesia"),
    ("BBRI", "Bank Rakyat Indonesia (Persero) Tbk.", "BBRI.JK", "EQUITY", "Indonesia"),
    ("BMRI", "Bank Mandiri (Persero) Tbk.", "BMRI.JK", "EQUITY", "Indonesia"),
    ("BBNI", "Bank Negara Indonesia (Persero) Tbk.", "BBNI.JK", "EQUITY", "Indonesia"),
    ("TLKM", "Telkom Indonesia (Persero) Tbk.", "TLKM.JK", "EQUITY", "Indonesia"),
    ("ASII", "Astra International Tbk.", "ASII.JK", "EQUITY", "Indonesia"),
    ("GOTO", "GoTo Gojek Tokopedia Tbk.", "GOTO.JK", "EQUITY", "Indonesia"),
    ("ANTM", "Aneka Tambang Tbk.", "ANTM.JK", "EQUITY", "Indonesia"),
    ("ADRO", "Alamtri Resources Indonesia Tbk.", "ADRO.JK", "EQUITY", "Indonesia"),
    ("MDKA", "Merdeka Copper Gold Tbk.", "MDKA.JK", "EQUITY", "Indonesia"),
    ("INDF", "Indofood Sukses Makmur Tbk.", "INDF.JK", "EQUITY", "Indonesia"),
    ("UNVR", "Unilever Indonesia Tbk.", "UNVR.JK", "EQUITY", "Indonesia"),
    ("AMMN", "Amman Mineral Internasional Tbk.", "AMMN.JK", "EQUITY", "Indonesia"),
]


def sanitize_symbol(symbol: str) -> str:
    """Normalize a ticker/symbol from the UI."""
    return (symbol or "").strip().upper()



def display_symbol(symbol: str) -> str:
    """Convert provider symbols into a user-friendly display code."""
    cleaned_symbol = sanitize_symbol(symbol)
    if cleaned_symbol == "^JKSE":
        return "IHSG"
    if cleaned_symbol.endswith(INDONESIA_SYMBOL_SUFFIX):
        return cleaned_symbol[: -len(INDONESIA_SYMBOL_SUFFIX)]
    return cleaned_symbol



def _catalog_entry_to_suggestion(entry: tuple[str, str, str, str, str]) -> SymbolSuggestion:
    symbol, company_name, provider_symbol, instrument_type, exchange = entry
    return SymbolSuggestion(
        symbol=symbol,
        company_name=company_name,
        provider_symbol=provider_symbol,
        instrument_type=instrument_type,
        exchange=exchange,
    )



def _find_exact_local_suggestion(symbol: str) -> SymbolSuggestion | None:
    """Return an exact local-catalog match for either display code or provider symbol."""
    cleaned_symbol = sanitize_symbol(symbol)
    if not cleaned_symbol:
        return None

    display_code = display_symbol(cleaned_symbol)
    for entry in LOCAL_SYMBOL_CATALOG:
        suggestion = _catalog_entry_to_suggestion(entry)
        if cleaned_symbol in {
            sanitize_symbol(suggestion.symbol),
            sanitize_symbol(suggestion.provider_symbol),
        }:
            return suggestion
        if display_code and display_code == sanitize_symbol(suggestion.symbol):
            return suggestion

    return None



def resolve_provider_symbol(symbol: str) -> str:
    """Map friendly UI aliases to the upstream market-data ticker symbol."""
    cleaned_symbol = sanitize_symbol(symbol)
    aliased_symbol = SYMBOL_ALIASES.get(cleaned_symbol)
    if aliased_symbol is not None:
        return aliased_symbol

    local_suggestion = _find_exact_local_suggestion(cleaned_symbol)
    if local_suggestion is not None:
        return local_suggestion.provider_symbol

    return cleaned_symbol



def candidate_provider_symbols(symbol: str) -> list[str]:
    """Build provider-symbol candidates, including common Indonesian stock shorthand."""
    cleaned_symbol = sanitize_symbol(symbol)
    resolved_symbol = resolve_provider_symbol(cleaned_symbol)
    candidates = [resolved_symbol]

    if (
        resolved_symbol == cleaned_symbol
        and cleaned_symbol.isalpha()
        and 3 <= len(cleaned_symbol) <= 5
    ):
        indonesia_symbol = f"{cleaned_symbol}{INDONESIA_SYMBOL_SUFFIX}"
        candidates.append(indonesia_symbol)

    return list(dict.fromkeys(candidates))



def _suggestion_sort_key(suggestion: SymbolSuggestion, query: str) -> tuple[int, int, int, str]:
    cleaned_query = sanitize_symbol(query)
    symbol = suggestion.symbol.upper()
    company_name = suggestion.company_name.upper()
    exchange = suggestion.exchange.upper()
    is_indonesia = (
        suggestion.provider_symbol.endswith(INDONESIA_SYMBOL_SUFFIX)
        or suggestion.provider_symbol == "^JKSE"
        or "INDONESIA" in exchange
        or "JAKARTA" in exchange
    )
    if symbol == cleaned_query:
        symbol_rank = 0
    elif symbol.startswith(cleaned_query):
        symbol_rank = 1
    elif cleaned_query in symbol:
        symbol_rank = 2
    elif cleaned_query in company_name:
        symbol_rank = 3
    else:
        symbol_rank = 4
    return (symbol_rank, 0 if is_indonesia else 1, len(symbol), symbol)



def _search_local_catalog(query: str) -> list[SymbolSuggestion]:
    cleaned_query = sanitize_symbol(query)
    if not cleaned_query:
        return []

    matches = []
    for entry in LOCAL_SYMBOL_CATALOG:
        suggestion = _catalog_entry_to_suggestion(entry)
        haystack = f"{suggestion.symbol} {suggestion.company_name}".upper()
        if cleaned_query in haystack:
            matches.append(suggestion)

    return sorted(matches, key=lambda item: _suggestion_sort_key(item, cleaned_query))



def _quote_to_suggestion(quote: dict[str, object]) -> SymbolSuggestion | None:
    raw_symbol = sanitize_symbol(str(quote.get("symbol") or ""))
    quote_type = sanitize_symbol(str(quote.get("quoteType") or ""))
    company_name = str(
        quote.get("longname") or quote.get("shortname") or quote.get("name") or ""
    ).strip()
    exchange = str(quote.get("exchDisp") or quote.get("exchange") or "").strip()

    if not raw_symbol or quote_type not in SEARCHABLE_QUOTE_TYPES:
        return None

    if raw_symbol == "^JKSE" and not company_name:
        company_name = "Indeks Harga Saham Gabungan"

    if not company_name:
        return None

    return SymbolSuggestion(
        symbol=display_symbol(raw_symbol),
        company_name=company_name,
        provider_symbol=raw_symbol,
        instrument_type=quote_type,
        exchange=exchange,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _search_yahoo_quotes(query: str) -> list[SymbolSuggestion]:
    """Search Yahoo Finance for a query and normalize the returned quotes."""
    if requests is None:
        return []

    response = requests.get(
        YAHOO_SEARCH_URL,
        params={
            "q": query,
            "quotesCount": 12,
            "newsCount": 0,
            "listsCount": 0,
            "enableFuzzyQuery": True,
        },
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=4,
    )
    response.raise_for_status()
    payload = response.json()
    quotes = payload.get("quotes") or []

    suggestions: list[SymbolSuggestion] = []
    for quote in quotes:
        if not isinstance(quote, dict):
            continue
        suggestion = _quote_to_suggestion(quote)
        if suggestion is not None:
            suggestions.append(suggestion)

    return suggestions



def _deduplicate_suggestions(suggestions: list[SymbolSuggestion]) -> list[SymbolSuggestion]:
    deduplicated: list[SymbolSuggestion] = []
    seen: set[str] = set()

    for suggestion in suggestions:
        suggestion_key = suggestion.provider_symbol or suggestion.symbol
        if suggestion_key in seen:
            continue
        seen.add(suggestion_key)
        deduplicated.append(suggestion)

    return deduplicated



def resolve_company_name(symbol: str) -> str:
    """Resolve a full company/index name for the displayed symbol."""
    cleaned_symbol = sanitize_symbol(symbol)
    display_code = display_symbol(cleaned_symbol)

    local_suggestion = _find_exact_local_suggestion(cleaned_symbol)
    if local_suggestion is not None:
        return local_suggestion.company_name

    queries = [display_code, cleaned_symbol]
    for query in queries:
        if not query or len(query) < 2:
            continue
        try:
            suggestions = _search_yahoo_quotes(query)
        except Exception:
            continue

        for suggestion in suggestions:
            if cleaned_symbol in {
                sanitize_symbol(suggestion.provider_symbol),
                sanitize_symbol(suggestion.symbol),
            }:
                return suggestion.company_name
            if display_code and display_code == sanitize_symbol(suggestion.symbol):
                return suggestion.company_name

    return display_code or cleaned_symbol



def search_symbol_suggestions(query: str, limit: int = 8) -> list[SymbolSuggestion]:
    """Return user-friendly symbol suggestions with both code and company name."""
    cleaned_query = (query or "").strip()
    if len(cleaned_query) < 2:
        return []

    suggestions: list[SymbolSuggestion] = []
    try:
        suggestions.extend(_search_yahoo_quotes(cleaned_query))
    except Exception:
        pass

    suggestions.extend(_search_local_catalog(cleaned_query))
    suggestions = _deduplicate_suggestions(suggestions)
    suggestions.sort(key=lambda item: _suggestion_sort_key(item, cleaned_query))
    return suggestions[:limit]
