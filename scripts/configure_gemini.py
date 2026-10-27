"""Privately prepare an ignored Gemini smoke-test configuration; makes no API calls."""
import getpass
import os
from pathlib import Path
import re
import sys
import warnings

DESTINATION = Path(__file__).resolve().parents[1] / '.env.gemini'


def save_config(path, key, model):
    # Trim surrounding clipboard whitespace; reject embedded newlines or shell syntax.
    key = key.strip()
    # Some terminals include bracketed-paste control markers in hidden input.
    if key.startswith('\x1b[200~') and key.endswith('\x1b[201~'):
        key = key[6:-6].strip()
    if not key:
        raise ValueError('No key received. Copy the full key, then paste once at the hidden prompt.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{20,200}', key):
        reasons = []
        if len(key) < 20:
            reasons.append('fewer than 20 characters received')
        if len(key) > 200:
            reasons.append('more than 200 characters received')
        if any(c.isspace() for c in key):
            reasons.append('contains internal whitespace')
        if any(ord(c) < 32 or ord(c) == 127 for c in key):
            reasons.append('contains terminal control characters')
        if any(ord(c) > 127 for c in key):
            reasons.append('contains non-ASCII characters')
        if any(c in '\"\'' for c in key):
            reasons.append('contains quotation marks')
        if not reasons:
            reasons.append('contains punctuation outside letters, digits, underscore and hyphen')
        raise ValueError('Key format not recognized: ' + '; '.join(reasons) + '. No key content displayed or saved.')
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
    except ValueError as error:
        # save_config emits only fixed messages, never the submitted value.
        print(str(error))
        return 2
    except FileExistsError:
        print('.env.gemini already exists; it was not changed. Ask to run the safe preflight check.')
        return 2
    except getpass.GetPassWarning:
        print('Hidden input is unavailable. Run directly in the macOS Terminal app.')
        return 2
    except OSError:
        print('Could not save the private file. Check folder permissions and available disk space.')
        return 2
    print('Saved privately to .env.gemini. Offline application defaults are unchanged.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print('\nCancelled.')
        raise SystemExit(2)
