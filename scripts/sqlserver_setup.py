import os
import time
import pyodbc

password = os.environ["SQLSERVER_TEST_PASSWORD"].replace("}", "}}")
for attempt in range(30):
    try:
        connection = pyodbc.connect("DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;UID=sa;PWD={" + password + "};TrustServerCertificate=yes", autocommit=True)
        connection.execute("IF DB_ID('servicestock_test') IS NULL CREATE DATABASE servicestock_test")
        connection.close()
        break
    except pyodbc.OperationalError:
        if attempt == 29:
            raise RuntimeError("SQL Server did not become ready") from None
        time.sleep(2)
