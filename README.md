# EMA crossover bot: the one that came first

> [!CAUTION]
> **This places live market orders. Do not run it.**
> `oanda_trade.py` opens with `API(access_token=..., environment="live")` and loops
> forever placing real `MARKET` orders on a real OANDA account. There is no dry-run
> flag, no position check, no error handling around the API call and no kill switch.
> It is kept here as a record, not as something to use. The repository is archived.

This is the first trading thing I built: an EMA(5/8) crossover on 1-minute EUR/USD,
long only, ATR-based stop, take-profit at 1.5× the stop distance, checked once a minute
forever.

I published it in June 2026 believing the idea was sound. It is here because of what
happened next.

---

## What happened next

I wanted to know whether the strategy actually made money, so I built
[**Back-Testing-Engine**](https://github.com/thirdbrew/Back-Testing-Engine), a bar-by-bar
backtester designed so lookahead bias is impossible by construction rather than by
remembering to avoid it, and so every fill pays half-spread, slippage and commission
charged *against* the trader.

Then I ran the same EMA(5/8) signal through it. Daily AAPL, 2013-02-08 to 2018-02-07,
1,259 bars, 118 trades:

| | Strategy | Buy and hold |
|---|---|---|
| Total return, after costs | **+6.73%** | **+134.32%** |
| Sharpe | 0.17 | 0.85 |
| Max drawdown | −42.97% | −32.08% |
| Win rate | 30.5% | n/a |

Gross of costs the strategy returned +11.95%. Costs took it to +6.73%, **roughly half
the return, consumed by trading**, at 46.6× annual turnover.

Those figures are not a claim in a README. They are pinned as golden values in
[`tests/test_reference.py`](https://github.com/thirdbrew/Back-Testing-Engine/blob/main/tests/test_reference.py)
and re-checked by CI on every push, so if the engine ever stops producing them, the
suite fails.

**Being precise about what that does and does not show:** it is daily AAPL, not 1-minute
EUR/USD, so it is not a backtest *of this bot*. What it establishes is that the signal is
weak and that at high turnover, costs decide the outcome. This bot trades a
one-minute timeframe, where turnover is far higher than 46.6× a year and the spread is
the dominant term, and the code below charges nothing for it at all. The direction of
that error is not ambiguous.

---

## What is wrong with the code

Worth naming, because "it lost money" is the least interesting part:

- **It never charges a spread.** On M1 EUR/USD that is the whole problem. It reads ask
  prices for its candles and then reasons about entries as if it could transact at the
  close it just observed.
- **Long only.** The `else` branch prints `"No crossover"` and returns. A downward cross
  is not a signal to exit or reverse. It does nothing. The only way out of a position is
  the stop or the take-profit.
- **No position management.** Nothing checks whether a position is already open before
  `place_order` fires, and nothing tracks what is live.
- **No error handling.** One network blip inside `client.request` and the loop dies
  silently, potentially with a position open.
- **Fixed 100 units** regardless of account size, volatility or the ATR it just computed
  for the stop.
- The signal is computed on completed candles only, which is the one thing it gets
  right: there is no lookahead in the entry logic.

---

## Why it is still here

My habit is to decide what "working" means before running the test, then report the
result against that bar. Publishing only the projects that passed would make that claim
unfalsifiable.

This is where the habit came from. I wrote the bot, then built the instrument that
could tell me whether the bot's idea held, and it did not. The engine was worth far more
than the strategy.

Archived and unmaintained. Nothing here should be traded.
