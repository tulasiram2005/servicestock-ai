import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('sql_setup', Path(__file__).resolve().parents[2]/'scripts/sqlserver_setup.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class DriverError(Exception):
    pass


def test_bounded_retries_do_not_disclose_driver_error():
    calls = []
    waits = []
    def connect(value, **options):
        calls.append(options)
        assert 'SERVER=127.0.0.1,1433' in value
        raise DriverError('08001', 'private-password should never appear')
    with pytest.raises(RuntimeError) as error:
        module.prepare(connect, DriverError, 'private-password', sleep=waits.append, attempts=3)
    assert str(error.value) == 'SQL Server readiness failed; SQLSTATE=08001'
    assert calls == [{'autocommit':True,'timeout':3}]*3
    assert waits == [2,2]


def test_success_closes_connection_and_escapes_password():
    class Connection:
        closed = False
        def execute(self, statement):
            assert 'servicestock_test' in statement
        def close(self):
            self.closed = True
    connection = Connection()
    def connect(value, **options):
        assert 'PWD={test}}secret}' in value
        return connection
    module.prepare(connect, DriverError, 'test}secret')
    assert connection.closed
    assert connection.timeout == 5
