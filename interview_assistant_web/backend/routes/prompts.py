"""
Prompt Template Routes - Manage prompt templates and profiles
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import get_db, PromptTemplate, SetupProfile
from models.schemas import (
    PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateResponse,
    TabWithSubtabs, SetupProfileCreate, SetupProfileResponse
)

router = APIRouter(prefix="/prompts", tags=["Prompts"])


# ============================================================================
# Prompt Template Endpoints
# ============================================================================

@router.post("/templates", response_model=PromptTemplateResponse)
def create_template(
    data: PromptTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new prompt template"""
    # Get max order index for this tab
    max_order = db.query(func.max(PromptTemplate.order_index))\
        .filter(PromptTemplate.tab_name == data.tab_name)\
        .scalar() or 0
    
    template = PromptTemplate(
        tab_name=data.tab_name,
        subtab_name=data.subtab_name,
        prompt_text=data.prompt_text,
        order_index=data.order_index or max_order + 1
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return PromptTemplateResponse(
        id=template.id,
        tab_name=template.tab_name,
        subtab_name=template.subtab_name,
        prompt_text=template.prompt_text,
        order_index=template.order_index,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.get("/templates", response_model=List[PromptTemplateResponse])
def get_all_templates(db: Session = Depends(get_db)):
    """Get all prompt templates"""
    templates = db.query(PromptTemplate)\
        .order_by(PromptTemplate.tab_name, PromptTemplate.order_index)\
        .all()
    
    return [
        PromptTemplateResponse(
            id=t.id,
            tab_name=t.tab_name,
            subtab_name=t.subtab_name,
            prompt_text=t.prompt_text,
            order_index=t.order_index,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in templates
    ]


@router.get("/templates/grouped", response_model=List[TabWithSubtabs])
def get_grouped_templates(db: Session = Depends(get_db)):
    """Get templates grouped by tab"""
    templates = db.query(PromptTemplate)\
        .order_by(PromptTemplate.tab_name, PromptTemplate.order_index)\
        .all()
    
    # Group by tab
    tabs = {}
    for t in templates:
        if t.tab_name not in tabs:
            tabs[t.tab_name] = []
        tabs[t.tab_name].append(
            PromptTemplateResponse(
                id=t.id,
                tab_name=t.tab_name,
                subtab_name=t.subtab_name,
                prompt_text=t.prompt_text,
                order_index=t.order_index,
                created_at=t.created_at,
                updated_at=t.updated_at
            )
        )
    
    return [
        TabWithSubtabs(tab_name=name, subtabs=subtabs)
        for name, subtabs in tabs.items()
    ]


@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a specific template"""
    template = db.query(PromptTemplate)\
        .filter(PromptTemplate.id == template_id)\
        .first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return PromptTemplateResponse(
        id=template.id,
        tab_name=template.tab_name,
        subtab_name=template.subtab_name,
        prompt_text=template.prompt_text,
        order_index=template.order_index,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.put("/templates/{template_id}", response_model=PromptTemplateResponse)
def update_template(
    template_id: int,
    data: PromptTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a prompt template"""
    template = db.query(PromptTemplate)\
        .filter(PromptTemplate.id == template_id)\
        .first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if data.tab_name is not None:
        template.tab_name = data.tab_name
    if data.subtab_name is not None:
        template.subtab_name = data.subtab_name
    if data.prompt_text is not None:
        template.prompt_text = data.prompt_text
    if data.order_index is not None:
        template.order_index = data.order_index
    
    db.commit()
    db.refresh(template)
    
    return PromptTemplateResponse(
        id=template.id,
        tab_name=template.tab_name,
        subtab_name=template.subtab_name,
        prompt_text=template.prompt_text,
        order_index=template.order_index,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete a prompt template"""
    template = db.query(PromptTemplate)\
        .filter(PromptTemplate.id == template_id)\
        .first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    return {"success": True}


@router.post("/templates/reorder")
def reorder_templates(
    template_orders: List[dict],  # [{id: 1, order_index: 0}, ...]
    db: Session = Depends(get_db)
):
    """Reorder templates"""
    for item in template_orders:
        template = db.query(PromptTemplate)\
            .filter(PromptTemplate.id == item["id"])\
            .first()
        if template:
            template.order_index = item["order_index"]
    
    db.commit()
    return {"success": True}


# ============================================================================
# Tab Management
# ============================================================================

@router.get("/tabs")
def get_tabs(db: Session = Depends(get_db)):
    """Get all tab names"""
    tabs = db.query(PromptTemplate.tab_name)\
        .distinct()\
        .order_by(PromptTemplate.tab_name)\
        .all()
    
    return [tab[0] for tab in tabs]


@router.put("/tabs/{old_name}/rename")
def rename_tab(
    old_name: str,
    new_name: str,
    db: Session = Depends(get_db)
):
    """Rename a tab"""
    updated = db.query(PromptTemplate)\
        .filter(PromptTemplate.tab_name == old_name)\
        .update({PromptTemplate.tab_name: new_name})
    
    if updated == 0:
        raise HTTPException(status_code=404, detail="Tab not found")
    
    db.commit()
    return {"success": True, "templates_updated": updated}


@router.delete("/tabs/{tab_name}")
def delete_tab(tab_name: str, db: Session = Depends(get_db)):
    """Delete a tab and all its subtabs"""
    deleted = db.query(PromptTemplate)\
        .filter(PromptTemplate.tab_name == tab_name)\
        .delete()
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Tab not found")
    
    db.commit()
    return {"success": True, "templates_deleted": deleted}


# ============================================================================
# Setup Profile Endpoints
# ============================================================================

@router.post("/profiles", response_model=SetupProfileResponse)
def create_profile(
    data: SetupProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a quick setup profile"""
    # Check if name exists
    existing = db.query(SetupProfile)\
        .filter(SetupProfile.name == data.name)\
        .first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Profile name already exists")
    
    profile = SetupProfile(
        name=data.name,
        prompt_ids=data.prompt_ids
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return SetupProfileResponse(
        id=profile.id,
        name=profile.name,
        prompt_ids=profile.prompt_ids,
        created_at=profile.created_at
    )


@router.get("/profiles", response_model=List[SetupProfileResponse])
def get_profiles(db: Session = Depends(get_db)):
    """Get all setup profiles"""
    profiles = db.query(SetupProfile)\
        .order_by(SetupProfile.created_at.desc())\
        .all()
    
    return [
        SetupProfileResponse(
            id=p.id,
            name=p.name,
            prompt_ids=p.prompt_ids,
            created_at=p.created_at
        )
        for p in profiles
    ]


@router.delete("/profiles/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete a setup profile"""
    profile = db.query(SetupProfile)\
        .filter(SetupProfile.id == profile_id)\
        .first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    db.delete(profile)
    db.commit()
    return {"success": True}


# ============================================================================
# Import/Export
# ============================================================================

@router.get("/export")
def export_templates(db: Session = Depends(get_db)):
    """Export all templates as JSON"""
    templates = db.query(PromptTemplate).all()
    profiles = db.query(SetupProfile).all()
    
    return {
        "templates": [
            {
                "tab_name": t.tab_name,
                "subtab_name": t.subtab_name,
                "prompt_text": t.prompt_text,
                "order_index": t.order_index
            }
            for t in templates
        ],
        "profiles": [
            {
                "name": p.name,
                "prompt_ids": p.prompt_ids
            }
            for p in profiles
        ]
    }


@router.post("/import")
def import_templates(
    data: dict,
    db: Session = Depends(get_db)
):
    """Import templates from JSON"""
    templates_data = data.get("templates", [])
    
    imported = 0
    for t in templates_data:
        # Check if exists
        existing = db.query(PromptTemplate)\
            .filter(
                PromptTemplate.tab_name == t["tab_name"],
                PromptTemplate.subtab_name == t["subtab_name"]
            )\
            .first()
        
        if not existing:
            template = PromptTemplate(
                tab_name=t["tab_name"],
                subtab_name=t["subtab_name"],
                prompt_text=t["prompt_text"],
                order_index=t.get("order_index", 0)
            )
            db.add(template)
            imported += 1
    
    db.commit()
    return {"success": True, "imported": imported}





