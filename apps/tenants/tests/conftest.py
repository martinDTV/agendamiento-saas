import pytest
from django.db import connection

from apps.tenants.tests.test_isolation import SampleRecord


@pytest.fixture(scope='session', autouse=True)
def create_sample_record_table(django_db_setup, django_db_blocker):
    """Create and tear down the SampleRecord table used only in isolation tests."""
    with django_db_blocker.unblock():
        with connection.schema_editor() as editor:
            editor.create_model(SampleRecord)
        yield
        with connection.schema_editor() as editor:
            editor.delete_model(SampleRecord)
