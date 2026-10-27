import importlib.util
from pathlib import Path
import stat
import pytest

spec = importlib.util.spec_from_file_location('gemini_setup', Path(__file__).resolve().parents[2] / 'scripts/configure_gemini.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
KEY = 'synthetic_test_key_never_a_real_secret'


def test_secret_file_is_private_and_existing_file_is_preserved(tmp_path):
    path = tmp_path / '.env.gemini'
    module.save_config(path, KEY, 'gemini-test-flash')
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        module.save_config(path, KEY, 'gemini-other-flash')
    assert path.read_bytes() == before


def test_symlink_and_dotenv_injection_are_rejected(tmp_path):
    target = tmp_path / 'existing'
    target.write_text('preserve')
    link = tmp_path / '.env.gemini'
    link.symlink_to(target)
    with pytest.raises(FileExistsError):
        module.save_config(link, KEY, 'gemini-test-flash')
    assert target.read_text() == 'preserve'
    for key, model in [(KEY+'\nINJECT=true', 'gemini-test-flash'), (KEY, 'gemini-flash\nINJECT=true')]:
        with pytest.raises(ValueError):
            module.save_config(tmp_path / 'absent', key, model)
    assert not (tmp_path / 'absent').exists()


def test_clipboard_whitespace_and_empty_input(tmp_path):
    path = tmp_path / '.env.gemini'
    module.save_config(path, ' \t'+KEY+'\r\n', 'gemini-test-flash')
    assert path.read_text().splitlines()[0] == 'GEMINI_API_KEY='+KEY
    with pytest.raises(ValueError, match='No key received'):
        module.save_config(tmp_path / 'empty', ' \n', 'gemini-test-flash')


@pytest.mark.parametrize('key, expected', [('', 'No key received'), ('...HRQQ', 'Key format not recognized')])
def test_terminal_error_is_actionable_and_does_not_print_input(monkeypatch, capsys, key, expected):
    monkeypatch.setattr(module.sys.stdin, 'isatty', lambda: True)
    answers = iter(['gemini-test-flash', 'yes'])
    monkeypatch.setattr('builtins.input', lambda _: next(answers))
    monkeypatch.setattr(module.getpass, 'getpass', lambda _: key)
    assert module.main() == 2
    output = capsys.readouterr().out
    assert expected in output
    if key:
        assert key not in output


def test_bracketed_paste_markers_are_removed(tmp_path):
    path = tmp_path / '.env.gemini'
    module.save_config(path, '\x1b[200~'+KEY+'\x1b[201~', 'gemini-test-flash')
    assert path.read_text().splitlines()[0] == 'GEMINI_API_KEY='+KEY


@pytest.mark.parametrize('key, reason', [
    ('short', 'fewer than 20'),
    ('x'*201, 'more than 200'),
    (KEY+' secret', 'internal whitespace'),
    (KEY+'\x1b', 'terminal control'),
    (KEY+'…', 'non-ASCII'),
    ('"'+KEY+'"', 'quotation marks'),
])
def test_diagnostic_never_includes_secret(tmp_path, key, reason):
    with pytest.raises(ValueError) as error:
        module.save_config(tmp_path / '.env.gemini', key, 'gemini-test-flash')
    assert reason in str(error.value)
    assert key not in str(error.value)
    assert not (tmp_path / '.env.gemini').exists()


def test_opaque_punctuation_round_trips_without_execution(tmp_path):
    check_spec = importlib.util.spec_from_file_location('check_setup_roundtrip', Path(__file__).resolve().parents[2] / 'scripts/check_gemini.py')
    check = importlib.util.module_from_spec(check_spec)
    check_spec.loader.exec_module(check)
    key = KEY + ':./+=!$()`;#&'
    path = tmp_path / '.env.gemini'
    module.save_config(path, key, 'gemini-test-flash')
    assert check.read_config(path)['GEMINI_API_KEY'] == key
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
