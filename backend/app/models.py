from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TripRequest(BaseModel):
    title: str = "Around the World Travel Book"
    description: str = "Voice notes and visit documentation for a travel blog and book."
    start_date: str = ""
    end_date: str = ""
    route_summary: str = ""


class OrderItem(BaseModel):
    id: int
    order_index: int


class OrderRequest(BaseModel):
    items: list[OrderItem]


class TravelMetadataRequest(BaseModel):
    country: str = ""
    city: str = ""
    place_name: str = ""
    visit_date: str = ""
    route_order: int = 0
    blog_title: str = ""
    chapter_title: str = ""
    tags: str = ""
    notes: str = ""


class TranscriptUpdateRequest(BaseModel):
    cleaned_text: str
    blog_draft_text: str = ""
    chapter_draft_text: str = ""
    reviewed_status: str = "reviewed"


class SummaryRequest(BaseModel):
    batch_id: int
    summary_type: str = "medium"


class ExportRequest(BaseModel):
    batch_id: int
    include_raw: bool = False
