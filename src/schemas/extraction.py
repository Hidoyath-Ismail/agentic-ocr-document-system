from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class ExtractedDocument(BaseModel):
    doc_type: str = Field(..., description="receipt|invoice|po|unknown")
    vendor_name: Optional[str] = None
    document_number: Optional[str] = None
    date: Optional[str] = None  # keep as string for now; parse/validate later
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    payment_method: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
