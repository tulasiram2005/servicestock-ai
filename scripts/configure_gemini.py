"""Privately prepare an ignored Gemini smoke-test configuration; makes no API calls."""
import getpass
import os
from pathlib import Path
import re
import sys
import warnings

DESTINATION = Path(__file__).resolve().parents[1] / '.env.gemini'


def save_config(path, key, model):
    # Strict single-line values prevent dotenv injection. Never include input in errors.
    if not re.fullmatch(r'[A-Za-z0-9_-]{20,200}', key):
        raise ValueError('Invalid key format')
    if not re.fullmatch(r'gemini-[a-z0-9.-]*flash[a-z0-9.-]*', model):
        raise ValueError('Enter a verified free-tier Gemini Flash model ID')
    payload = f'GEMINI_API_KEY={key}\nGEMINI_MODEL={model}\nGEMINI_FREE_TIER_CONFIRMED=true\n'
    # Exclusive creation also refuses symlinks; never overwrite an existing secret file.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(payload)


def main():
    if not sys.stdin.isatty():
        print('Run this command directly in an interactive terminal.')
        return 2
    print('No network requests will be made. Existing configuration will not be overwritten.')
    model = input('Verified free-tier Flash model ID: ').strip()
    confirmed = input('Project billing disabled and this model has free quota? Type yes: ').strip()
    if confirmed.lower() != 'yes':
        print('Cancelled; nothing saved.')
        return 2
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            key = getpass.getpass('Gemini API key (hidden): ')
        save_config(DESTINATION, key, model)
    except (OSError, ValueError, getpass.GetPassWarning):
        print('Configuration not saved. Check model/key format or whether .env.gemini already exists.')
        return 2
    print('Saved privately to .env.gemini. Offline application defaults are unchanged.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print('\nCancelled.')
        raise SystemExit(2)
