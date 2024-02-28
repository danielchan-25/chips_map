import time as sleep
from datetime import datetime, time, date
import chinese_calendar as calendar
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import json

# ----------------------- #
# Date: 2024-02-02
# Author: AlexChing
# Function: Chips Map
# ----------------------- #

current_datetime = datetime.now()
formatted_today_date = current_datetime.strftime('%Y%m%d')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()


# 判断是否为交易日
def is_workday(today):
    today = datetime.strptime(today, '%Y-%m-%d').date()
    is_workday = calendar.is_workday(today)
    return is_workday


# 获取最新的分钟数据，以 000001 或 399106 为例
def get_new_data(stock_code):
    logger.info(f'正在获取{stock_code}今日数据...')
    if stock_code == '000001':
        url_stock = '1.000001'
    elif stock_code == '399106':
        url_stock = '0.399106'

    url = f'secid={url_stock}' \
          f'klt=1&fqt=1&beg={formatted_today_date}&end={formatted_today_date}&lmt=50000&_=1584429841395'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
    }
    response = requests.get(url=url, headers=headers).text
    json_data = json.loads(response)['data']['klines']

    data_list = []

    for i in json_data:
        data = i.split(',', -1)
        datatime = data[0]  # 当前时间
        high_price = int(float(data[3]))  # 最高价
        low_price = int(float(data[4]))  # 最低价
        vol_price = float(data[5])  # 成交量
        close_price = int(float(data[2]))  # 收盘价

        data_list.append({
            'datatime': datatime,
            'closePrice': close_price,
            'highestPrice': high_price,
            'lowestPrice': low_price,
            'volume': vol_price
        })

    df = pd.DataFrame(data_list).reset_index(drop=True)
    return df


# 获取历史数据
def get_history_data(stock_code, row_sum):
    logger.info(f'正在获取{stock_code}历史数据...')
    if stock_code == '000001':
        csv_file = '000001_上证指数_1.csv'
    elif stock_code == '399106':
        csv_file = '399106_深证综指_1.csv'

    # 获取历史数据，创建价格区间
    df = pd.read_csv(csv_file).iloc[-row_sum:] 
    old_high_data = np.ceil(df['highestPrice'].max())
    old_low_data = np.floor(df['lowestPrice'].min())
    old_bins_list = np.arange(old_low_data, old_high_data + 1, 1)

    # 生成价格区间列表
    new_bins = []
    for k, i in enumerate(old_bins_list[:-1]):
        new_bins.append([old_bins_list[k], old_bins_list[k + 1]])

    min_high_data = df['highestPrice'].astype(int).astype(float).values.tolist()
    min_low_data = df['lowestPrice'].astype(int).astype(float).values.tolist()
    df['volume'] = np.array(df['volume'].astype(float).values.tolist()) / np.array(
        (np.array(min_high_data) - np.array(min_low_data)) + 1)  # 计算每份要摊的量，成交量 / (最高-最低)+1

    new_bins = [[i, 0] for i in new_bins]  # 生成列表：区间+成交量

    for index, row in df.iterrows():
        for l in new_bins:
            if l[0][0] <= row['closePrice'] < l[0][1]:
                l[1] += row['volume']
    return new_bins, old_high_data, old_low_data


# 合并数据
def merge_data(stock_code, row_sum):
    new_df = get_new_data(stock_code=stock_code)
    new_bins, old_high_data, old_low_data = get_history_data(stock_code=stock_code, row_sum=row_sum)
    new_high = new_df['highestPrice'].max()
    new_low = new_df['lowestPrice'].min()
    now_close = new_df['closePrice'].iloc[-1]

    # 如果最新数据有新高或新低，那就在数组头部或尾部插入价格区间
    if new_high > old_high_data:
        difference = np.ceil(new_high - old_high_data)
        for _ in range(int(difference)):
            new_bins.append([[new_bins[-1][0][1], new_bins[-1][0][1] + 1], 0])
    if new_low < old_low_data:
        difference = np.ceil(old_low_data - new_low)
        for _ in range(int(difference)):
            new_bins.insert(0, [[new_bins[0][0][0] - 1, new_bins[0][0][0]], 0])
    for index, row in new_df.iterrows():
        for l in new_bins:
            if l[0][0] <= row['closePrice'] < l[0][1]:  # 新增最新一分钟后的区间
                l[1] += row['volume']
    return new_bins, now_close


# 画图
def plot_data(stock_code, row_sum):
    if row_sum == 960:
        day_sum = 5
    elif row_sum == 4560:
        day_sum = 20

    new_bins, now_close = merge_data(stock_code=stock_code, row_sum=row_sum)

    x = [i[0][1] for i in new_bins]
    y = [i[1] for i in new_bins]
    colors = ['green' if int(close) > int(now_close) else 'red' for close in x]  # 红绿颜色区分获利盘和套牢盘
    plt.barh(x, y, color=colors)
    plt.axhline(y=int(now_close), color='black', linestyle='--', linewidth=2)  # 当前价格，用于画分割线
    plt.title(f'{stock_code}_{day_sum}d')
    plt.savefig(f'static\\{stock_code}_{day_sum}d.jpg')
    plt.close()
    logger.info(f'正在生成{stock_code}_{day_sum}d')
    # plt.show()


while True:
    today = datetime.today().strftime('%Y-%m-%d')
    day = datetime.today().strftime('%Y%m%d')
    now_time = datetime.now()

    logger.info(f'正在检测今天是否为交易日...')

    if is_workday(today=today) is True:
        logger.info(f'今天为交易日,正在检测当前时间...')

        if time(9, 30) <= time(now_time.hour, now_time.minute) < time(15, 0):
            logger.info(f'当前为开盘时间, 正在生成最新图片')
            stock_code_list = ['000001','399106']
            row_sum = [960, 4560]
            for i in stock_code_list:
                for j in row_sum:
                    plot_data(stock_code=i, row_sum=j)

            img1 = plt.imread("static\\000001_5d.jpg")
            img2 = plt.imread("static\\000001_20d.jpg")
            img3 = plt.imread("static\\399106_5d.jpg")
            img4 = plt.imread("static\\399106_20d.jpg")
            fig, axes = plt.subplots(2, 2, figsize=(10, 10))

            axes[0, 0].imshow(img1)
            axes[0, 0].axis('off')
            axes[0, 1].imshow(img2)
            axes[0, 1].axis('off')
            axes[1, 0].imshow(img3)
            axes[1, 0].axis('off')
            axes[1, 1].imshow(img4)
            axes[1, 1].axis('off')

            plt.tight_layout()
            plt.savefig(r'static\\main.jpg', dpi=300)
            plt.close()
            logger.info('正在合并图片...')
        else:
            logger.info(f'已收盘,等待下个交易日...')
    else:
        logger.info(f'今天为休息日,等待下个交易日运行...')
    sleep.sleep(60)
