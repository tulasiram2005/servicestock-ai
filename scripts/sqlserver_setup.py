"""Create the isolated CI database with bounded, secret-safe readiness diagnostics."""
import os
import re
import time


def prepare(connect, operational_error, password, sleep=time.sleep, attempts=12):
    escaped = password.replace('}', '}}')
    connection_string = ('DRIVER={ODBC Driver 18 for SQL Server};SERVER=127.0.0.1,1433;'
                         'UID=sa;PWD={' + escaped + '};Encrypt=yes;TrustServerCertificate=yes')
    state = 'unknown'
    for attempt in range(attempts):
        try:
            connection = connect(connection_string, autocommit=True, timeout=3)
            try:
                connection.timeout = 5
                connection.execute("IF DB_ID('servicestock_test') IS NULL CREATE DATABASE servicestock_test")
            finally:
                connection.close()
            return
        except operational_error as error:
            # Only the standardized SQLSTATE, never driver text or connection values.
            candidate = str(error.args[0]) if error.args else ''
            state = candidate if re.fullmatch(r'[A-Z0-9]{5}', candidate) else 'unknown'
            if attempt < attempts - 1:
                sleep(2)
    raise RuntimeError('SQL Server readiness failed; SQLSTATE=' + state) from None


def main():
    import pyodbc
    from sqlalchemy.engine import URL
    password = os.environ['SQLSERVER_TEST_PASSWORD']
    prepare(pyodbc.connect, pyodbc.OperationalError, password)
    if os.getenv('GITHUB_ENV'):
        url = URL.create('mssql+pyodbc', username='sa', password=password,
            host='127.0.0.1', port=1433, database='servicestock_test',
            query={'driver': 'ODBC Driver 18 for SQL Server', 'TrustServerCertificate': 'yes'}
        ).render_as_string(hide_password=False)
        print('::add-mask::' + url)
        with open(os.environ['GITHUB_ENV'], 'a') as output:
            output.write('TEST_DATABASE_URL=' + url + '\nDATABASE_URL=' + url + '\n')


if __name__ == '__main__':
    main()
