from pathlib import Path
from io import BytesIO
from pypdf import PdfReader

from app.db import schema as db
from app.db.store import Store
from app.ingest.seed import seed
from app.services import publish
from app.reports import review_pack
from app.export import csv_bytes


def test_streamable_report_contains_assumptions_and_artifact_values():
    store = Store("sqlite://")
    db.metadata.create_all(store.engine)
    seed(store)
    publish(store, Path(__file__).resolve().parents[2] / "results")
    content = review_pack(store)
    assert content.startswith(b"%PDF-")
    reader = PdfReader(BytesIO(content))
    text = " ".join(page.extract_text() for page in reader.pages)
    assert "SYNTHETIC COST ASSUMPTIONS" in text
    assert "not realized business savings" in text
    assert len(reader.pages) >= 1
    assert csv_bytes(store, "parts").startswith(b"id,description")
