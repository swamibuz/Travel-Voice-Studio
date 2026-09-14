from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class InferMetadataItem(BaseModel):
    filename: str
    order_index: int = 0


class InferMetadataRequest(BaseModel):
    files: list[InferMetadataItem]


class SummaryRequest(BaseModel):
    sections: list[dict[str, object]]
    summary_type: str = "medium"


class ExportRequest(BaseModel):
    title: str = "Travel Book Manuscript"
    sections: list[dict[str, object]]
    include_raw: bool = False

