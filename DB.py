from mysql.connector import connect

from Config import Config


class DB:
    @staticmethod
    def connect():
        config = Config()
        connection_data = config.get('DataBase')
        result = connect(
            host=connection_data['host'],
            user=connection_data['user'],
            password=connection_data['pass'],
            database=connection_data['database_name']
        )

        return result

    @staticmethod
    def query(query_string, params=()):
        connection = DB.connect()
        if not connection == False:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute('SET session sql_mode=traditional')
                cursor.execute(query_string, params)
                result = cursor.fetchall()
            connection.close()
        else:
            result = False
        return result
