"""
Property Catalogs API Endpoints
Create and manage property portfolios/catalogs
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

from database import async_session, Tenant, TenantProperty, get_db

router = APIRouter(prefix="/api/tenants", tags=["Catalogs"])


class PropertyCatalogCreate(BaseModel):
    """Request body for creating a catalog (tenant_id comes from URL path)"""
    name: str
    description: Optional[str] = None
    property_ids: List[int]  # List of TenantProperty IDs
    is_public: bool = False


class PropertyCatalog(BaseModel):
    """Full catalog model including tenant_id"""
    id: Optional[int] = None
    tenant_id: int
    name: str
    description: Optional[str] = None
    property_ids: List[int]  # List of TenantProperty IDs
    is_public: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CatalogResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: Optional[str]
    property_ids: List[int]
    property_count: int
    is_public: bool
    share_link: Optional[str]
    created_at: datetime
    updated_at: datetime


# In-memory storage (replace with database table in production)
CATALOGS_DB = {}
CATALOG_ID_COUNTER = 1


@router.get("/{tenant_id}/catalogs", response_model=List[CatalogResponse])
async def get_catalogs(
    tenant_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all catalogs for a tenant."""
    # Filter catalogs by tenant_id
    tenant_catalogs = [
        CatalogResponse(
            id=catalog["id"],
            tenant_id=catalog["tenant_id"],
            name=catalog["name"],
            description=catalog.get("description"),
            property_ids=catalog["property_ids"],
            property_count=len(catalog["property_ids"]),
            is_public=catalog.get("is_public", False),
            share_link=f"/catalogs/{catalog['id']}" if catalog.get("is_public") else None,
            created_at=catalog["created_at"],
            updated_at=catalog["updated_at"]
        )
        for catalog in CATALOGS_DB.values()
        if catalog["tenant_id"] == tenant_id
    ]
    
    return tenant_catalogs


@router.post("/{tenant_id}/catalogs", response_model=CatalogResponse)
async def create_catalog(
    tenant_id: int,
    catalog: PropertyCatalogCreate,  # Changed from PropertyCatalog
    db: AsyncSession = Depends(get_db)
):
    """Create a new property catalog."""
    global CATALOG_ID_COUNTER
    
    # Verify tenant exists
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Verify properties exist
    if catalog.property_ids:
        props_result = await db.execute(
            select(TenantProperty).where(
                and_(
                    TenantProperty.tenant_id == tenant_id,
                    TenantProperty.id.in_(catalog.property_ids)
                )
            )
        )
        found_props = props_result.scalars().all()
        if len(found_props) != len(catalog.property_ids):
            raise HTTPException(status_code=404, detail="Some properties not found")
    
    # Create catalog
    now = datetime.utcnow()
    catalog_id = CATALOG_ID_COUNTER
    CATALOG_ID_COUNTER += 1
    
    catalog_data = {
        "id": catalog_id,
        "tenant_id": tenant_id,
        "name": catalog.name,
        "description": catalog.description,
        "property_ids": catalog.property_ids,
        "is_public": catalog.is_public,
        "created_at": now,
        "updated_at": now
    }
    
    CATALOGS_DB[catalog_id] = catalog_data
    
    return CatalogResponse(
        id=catalog_id,
        tenant_id=tenant_id,
        name=catalog.name,
        description=catalog.description,
        property_ids=catalog.property_ids,
        property_count=len(catalog.property_ids),
        is_public=catalog.is_public,
        share_link=f"/catalogs/{catalog_id}" if catalog.is_public else None,
        created_at=now,
        updated_at=now
    )


@router.put("/{tenant_id}/catalogs/{catalog_id}", response_model=CatalogResponse)
async def update_catalog(
    tenant_id: int,
    catalog_id: int,
    catalog: PropertyCatalogCreate,  # Changed from PropertyCatalog
    db: AsyncSession = Depends(get_db)
):
    """Update an existing catalog."""
    if catalog_id not in CATALOGS_DB:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    existing = CATALOGS_DB[catalog_id]
    if existing["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify properties exist
    if catalog.property_ids:
        props_result = await db.execute(
            select(TenantProperty).where(
                and_(
                    TenantProperty.tenant_id == tenant_id,
                    TenantProperty.id.in_(catalog.property_ids)
                )
            )
        )
        found_props = props_result.scalars().all()
        if len(found_props) != len(catalog.property_ids):
            raise HTTPException(status_code=404, detail="Some properties not found")
    
    # Update
    now = datetime.utcnow()
    CATALOGS_DB[catalog_id].update({
        "name": catalog.name,
        "description": catalog.description,
        "property_ids": catalog.property_ids,
        "is_public": catalog.is_public,
        "updated_at": now
    })
    
    updated = CATALOGS_DB[catalog_id]
    
    return CatalogResponse(
        id=catalog_id,
        tenant_id=tenant_id,
        name=updated["name"],
        description=updated.get("description"),
        property_ids=updated["property_ids"],
        property_count=len(updated["property_ids"]),
        is_public=updated["is_public"],
        share_link=f"/catalogs/{catalog_id}" if updated["is_public"] else None,
        created_at=updated["created_at"],
        updated_at=updated["updated_at"]
    )


@router.delete("/{tenant_id}/catalogs/{catalog_id}")
async def delete_catalog(
    tenant_id: int,
    catalog_id: int
):
    """Delete a catalog."""
    if catalog_id not in CATALOGS_DB:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    existing = CATALOGS_DB[catalog_id]
    if existing["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del CATALOGS_DB[catalog_id]
    
    return {"status": "deleted", "id": catalog_id}


@router.get("/{tenant_id}/catalogs/{catalog_id}/download")
async def download_catalog(
    tenant_id: int,
    catalog_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download catalog as PDF (stub - returns JSON for now)."""
    if catalog_id not in CATALOGS_DB:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    catalog = CATALOGS_DB[catalog_id]
    if catalog["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Fetch property details
    props_result = await db.execute(
        select(TenantProperty).where(
            and_(
                TenantProperty.tenant_id == tenant_id,
                TenantProperty.id.in_(catalog["property_ids"])
            )
        )
    )
    properties = props_result.scalars().all()
    
    # Return JSON for now (implement PDF generation later)
    catalog_data = {
        "catalog": catalog,
        "properties": [
            {
                "id": p.id,
                "name": p.name,
                "location": p.location,
                "price": p.price,
                "bedrooms": p.bedrooms,
                "type": p.type
            }
            for p in properties
        ]
    }
    
    return Response(
        content=json.dumps(catalog_data, default=str, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=catalog_{catalog_id}.json"}
    )
