from src.tenant_ingest import run_sample


if __name__ == "__main__":
    result = run_sample()
    print(f"tenant={result.tenant_id} state={result.account_state} vectors={result.vector_count}")

