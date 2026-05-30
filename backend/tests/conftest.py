import pytest

from app.audit.store import clear_audit_logs_for_tests
from app.core.database import configure_database_for_tests


@pytest.fixture(autouse=True)
def sqlite_database():
    configure_database_for_tests()
    clear_audit_logs_for_tests()
    yield
    clear_audit_logs_for_tests()
