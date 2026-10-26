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

# Derive both test and migration URLs from the same isolated database credentials.
# A separately configured URL could silently skip tests or target a different server.
if os.getenv("GITHUB_ENV"):
    from sqlalchemy.engine import URL
    url = URL.create("mssql+pyodbc", username="sa", password=os.environ["SQLSERVER_TEST_PASSWORD"],
        host="localhost", port=1433, database="servicestock_test",
        query={"driver":"ODBC Driver 18 for SQL Server", "TrustServerCertificate":"yes"}).render_as_string(hide_password=False)
    print("::add-mask::" + url)
    with open(os.environ["GITHUB_ENV"], "a") as output:
        output.write("TEST_DATABASE_URL=" + url + "\nDATABASE_URL=" + url + "\n")
