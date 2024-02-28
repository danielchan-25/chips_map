import chinese_calendar as calendar
import requests
import json
from datetime import datetime
import time
import logging
import pandas as pd

# ---------------------------------------------------------- #
# Date：2024-02-19
# Author: AlexChing
# Function：Get Data
# ---------------------------------------------------------- #

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()
logger.info('''此程序功能为：爬取东方财富的当天指数数据，时间周期为：1min''')
logger.info('''1.000001, 0.399106''')

# 检测是否为交易日
def is_workday(today):
    today = datetime.strptime(today, '%Y-%m-%d').date()
    is_workday = calendar.is_workday(today)
    return is_workday

def main(klt, day):
    secids = ['1.000001', '0.399106']

    for i in secids:
        url = f'secid={i}&klt={klt}&fqt=1&beg={day}&end={day}&lmt=50000&_=1584429841395'  # URL地址
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
        response = requests.get(url=url, headers=headers).text
        json_data = json.loads(response)

        index_code = json_data['data']['code']
        index_name = json_data['data']['name']
        file_name = f'{index_code}_{index_name}_{klt}.csv'

        input_data = []
        for i in json_data['data']['klines']:
            data = i.split(',', -1)
            datatime = data[0]  # 当前时间
            open_price = data[1]  # 开盘价
            close_price = data[2]  # 收盘价
            high_price = data[3]  # 最高价
            low_price = data[4]  # 最低价
            vol_price = data[5]  # 成交量
            value_price = data[6]  # 成交额
            zf = data[7]  # 振幅

            input_data.append({
                'datatime': datatime,
                'open_price': open_price,
                'close_price': close_price,
                'high_price': high_price,
                'low_price': low_price,
                'vol_price': vol_price,
                'value_price': value_price,
                'zf': zf
            })

        df = pd.DataFrame(input_data).reset_index(drop=True)
        df.to_csv(file_name, index=False, mode='a', header=False)
        logger.info(f'已写入{len(df)}条数据')


if __name__ == '__main__':
    while True:
        today = datetime.today().strftime('%Y-%m-%d')
        day = datetime.today().strftime('%Y%m%d')
        now_time = datetime.now()

        if is_workday(today=today) is True:
            if now_time.hour == 15 and now_time.minute == 35:
                main(klt=1, day=day)
                time.sleep(60)
                logger.info(f'{today}程序执行完毕.')
