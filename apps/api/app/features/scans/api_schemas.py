"""Request and response models for the scan routes (Plan 4 Task 4).

Separate from `schemas.py` (the model-facing extraction schema) because `ProductDraft`
lives in `normalize.py`, which itself imports `schemas.py`.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.features.scans.normalize import ProductDraft

UPLOAD_URL_EXPIRES_IN_S = 600


class UploadUrlIn(BaseModel):
    ext: Literal["jpg", "png", "webp"]


class UploadUrlOut(BaseModel):
    upload_url: str  # PUT the photo here (Supabase Storage signed upload URL)
    path: str  # `<account_id>/<uuid4>.<ext>`; send it to POST /v1/scans/label
    expires_in: int  # seconds


class LabelScanIn(BaseModel):
    path: str = Field(max_length=200)
    barcode: str | None = Field(default=None, max_length=32)


class ScanDraftOut(BaseModel):
    scan_id: UUID
    draft: ProductDraft  # unconfirmed: the user must review it before any product is saved
    cached: bool  # True when served from an earlier extraction of the same image
    prompt_version: str
