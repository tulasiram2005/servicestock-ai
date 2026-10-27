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
