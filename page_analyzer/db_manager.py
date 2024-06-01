import psycopg2


class TableManager:
    def __init__(self, database_url, table, table_descr):
        self.conn = psycopg2.connect(database_url)
        self.table = table
        self.table_descr = table_descr

    def _execute_query(self, query, values=None, fetchone=False, insert=False):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                if insert:
                    self.conn.commit()
                    return None
                if fetchone:
                    return cur.fetchone()
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
        fields='',
        search_field='',
        reverse=False,
        insert=False,
    ) -> str:
        query_templates = {
            'select': f'SELECT {fields} FROM {self.table}' if fields else '',
            'where': f'WHERE {search_field} = %s' if search_field else '',
            'reverse': 'ORDER BY id DESC' if reverse else '',
            'insert': f'INSERT INTO {self.table} '
            f'({", ".join(self.table_descr)}) VALUES %s' if insert else '',
        }

        query_list = [value for value in query_templates.values() if value]
        query = ' '.join(query_list)
        return query

    def get_one(self, search_field, search_value, **kwargs):
        query = self._query_constructor(search_field=search_field, **kwargs)
        return self._execute_query(query, (search_value,), fetchone=True)

    def get_many(self, search_field, search_value, **kwargs):
        query = self._query_constructor(search_field=search_field, **kwargs)
        return self._execute_query(query, (search_value,))

    def get_all(self):
        query = self._query_constructor(fields='*')
        return self._execute_query(query)

    def insert(self, *value):
        query = self._query_constructor(insert=True)
        self._execute_query(query, (value,), insert=True)
        self.conn.commit()
