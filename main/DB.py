from sqlalchemy import create_engine
import pymysql
pymysql.install_as_MySQLdb()
import pandas as pd

class StockDB(object):
    # 싱글톤 패턴
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            return cls._instance
        return cls._instance


    def init(self, password):
        if self._create_database(password) is False:
            return False
        self.engine = create_engine("mysql+mysqldb://root:"+password+"@localhost/stock", encoding='utf-8')
        self.conn = pymysql.connect(host='localhost', user='root', password=password, db='stock', charset='utf8')
        self.cursor = self.conn.cursor()
        return True

    def _create_database(self,password):
        try:
            conn = pymysql.connect(host='localhost', user='root', password=password, charset='utf8')
            cursor = conn.cursor()
            sql = 'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = \'stock\''
            result = cursor.execute(sql)

            if result == 0:
                sql = 'CREATE DATABASE stock'
                cursor.execute(sql)
                conn.commit()
        except:
            return False
        return True


    def close(self):
        self.conn.close()

    def select_max_date(self,table_name):
        sql = 'select max(Date) from ' + table_name
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    def select_min_date(self,table_name):
        sql = 'select min(Date) from ' + table_name
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    # 0 리턴 : 데이터 없음 , 1 리턴 : 데이터 있음
    def exist_data(self, table_name):
        sql = 'select exists (select * from '+table_name+')'
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    # 0 리턴 : 데이터 없음 , 1 리턴 : 데이터 있음
    def exist_profit_by_slip_scope(self, table_name, slip, scope):
        sql = 'select exists (select * from '+table_name+' where Slip='+str(slip)+' and Scope='+str(scope)+')'
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    def insert_data(self,data, table_name):
        data.to_sql(name=table_name, con=self.engine, if_exists='append')
        self.conn.commit()

    def select_data_by_date(self,table_name,start, end):
        data = pd.read_sql('select * from '+table_name+' where \''+start+'\'<= Date and Date <= \''+end+'\''
                           , self.conn, index_col='Date')
        return data

    def select_data_by_start(self,table_name,start):
        data = pd.read_sql('select * from '+table_name+' where \''+start+'\'<= Date '
                           , self.conn, index_col='Date')
        return data

    def select_profit_by_date(self,table_name,start, end, scope, slip):
        data = pd.read_sql('select Date, Profit from '+table_name+' where \''+start+'\'<= Date '
                                        'and Date <= \''+end+'\' and Scope='+str(scope)+" and Slip="+str(slip)
                           , self.conn, index_col='Date')
        return data

    def select_stock_by_profit_data(self,table_name, start, scope, slip):
        data = pd.read_sql('select * from '+ table_name+' where \''+start+'\'<=Date and '
                            'Date <= ( select min(Date) from '+table_name+'_profit '
                             'where Slip='+str(slip)+' and Scope='+str(scope)+')'
                           ,self.conn, index_col='Date')
        if data.empty == True:
            date_standard = None
        else:
            date_standard = data.index[-1]
        data = data.append(pd.read_sql('select * from '+ table_name+' where '
                            'Date > ( select max(Date) from '+table_name+'_profit '
                             'where Slip='+str(slip)+' and Scope='+str(scope)+')'
                           ,self.conn, index_col='Date'))
        return [date_standard, data]

    def create_stock_table(self,table_name):
        sql = 'SHOW TABLES LIKE \'' + table_name + '\''
        result = self.cursor.execute(sql)
        if result == 0:
            sql = 'create table ' + table_name + '(Date date primary key,Open Decimal,High Decimal,Low Decimal,Close Decimal, Volume Decimal);'
            self.cursor.execute(sql)
            self.conn.commit()

    def create_profit_table(self, table_name):
        sql = 'SHOW TABLES LIKE \'' + table_name + '\''
        result = self.cursor.execute(sql)
        if result == 0:
            sql = 'create table '+table_name+'(Scope decimal(2,1) , Date date, Profit decimal(5,4), Slip decimal(5,4), primary key(Scope, Date,Profit));'
            self.cursor.execute(sql)
            self.conn.commit()
