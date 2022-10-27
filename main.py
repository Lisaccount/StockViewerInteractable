# -*- coding: utf-8 -*-
# @Author  : bedeyoux@gmail.com
# @Time    : 2022/10/27 下午4:54
# @Function: Candle chart visualization Input ohlc data Output Visualize results, drag and drop, and switch candles on
#            different time scales
import pandas as pd

from candlestick import CandlestickServer


def get_data():
    x = ['date', '_time', 'open', 'high', 'low', 'close', 'volume']
    dataframe = pd.read_csv('data/DAT_MT_XAUUSD_M1_2021.csv', header=None)
    dataframe.columns = x
    dataframe.index = pd.to_datetime(dataframe['date'] + ' ' + dataframe['_time'])
    return dataframe


def main():
    CandlestickServer(get_data())


if __name__ == '__main__':
    main()
