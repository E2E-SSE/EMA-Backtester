import os
import sys
import time
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
plt.style.use("ggplot")


def fetchPrice(ticker, start_date, time_interval, mav1, mav2):
    df = yf.download(tickers=ticker, start=start_date, interval=time_interval,
                     auto_adjust=True, progress=False).reset_index()
    if df.empty:
        print("Exiting")
        sys.exit()

    df[f"EMA{mav1}"] = df.Close.ewm(span=mav1, adjust=False).mean()
    df[f"EMA{mav2}"] = df.Close.ewm(span=mav2, adjust=False).mean()
    return df


def emaCross(df, mav1, mav2, initial_investment, asset):
    buy_signal = []
    sell_signal = []
    percent_change = []

    profits = []
    profit_dates = []
    position = False

    IC = initial_investment

    for i in range(0, len(df.index)):

        close = df.Close[i]
        date = df.iloc[:, 0][i]  # grabbing date column

        if df[f"EMA{mav1}"][i] > df[f"EMA{mav2}"][i] and position is False:

            buy_price = close
            buy_signal.append(buy_price)
            sell_signal.append(np.nan)

            qty_shares = initial_investment / buy_price
            buy_value = buy_price * qty_shares

            print(f"BUYING AT {buy_price} - {date}")
            position = True

        elif df[f"EMA{mav1}"][i] < df[f"EMA{mav2}"][i] and position is True:

            sell_price = close
            sell_signal.append(sell_price)
            buy_signal.append(np.nan)

            sell_value = (sell_price * qty_shares)
            profit = round(float(sell_value - buy_value), 2)
            profits.append(profit)
            profit_dates.append(date)
            initial_investment = initial_investment + profit

            change = (sell_price / buy_price - 1) * 100
            percent_change.append(change)

            print(f"SELLING AT {sell_price} - {date} \n")
            position = False

        else:
            buy_signal.append(np.nan)
            sell_signal.append(np.nan)

    df["Buy"] = buy_signal
    df["Sell"] = sell_signal

    df_trades = pd.DataFrame([(profits, profit_dates) for profits, profit_dates in zip(profits, profit_dates)],
                             columns=["Profit", "Date"])

    gains = 0
    number_gain = 0
    losses = 0
    number_loss = 0
    total_return = 1

    for i in percent_change:

        if i > 0:
            gains += i
            number_gain += 1

        else:
            losses += i
            number_loss += 1

        total_return = total_return * ((i / 100) + 1)

    total_return = round((total_return - 1) * 100, 2)

    if number_gain > 0:
        avg_gain = gains / number_gain
        max_return = str(max(percent_change))

    else:
        avg_gain = 0
        max_return = "undefined"

    if number_loss > 0:
        avg_loss = losses / number_loss
        max_loss = str(min(percent_change))
        ratio = str(-avg_gain / avg_loss)

    else:
        avg_loss = 0
        max_loss = "undefined"
        ratio = "inf"

    if number_gain > 0 or number_loss > 0:
        batting_avg = number_gain / (number_gain + number_loss)

    else:
        batting_avg = 0

    ASSET           = f"ASSET:           {asset}"
    DATE_RANGE      = f"DATE_RANGE:      {str(df.iloc[:, 0].iloc[0])} - {str(df.iloc[:, 0].iloc[-1])}"
    SAMPLE_SIZE     = f"SAMPLE_SIZE:     {number_gain + number_loss} TRADES"
    BATTING_AVG     = f"BATTING_AVG:     {batting_avg}"
    GAIN_LOSS_RATIO = f"GAIN_LOSS_RATIO: {ratio}"
    AVERAGE_GAIN    = f"AVERAGE_GAIN:    {avg_gain}"
    AVERAGE_LOSS    = f"AVERAGE_LOSS:    {avg_loss}"
    MAX_RETURN      = f"MAX_RETURN:      {max_return}"
    MAX_LOSS        = f"MAX_LOSS:        {max_loss}"
    TOTAL_RETURN    = f"TOTAL_RETURN:    {total_return}%"
    INITIAL_CAPITAL = f"INITIAL_CAPITAL: ${IC:,.2f}"
    TOTAL_PNL       = f"TOTAL_PNL:       ${df_trades['Profit'].sum()+IC:,.2f} : +${round(df_trades['Profit'].sum(), 2):,.2f} "
    BEST_TRADE      = f"BEST_TRADE:      ${df_trades.max()['Profit']:,.2f} : {df_trades.max()['Date']}"
    WORST_TRADE     = f"WORST_TRADE:     ${df_trades.min()['Profit']:,.2f} : {df_trades.min()['Date']}"

    details = (ASSET, DATE_RANGE, SAMPLE_SIZE, BATTING_AVG, GAIN_LOSS_RATIO,
               AVERAGE_GAIN, AVERAGE_LOSS, MAX_RETURN, MAX_LOSS, TOTAL_RETURN,
               INITIAL_CAPITAL, TOTAL_PNL, BEST_TRADE, WORST_TRADE)

    info = (
        "{}\n"
        "{}\n"
        "{}\n"
        "{}\n"
        "{}\n"
        "{}\n"
        "{}\n"
        "{}\n"
        "{}\n"
        "{}\n\n"
        "{}\n"
        "{}\n"
        "{}\n"
        "{}\n"  # 14 Total
    ).format(*details)
    print(info)
    return df

# df, change = emaCross(fetchPrice("ETH-USD", "2022-01-01", "1d", 13, 21), 13, 21)
# calcTrades(df, change)


def plotAndSave(df, file_path, asset, mav1, mav2):

    fig, (ax1) = plt.subplots(nrows=1)

    ax1.plot(df.iloc[:, 0], df.Close, color="red")
    ax1.plot(df.iloc[:, 0], df[f"EMA{mav1}"], color="orange", alpha=0.35, label=f"EMA{mav1}")
    ax1.plot(df.iloc[:, 0], df[f"EMA{mav2}"], color="yellow", alpha=0.35, label=f"EMA{mav2}")
    ax1.plot(df.iloc[:, 0], df["Buy"], color="green", marker="^", alpha=1)
    ax1.plot(df.iloc[:, 0], df["Sell"], color="red", marker="v", alpha=1)

    plt.tight_layout()
    plt.legend()
    plt.title(f"{asset} Close Price | {str(df.iloc[:, 0].iloc[0])} - {str(df.iloc[:, 0].iloc[-1])}|")
    plt.savefig(f"{file_path}{asset}_EMACROSS_{pd.to_datetime(time.time(), unit='s')}.png")
    plt.show()


def main():

    ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
    BO_PATH = os.path.join(ROOT_PATH, "BacktestOutput")
    if not os.path.exists(BO_PATH):
        os.mkdir(BO_PATH)
        print("Directory '%s' created" % BO_PATH)
    else:
        pass

    ticker = input("Enter an asset ticker symbol eg (AAPL ES=F BTC-USD): ")
    interval = input("Enter one of the following intervals (1m 5m 15m 30m 60m 1d): ")
    start = input("Enter a starting date (YYYY-MM-DD): ")
    ma1 = int(input("Enter your fast/short EMA (number): "))
    ma2 = int(input("Enter your slow/long  EMA (number): "))
    initial_capital = float(input("Enter your starting capital (number): $"))

    print(f"STARTING TEST FOR {ticker} \n\n")

    frame = emaCross(fetchPrice(
        ticker=ticker,
        time_interval=interval,
        start_date=start,
        mav1=ma1,
        mav2=ma2
    ),
        mav1=ma1,
        mav2=ma2,
        initial_investment=initial_capital,
        asset=ticker)

    plotAndSave(df=frame, file_path=BO_PATH, asset=ticker, mav1=ma1, mav2=ma2)


main()

