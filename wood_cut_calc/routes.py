"""Routing definitions for the WoodYou Cutting Plan API."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .cutting_algorithms import generate_basic_plan


class Part(BaseModel):
    """A single part to be cut."""
    id: str = Field(..., description="Unique part identifier")
    label: str = Field(..., description="Part label or description")
    length: int = Field(..., ge=0, description="Part length in mm")
    width: int = Field(..., ge=0, description="Part width in mm")
    thickness: int = Field(..., ge=0, description="Part thickness in mm (0 for wildcard)")
    quantity: int = Field(1, ge=1, description="Number of identical parts")


class InventoryItem(BaseModel):
    """An available timber sheet in stock."""
    id: str = Field(..., description="Inventory sheet identifier")
    length: int = Field(..., ge=0, description="Sheet length in mm")
    width: int = Field(..., ge=0, description="Sheet width in mm")
    thickness: int = Field(..., ge=0, description="Sheet thickness in mm")
    price: float = Field(0.0, ge=0.0, description="Unit price")


class CuttingPlanRequest(BaseModel):
    """Request body for generating a cutting plan."""
    parts: List[Part]
    inventory: List[InventoryItem]


router = APIRouter()


@router.post("/cutting-plan")
async def cutting_plan(request: CuttingPlanRequest) -> Dict[str, Any]:
    """Generate a basic cutting plan for the given parts and inventory."""
    if not request.inventory:
        raise HTTPException(status_code=400, detail="Inventory cannot be empty")

    # Expand each part by its quantity
    raw_parts: List[Dict[str, Any]] = []
    for part in request.parts:
        for _ in range(part.quantity):
            raw_parts.append({
                "label": part.label,
                "length": part.length,
                "width": part.width,
                "thickness": part.thickness,
            })

    # Convert inventory to raw dicts
    raw_inventory = [
        {
            "id": item.id,
            "length": item.length,
            "width": item.width,
            "thickness": item.thickness,
            "price": item.price,
        }
        for item in request.inventory
    ]

    plan = generate_basic_plan(raw_parts, raw_inventory)
    return plan