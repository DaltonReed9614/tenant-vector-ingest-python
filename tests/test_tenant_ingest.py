from src.tenant_ingest import TenantOnboarding, account_state, chunk_documents


def test_admin_and_documents_activate_account():
    onboarding = TenantOnboarding("acme", "admin@acme.example", ["role policy"])
    assert account_state(onboarding) == "active"
    assert chunk_documents(onboarding.documents) == ["role policy"]


def test_missing_admin_stays_pending():
    assert account_state(TenantOnboarding("acme", None, ["role policy"])) == "pending"

