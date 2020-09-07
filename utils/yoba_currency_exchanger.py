import aiohttp
import asyncio
import re
from decimal import Decimal


class CurrencyExchanger:
    api_key = '9c8736a2c2fb0f26f7bd448155798db6'
    url = f'http://data.fixer.io/api/latest?access_key={api_key}'
    cur_list = ['AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN', 'BAM', 'BBD', 'BDT', 'BGN', 'BHD',
                'BIF',
                'BMD', 'BND', 'BOB', 'BRL', 'BSD', 'BTC', 'BTN', 'BWP', 'BYN', 'BYR', 'BZD', 'CAD', 'CDF', 'CHF', 'CLF',
                'CLP',
                'CNY', 'COP', 'CRC', 'CUC', 'CUP', 'CVE', 'CZK', 'DJF', 'DKK', 'DOP', 'DZD', 'EGP', 'ERN', 'ETB', 'EUR',
                'FJD',
                'FKP', 'GBP', 'GEL', 'GGP', 'GHS', 'GIP', 'GMD', 'GNF', 'GTQ', 'GYD', 'HKD', 'HNL', 'HRK', 'HTG', 'HUF',
                'IDR',
                'ILS', 'IMP', 'INR', 'IQD', 'IRR', 'ISK', 'JEP', 'JMD', 'JOD', 'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW',
                'KRW',
                'KWD', 'KYD', 'KZT', 'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LTL', 'LVL', 'LYD', 'MAD', 'MDL', 'MGA', 'MKD',
                'MMK',
                'MNT', 'MOP', 'MRO', 'MUR', 'MVR', 'MWK', 'MXN', 'MYR', 'MZN', 'NAD', 'NGN', 'NIO', 'NOK', 'NPR', 'NZD',
                'OMR',
                'PAB', 'PEN', 'PGK', 'PHP', 'PKR', 'PLN', 'PYG', 'QAR', 'RON', 'RSD', 'RUB', 'RWF', 'SAR', 'SBD', 'SCR',
                'SDG',
                'SEK', 'SGD', 'SHP', 'SLL', 'SOS', 'SRD', 'STD', 'SVC', 'SYP', 'SZL', 'THB', 'TJS', 'TMT', 'TND', 'TOP',
                'TRY',
                'TTD', 'TWD', 'TZS', 'UAH', 'UGX', 'USD', 'UYU', 'UZS', 'VEF', 'VND', 'VUV', 'WST', 'XAF', 'XAG', 'XAU',
                'XCD',
                'XDR', 'XOF', 'XPF', 'YER', 'ZAR', 'ZMK', 'ZMW', 'ZWL']

    @classmethod
    async def get_rates(cls) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{cls.url}') as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise ConnectionError

    @classmethod
    async def exchange(cls, string: str) -> str:
        try:
            value = re.search(r'\d+', string)[0]
            cur_list = string.split('/')
            from_cur = cur_list[0][-3:].upper()
            to_cur = cur_list[1][0:3].upper()
        except:
            return 'не правильный ввод'

        if not (from_cur in cls.cur_list and to_cur in cls.cur_list):
            return 'такой валюты нету в апи'

        data = await cls.get_rates()
        rate = data['rates']
        if from_cur != 'EUR':
            eur = Decimal(value) / Decimal(rate[from_cur])
            if to_cur == 'EUR':
                return f'{value} {from_cur} = {round(eur, 2)} {to_cur}'
            result = eur * Decimal(rate[to_cur])
            return f'{value} {from_cur} = {round(result,2)} {to_cur}'
        else:
            result = Decimal(value) * Decimal(rate[to_cur])
            return f'{value} {from_cur} = {round(result,2)} {to_cur}'


# async def main():
#     print('пример: 100 RUB/USD')
#     while True:
#         string = input()
#         # string = '100 EUR/USD'
#         res = await CurrencyExchanger.exchange(string)
#         print(res)
#
#
# asyncio.run(main())
