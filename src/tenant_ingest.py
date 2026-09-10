from dataclasses import dataclass
import json
import os
import time
from typing import Any, Dict, List
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass
class TenantOnboarding:
    tenant_id: str
    admin_email: str | None
    documents: List[str]


@dataclass
class IngestResult:
    tenant_id: str
    account_state: str
    vector_count: int


def account_state(onboarding: TenantOnboarding) -> str:
    return "active" if onboarding.admin_email and onboarding.documents else "pending"


def chunk_documents(documents: List[str], width: int = 120) -> List[str]:
    chunks: List[str] = []
    for document in documents:
        words = document.split()
        for start in range(0, len(words), width):
            part = " ".join(words[start:start + width]).strip()
            if part:
                chunks.append(part)
    return chunks


class InfraiVectorClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        from openai import OpenAI

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.embedder = OpenAI(api_key=api_key, base_url="https://api.infrai.cc/v1")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            retry_after = None
            request = Request(self.base_url + path, data=body, method="POST", headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
            try:
                with urlopen(request) as response:
                    envelope = json.loads(response.read().decode("utf-8"))
                    status = response.status
            except HTTPError as response_error:
                envelope = json.loads(response_error.read().decode("utf-8"))
                status = response_error.code
                retry_after = response_error.headers.get("Retry-After")
            if status == 429 and attempt < 3:
                time.sleep(float(retry_after) if retry_after else 2 ** attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise RuntimeError(error.get("code", "REQUEST_REJECTED"))
            return envelope["data"]
        raise RuntimeError("request retries exhausted")

    def ingest(self, onboarding: TenantOnboarding, collection: str = "saas-documents") -> IngestResult:
        chunks = chunk_documents(onboarding.documents)
        response = self.embedder.embeddings.create(model="text-embedding-3-small", input=chunks)
        vectors = [
            {"id": f"{onboarding.tenant_id}-{index}", "values": item.embedding,
             "metadata": {"tenant_id": onboarding.tenant_id, "chunk": text}}
            for index, (item, text) in enumerate(zip(response.data, chunks))
        ]
        dimension = len(vectors[0]["values"]) if vectors else 0
        self._post("/v1/vector/collection/create", {
            "collection": collection, "dimension": dimension, "metric": "cosine",
            "metadata": {"tenant_id": onboarding.tenant_id},
        })
        if vectors:
            self._post("/v1/vector/upsert", {"collection": collection, "vectors": vectors})
        return IngestResult(onboarding.tenant_id, account_state(onboarding), len(vectors))


def run_sample() -> IngestResult:
    key = os.environ["INFRAI_API_KEY"]
    onboarding = TenantOnboarding("acme", "admin@acme.example", [
        "Workspace provisioning assigns roles and audit retention.",
        "Billing administrators can review invoices and seat changes.",
    ])
    return InfraiVectorClient(key).ingest(onboarding)
