import hashlib
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from .db.schema import llm_daily_usage as usage


class Exhausted(Exception):
    pass


class DatabaseBudget:
    def __init__(self, store):
        self.store = store

    def reserve(self, username, day, global_cap, user_cap, output_tokens=0, token_global_cap=0, token_user_cap=0):
        if global_cap <= 0 or user_cap <= 0:
            return False
        subject = hashlib.sha256(username.encode()).hexdigest()
        try:
            with self.store.transaction() as connection:
                # Always acquire global before user to avoid cross-user deadlocks.
                limits = [('global', global_cap, 1), (subject, user_cap, 1)]
                if output_tokens:
                    limits += [('tokens-global', token_global_cap, output_tokens),
                               (hashlib.sha256(('output-tokens\0' + username).encode()).hexdigest(), token_user_cap, output_tokens)]
                for key, cap, units in limits:
                    condition = (usage.c.day == day) & (usage.c.subject == key)
                    if connection.scalar(select(usage.c.attempts).where(condition)) is None:
                        try:
                            with connection.begin_nested():
                                connection.execute(usage.insert().values(day=day, subject=key, attempts=0))
                        except IntegrityError:
                            if connection.scalar(select(usage.c.attempts).where(condition)) is None:
                                raise
                    result = connection.execute(update(usage).where(condition, usage.c.attempts <= cap - units)
                        .values(attempts=usage.c.attempts + units))
                    if result.rowcount != 1:
                        raise Exhausted()
            return True
        except Exhausted:
            return False

    def total(self, day):
        with self.store.transaction() as connection:
            return connection.scalar(select(usage.c.attempts).where(usage.c.day == day, usage.c.subject == 'global')) or 0

    def reserved_output_tokens(self, day):
        with self.store.transaction() as connection:
            return connection.scalar(select(usage.c.attempts).where(usage.c.day == day, usage.c.subject == 'tokens-global')) or 0
