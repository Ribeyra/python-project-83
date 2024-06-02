import psycopg2


class TableManager:
    def __init__(self, database_url, table, table_descr):
        self.conn = psycopg2.connect(database_url)
        self.table = table
        self.table_descr = table_descr

    def _execute_query(self, query):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            print(f"Query failed: {e}")
            raise e

    def get(self, query):
        return self._execute_query(query)

    def close_conn(self):
        self.conn.close()

    def __del__(self):
        self.close_conn()


class TableManagerWithConstructor(TableManager):
    def _query_constructor(
        self,
        *,
        select_columns='',
        search_column='',
        reverse=False,
        insert=False,
    ) -> str:
        query_templates = {
            'select': f'SELECT {select_columns} FROM '
            f'{self.table}' if select_columns else '',
            'where': f'WHERE {search_column} = %s' if search_column else '',
            'reverse': 'ORDER BY id DESC' if reverse else '',
            'insert': f'INSERT INTO {self.table} '
            f'({", ".join(self.table_descr)}) VALUES %s '
            'RETURNING id' if insert else '',
        }

        query_list = [value for value in query_templates.values() if value]
        query = ' '.join(query_list)
        return query

    def _execute_query(self, query, values=None, fetch_all=False):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                if fetch_all:
                    return cur.fetchall()
                return cur.fetchone()
        except Exception as e:
            self.conn.rollback()
            print(f"Query failed: {e}")
            raise e

    def get_one(self, search_column, search_value, **kwargs):
        query = self._query_constructor(search_column=search_column, **kwargs)
        return self._execute_query(query, (search_value,))

    def get_many(self, search_column, search_value, **kwargs):
        query = self._query_constructor(search_column=search_column, **kwargs)
        return self._execute_query(query, (search_value,), fetch_all=True)

    def get_all(self):
        query = self._query_constructor(select_columns='*')
        return self._execute_query(query, fetch_all=True)

    def insert(self, *value):
        """
        Add value in table and return row id
        """
        query = self._query_constructor(insert=True)
        id = self._execute_query(query, (value,))
        self.conn.commit()
        return id[0]
