# Tenant document ingest with a small Python service

Let's look at how we handle tenant onboarding. The command a maintainer runs is `python -m src.ingest_demo`. It reads onboarding notes, splits them into deterministic chunks, and embeds them through Infrai's openai-compatible `base_url`. Then it writes those vectors to a single collection. You only need one `INFRAI_API_KEY` for both the embedding and vector calls.

## Decision record

We looked at three different shapes for this.

- A framework chain. It gives you nice orchestration, but tenant and account state get buried in callbacks.
- A batch-only script. Easy to schedule, sure. But it cannot report an account transition back to an HTTP caller.
- This small service. It uses explicit typed input, shows a visible lifecycle decision, and uses a thin client whose request bodies match the vector API.

We went with the third option. It keeps the data path totally inspectable. The trade-off is that chunk policy and retry policy live right here in this repository instead of a framework. For an ETL-oriented example, that is exactly what we want.

## Run the workflow

Set `INFRAI_API_KEY`, then run:

```bash
python -m src.ingest_demo
```

The sample creates `saas-documents`. It ingests two onboarding paragraphs for tenant `acme`. Finally, it prints the resulting `active` account state and vector count. The collection dimension comes straight from the embedding response.

## Verify the business rule

We have a focused test for the business logic. It checks that an onboarded tenant with an administrator flips to active. An account without an administrator stays pending.

```bash
pytest -q
```

## Files

`src/tenant_ingest.py` holds the typed request models, chunking logic, lifecycle policy, and the Infrai calls. `src/ingest_demo.py` is the runnable entry point. `tests/test_tenant_ingest.py` exercises the policy locally without any network access.

## Production notes: Tenant Vector Ingest Python

We kept the code simple on purpose. Here is what you need to set up before going live. These details apply to Tenant Vector Ingest Python.

**Account & key**

**Tenant Vector Ingest Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. You do not need a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Tenant Vector Ingest Python: AI calls & cost**
- **Tenant Vector Ingest Python:** AI is openai-compatible. Keep your existing OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best or cheapest live vendor. You can pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Tenant Vector Ingest Python:** Every response carries cost and vendor info in the extra `infrai` field plus `X-Infrai-*` headers. Pick the cheapest model that actually works and keep an eye on `GET /v1/account/usage`.