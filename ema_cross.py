import os
import time
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
plt.style.use("seaborn-dark")


def fetchPrice(ticker, start_date, interval, mav1, mav2):
    df = yf.download(tickers=ticker, start=start_date, interval=interval,
                     auto_adjust=True, progress=False)

    df[f"EMA{mav1}"] = df.Close.ewm(span=mav1, adjust=False).mean()
    df[f"EMA{mav2}"] = df.Close.ewm(span=mav2, adjust=False).mean()
    return df


def emaCross(df, mav1, mav2):
    buy_signal = []
    sell_signal = []
    percent_change = []
    position = False

    for i in range(0, len(df.index)):

        close = df.Close[i]
        date = df.index[i]

        if df[f"EMA{mav1}"][i] > df[f"EMA{mav2}"][i] and position == False:

            buy_price = close
            buy_signal.append(buy_price)
            sell_signal.append(np.nan)
            print(f"BUYING AT {buy_price} - {date}")
            position = True

        elif df[f"EMA{mav1}"][i] < df[f"EMA{mav2}"][i] and position == True:

            sell_price = close
            sell_signal.append(sell_price)
            buy_signal.append(np.nan)
            print(f"SELLING AT {sell_price} - {date} \n")
            position = False

            change = (sell_price / buy_price - 1) * 100
            percent_change.append(change)

        else:
            buy_signal.append(np.nan)
            sell_signal.append(np.nan)

    df["Buy"] = buy_signal
    df["Sell"] = sell_signal

    return df, percent_change


def calcTrades(df, change):

    gains = 0
    number_gain = 0
    losses = 0
    number_loss = 0
    total_return = 1

    for i in change:

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
        max_return = str(max(change))

    else:
        avg_gain = 0
        max_return = "undefined"

    if number_loss > 0:
        avg_loss = losses / number_loss
        max_loss = str(min(change))
        ratio = str(-avg_gain / avg_loss)

    else:
        avg_loss = 0
        max_loss = "undefined"
        ratio = "inf"

    if number_gain > 0 or number_loss > 0:
        batting_avg = number_gain / (number_gain + number_loss)

    else:
        batting_avg = 0

    print(f"STARTING DATE:     {str(df.index[0])} \n"
          f"SAMPLE SIZE:       {number_gain+number_loss} TRADES \n"
          f"BATTING AVG:       {batting_avg} \n"
          f"GAIN/LOSS RATIO:   {ratio} \n"
          f"AVERAGE GAIN:      {avg_gain} \n"
          f"AVERAGE LOSS:      {avg_loss} \n"
          f"MAX RETURN:        {max_return} \n"
          f"MAX LOSS:          {max_loss} \n"
          f"TOTAL RETURN:      {total_return}% \n")


# df, change = emaCross(fetchPrice("ETH-USD", "2022-01-01", "1d", 13, 21), 13, 21)
# calcTrades(df, change)

def plotAndSave(df, file_path, asset, mav1, mav2):

    plt.plot(df.index, df.Close, color="red")
    plt.plot(df[f"EMA{mav1}"], color="orange", alpha=0.35, label=f"EMA{mav1}")
    plt.plot(df[f"EMA{mav2}"], color="yellow", alpha=0.35, label=f"EMA{mav2}")

    plt.plot(df.index, df["Buy"], color="green", marker="^", alpha=1)
    plt.plot(df.index, df["Sell"], color="red", marker="v", alpha=1)

    plt.tight_layout()
    plt.legend()
    plt.savefig(f"{file_path}{asset}_EMACROSS_{pd.to_datetime(time.time(), unit='s')}.png")
    plt.show()


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
BO_PATH = ROOT_PATH+"/BacktestOutput/"

assets = ["ETH-USD", "BTC-USD", "UNI1-USD", "CRO-USD"]
interval = "1m"
start = "2022-10-10"

ma1 = 34
ma2 = 55

for asset in assets:

    print(f"STARTING TEST FOR {asset} \n\n")

    frame, pc_change = emaCross(fetchPrice(
        ticker=asset,
        interval=interval,
        start_date=start,
        mav1=ma1,
        mav2=ma2
    ),
        mav1=ma1,
        mav2=ma2)

    calcTrades(frame, change=pc_change)
    plotAndSave(frame, BO_PATH, asset, ma1, ma2)
