from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LeadCreate(BaseModel):
    full_name: str = Field(..., example="Ali Valiyev")
    phone: str = Field(..., example="+998901234567")
    course: Optional[str] = Field(default="Ingliz tili", example="Ingliz tili")
    source: Optional[str] = Field(default="Instagram Target", example="Instagram Target")
    ad_name: Optional[str] = Field(default="Target Noyabr 2026", example="Target Noyabr 2026")
    notes: Optional[str] = Field(default="", example="Soat 18:00 dan keyin bo'sh ekan")

class LeadUpdateStatus(BaseModel):
    status: str = Field(..., example="CONTACTED")
    assigned_to: Optional[str] = Field(default="Admin", example="Admin")
    note: Optional[str] = Field(default=None, example="Bog'landik, ertaga sinov darsiga keladi")
    trial_date: Optional[str] = Field(default=None, example="2026-11-10 18:30")
    cancel_reason: Optional[str] = Field(default=None, example="Qimmatlik qildi")

class LeadResponse(BaseModel):
    id: int
    full_name: str
    phone: str
    course: Optional[str]
    source: Optional[str]
    ad_name: Optional[str]
    status: str
    notes: Optional[str]
    assigned_to: Optional[str]
    trial_date: Optional[str] = None
    cancel_reason: Optional[str] = None
    telegram_message_id: Optional[int]
    created_at: str
    updated_at: str

