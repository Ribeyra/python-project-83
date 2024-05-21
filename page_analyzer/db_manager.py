import psycopg2


class DatabaseManager:
    def __init__(self, database_url, table, table_descr):
        self.database_url = database_url
        self.table = table
        self.table_descr = table_descr

    def _query_constructor(
        self,
        *,
        fields='*',
        search_field='',
        reverse=False,
        **kwargs
    ) -> str:

        query_templates = {
            'select': f'SELECT {fields} FROM {self.table}',
            'where': f'WHERE {search_field} = %s' if search_field else '',
            'reverse': 'ORDER BY id DESC' if reverse else ''
        }

        query_list = [value for value in query_templates.values() if value]

        query = ' '.join(query_list)
        return query

    def _read_db(self, *args, one=False, **kwargs):

        query = self._query_constructor(**kwargs)
        search_value = kwargs.get('search_value')

        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    if search_value:
                        cur.execute(query, (search_value,))
                    else:
                        cur.execute(query)
                    result = cur.fetchone() if one else cur.fetchall()
                    return result
        except (psycopg2.Error, Exception) as error:
            print("Error reading data from the database:", error)
            return None

    def _write_db(self, value):

        table = f'{self.table} ({", ".join(self.table_descr)})'
        query = f"INSERT INTO {table} VALUES %s"

        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (value,))
                    conn.commit()
        except (psycopg2.Error, Exception) as error:
            print("Error write data in the database:", error)
            raise

    def content(self, **kwargs):
        return self._read_db(**kwargs)

    def find(self, search_field, search_value, **kwargs):
        return self._read_db(
            search_field=search_field,
            search_value=search_value,
            **kwargs
        )

    def insert(self, *value):
        self._write_db(value)


class DBManagerForComplexQuery(DatabaseManager):
    def _query_constructor(*args, **kwargs):
        return kwargs['query']
