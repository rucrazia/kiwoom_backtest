import Kiwoom as kw
import DB as db
from datetime import date, timedelta
import pandas as pd


class MainFunctions():
    def __init__(self):
        self.ki = kw.Kiwoom()
        self.dB = db.StockDB()

        self.date = date.today() - timedelta(1)

    def db_login(self, password):
        return self.dB.init(password)

    def is_stock(self, code):
        if code == 'kospi' or code == 'kosdaq':
            return code
        stock_name = self.ki.is_stock(code)
        if stock_name is not "":
            return stock_name
        return None

    def get_stock_date_range(self, code):
        if code == 'kospi' or code == 'kosdaq':
            table_name = code
        else:
            table_name = 'a'+code
        min_date = self.dB.select_min_date(table_name)
        max_date = self.dB.select_max_date(table_name)
        return [min_date, max_date]

    def db_insert_stock(self, code):
        if code == 'kospi':
            table_name = code
            code = '001'

        elif code == 'kosdaq':
            table_name = code
            code = '101'

        else:
            table_name = 'a' + code

        # 테이블이 생성되지 않았으면 테이블 생성
        self.dB.create_stock_table(table_name)
        # 테이블에 입력된 데이터 중 가장 최근 날짜 획득
        recent_day = self.dB.select_max_date(table_name)
        if recent_day == self.date:
            return
        #  일봉 데이터 획득
        if code == '001' or code =='101':
            data = self.ki.req_index_daily_value(code, recent_day)
        else:
            data = self.ki.req_stock_daily_value(code, recent_day)
        # 테이블에 데이터 insert
        self.dB.insert_data(data, table_name)
        return True

    def backtesting(self,code,start, end, scopes, slip):
        if code == 'kospi' or code=='kosdaq':
            table_name = code
        else:
            table_name = 'a'+code

        buy_and_hold = self.buy_and_hold_profit(self.dB.select_data_by_date(table_name,start, end))
        profit_datas = pd.DataFrame(buy_and_hold['buy and hold'])

        for scope in scopes:
            # profit 테이블 생성
            self.dB.create_profit_table(table_name + "_profit")
            # profit 테이블 데이터 존재 유무 확인
            exist = self.dB.exist_profit_by_slip_scope(table_name + '_profit', slip, scope)

            # profit 테이블 데이터가 존재하지 않는다면 범위내 stock 전체 데이터 리턴
            # 존재한다면 profit 테이블 범위 외 stock 데이터 리턴
            if exist == 0:
                stock_data = self.dB.select_data_by_start(table_name, start)
                self.dB.insert_data(self.cal_profit(stock_data, scope, slip), table_name + '_profit')
            else:
                stock_datas = self.dB.select_stock_by_profit_data(table_name, start, scope, slip)
                date_standard = stock_datas[0]
                stock_data = stock_datas[1]

                # empty라면 DB예 profit 데이터 모두 존재
                if stock_data.empty is False:
                    # stock_datas[0] 이 None 아니라면 데이터를 분류해야함
                    if date_standard is None:
                        self.dB.insert_data(self.cal_profit(stock_data, scope, slip), table_name + '_profit')
                    else:
                        stock_data1 = stock_data[stock_data.index.values <= date_standard]
                        stock_data2 = stock_data[stock_data.index.values > date_standard]
                        self.dB.insert_data(self.cal_profit(stock_data1, scope, slip), table_name + '_profit')
                        self.dB.insert_data(self.cal_profit(stock_data2, scope, slip), table_name + '_profit')

            # DB에서 profit_data 획득 후 누적 수익률 계산
            column_name = 'Scope:' + str(scope)
            profit_data = self.cal_cul_profit(
                self.dB.select_profit_by_date(table_name + '_profit', start, end, scope, slip), column_name)

            # 최종 데이터로 추가
            profit_datas = profit_datas.merge(pd.DataFrame(profit_data[column_name]), how='outer', left_index=True,
                                                  right_index=True)
            profit_datas.index.name = 'Date'

        profit_datas = profit_datas.fillna(method='ffill')
        profit_datas = profit_datas.fillna(method='bfill')
        return profit_datas

    def cal_profit(self, data, scope, slip):
        data['Criteria'] = (data['High'] - data['Low']).shift(1) * scope + data['Open']
        data['buy'] = data['High'] >= data['Criteria']
        data['Next_Open'] = data['Open'].shift(-1)

        data = data[data['buy']]
        data = data.dropna(axis=0)
        data['Profit'] = round(data['Next_Open'] / data['Criteria'] - 1 - slip, 4)


        profit = pd.DataFrame({'Profit': data['Profit']})
        profit['Scope'] = scope
        profit['Slip'] = slip
        profit.index.name = 'Date'


        return profit

    def cal_cul_profit(self, data, column_name):
        data[column_name] = (data['Profit'] + 1).cumprod()
        return data

    # 종가 기준 buy_and_hold
    def buy_and_hold_profit(self, data):
        criteria = data['Close'][0]
        data['buy and hold'] = data['Close']/criteria
        return data