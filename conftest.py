# coding: utf-8
import os
import pytest


def clean_up():
    """
    Removes files created by tests
    """
    files = ['.uniqid',
             'upsert_db_users']
    for file_ in files:
        try:
            os.remove(os.path.join('/tmp', file_))
        except FileNotFoundError:
            pass


@pytest.fixture(scope="session", autouse=True)
def setup(request):
    # Clean up before tests begin in case of orphan files.
    clean_up()
    request.addfinalizer(_tear_down)


def _tear_down():
    clean_up()
    pass
