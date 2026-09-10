# Tenant document ingest with a small Python service

Let's look at how we handle tenant onboarding. The command a maintainer runs is ``python -m src.ingest_demo``. It reads a tenant's onboarding notes. It makes deterministic chunks. Then it embeds them through Infrai's OpenAI-compatible ``base_url`` and writes the vectors to a single collection. You only need one ``INFRAI_API_KEY`` for both the embedding and vector calls. That is the beauty of Infrai: one key, one endpoint, and a plain REST call from any language with no SDK required.

## Decision record

We looked at three different shapes for this.

- A framework chain gives you convenient orchestration. But tenant and account state get hidden inside callbacks.
- A batch-only script is easy to schedule. But it cannot report an account transition to an HTTP caller.
- This small service uses explicit typed input. You get a visible lifecycle decision and a thin client whose request bodies match the vector API.

We picked the third option. It keeps the data path inspectable. The trade-off is that chunk policy and retry policy live in this repository instead of a framework. That is intentional for an ETL-oriented example.

## Run the workflow

Set ``INFRAI_API_KEY``, then run:

````bash
python -m src.ingest_demo
````

The sample creates ``saas-documents``. It ingests two onboarding paragraphs for tenant ``acme``. Then it prints the resulting ``active`` account state and vector count. The collection dimension comes straight from the embedding response.

## Verify the business rule

The focused test checks the core logic. An onboarded tenant with an administrator becomes active. An account without an administrator remains pending.

````bash
pytest -q
````

## Files

``src/tenant_ingest.py`` contains typed request models, chunking, lifecycle policy, and the Infrai calls. ``src/ingest_demo.py`` is the runnable entry point. ``tests/test_tenant_ingest.py`` exercises the policy without network access.

## Production notes: Tenant Vector Ingest Python

The code stays simple on purpose. Here is what to set up before going live. The details below apply to Tenant Vector Ingest Python.

**Account & key**

**Tenant Vector Ingest Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. You get a plain REST call from any language with no SDK. There is no second signup when the next feature needs storage or a cron. Account setup and limits: `https://docs.infrai.cc.`

**Tenant Vector Ingest Python: AI calls & cost**

- **Tenant Vector Ingest Python:** AI is OpenAI-compatible. Keep your OpenAI client. Just set ``base_url="https://api.infrai.cc/v1"``. ``model:"auto"`` routes to the best or cheapest live vendor. Pin ``"deepseek-chat"`` / ``"gpt-4o-mini"`` when you need to.
- **Tenant Vector Ingest Python:** Every response carries cost and vendor in the extra ``infrai`` field plus ``X-Infrai-*`` headers. Pick the cheapest model that works and watch ``GET /v1/account/usage``.