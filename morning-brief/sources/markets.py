# Pulls price and news data for a configured watchlist of stocks/assets

import yfinance as yf


def get_market_data(tickers: list[str]) -> dict:
    """
    Returns current price, day change $, and day change % for each ticker.

    Args:
        tickers: list of ticker symbols, e.g. ['MU', 'AMD', 'NVDA']

    Returns:
        {
            'MU': {'price': 94.21, 'change_dollar': -1.43, 'change_pct': -1.49},
            ...
        }
    """
    results = {}

    for symbol in tickers:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info

            price = round(info.last_price, 2)
            prev_close = round(info.previous_close, 2)
            change_dollar = round(price - prev_close, 2)
            change_pct = round((change_dollar / prev_close) * 100, 2)

            results[symbol] = {
                "price": price,
                "change_dollar": change_dollar,
                "change_pct": change_pct,
            }
        except Exception as e:
            results[symbol] = {"error": str(e)}

    return results


if __name__ == "__main__":
    watchlist = ["MU", "AMD", "NVDA", "QCOM", "MSFT"]
    data = get_market_data(watchlist)

    print(f"\n{'Ticker':<8} {'Price':>8} {'Change $':>10} {'Change %':>10}")
    print("-" * 40)
    for symbol, d in data.items():
        if "error" in d:
            print(f"{symbol:<8}  ERROR: {d['error']}")
        else:
            arrow = "+" if d["change_dollar"] >= 0 else ""
            print(
                f"{symbol:<8} ${d['price']:>7.2f} "
                f"{arrow}{d['change_dollar']:>+9.2f} "
                f"{arrow}{d['change_pct']:>+9.2f}%"
            )
    print()
