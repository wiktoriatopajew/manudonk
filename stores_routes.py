"""
Shopify store cards for the internal /panel dashboard (/api/stores).

Each row is one store the user runs ads for: display name, shop link, the domain
that is currently pointed at it, and the Google account (login/password). Stored
in its own `shopify_stores` table so nothing here can touch the shop's data.

A tiny `store_name_history` table remembers every name ever typed so the /panel
form can suggest them again (pick from a list instead of retyping each time).
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func

from database.models import ShopifyStore, StoreNameHistory, GmcTimer, get_session

router = APIRouter(tags=["stores"])

MAX_STORES = ShopifyStore.MAX_STORES
NAME_HISTORY_LIMIT = 200


def _normalize_url(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if not value.startswith("http://") and not value.startswith("https://"):
        value = "https://" + value
    return value


def _remember_name(session, name: str):
    """Keep a unique list of store names ever used, capped to a sane size."""
    clean = (name or "").strip()
    if not clean:
        return
    existing = session.query(StoreNameHistory).filter(
        StoreNameHistory.name == clean
    ).first()
    if not existing:
        session.add(StoreNameHistory(name=clean))
        overflow = (session.query(func.count(StoreNameHistory.id)).scalar() or 0) \
            - NAME_HISTORY_LIMIT
        if overflow > 0:
            oldest = session.query(StoreNameHistory).order_by(
                StoreNameHistory.id.asc()
            ).limit(overflow).all()
            for row in oldest:
                session.delete(row)
        session.commit()


class StoreCreate(BaseModel):
    name: str = Field(..., max_length=255)
    url: str = Field(..., max_length=500)
    domain: str = Field(..., max_length=255)
    google_login: Optional[str] = Field(default=None, max_length=255)
    google_password: Optional[str] = Field(default=None, max_length=255)


class StoreUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    url: Optional[str] = Field(default=None, max_length=500)
    domain: Optional[str] = Field(default=None, max_length=255)
    google_login: Optional[str] = Field(default=None, max_length=255)
    google_password: Optional[str] = Field(default=None, max_length=255)


@router.get("/api/stores")
async def list_stores():
    session = get_session()
    try:
        stores = session.query(ShopifyStore).order_by(
            ShopifyStore.position.asc(), ShopifyStore.id.asc()
        ).all()
        return {
            'stores': [s.to_dict() for s in stores],
            'max_stores': MAX_STORES,
        }
    finally:
        session.close()


@router.post("/api/stores")
async def create_store(data: StoreCreate):
    session = get_session()
    try:
        count = session.query(func.count(ShopifyStore.id)).scalar() or 0
        if count >= MAX_STORES:
            raise HTTPException(
                status_code=409,
                detail=f"Maksymalna liczba sklepów to {MAX_STORES}."
            )

        name = (data.name or "").strip()
        url = _normalize_url(data.url)
        domain = (data.domain or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Podaj nazwę sklepu.")
        if not url:
            raise HTTPException(status_code=400, detail="Podaj link do sklepu.")
        if not domain:
            raise HTTPException(status_code=400, detail="Podaj aktualną domenę.")

        max_position = session.query(func.max(ShopifyStore.position)).scalar()
        store = ShopifyStore(
            name=name[:255],
            url=url[:500],
            domain=domain[:255],
            google_login=(data.google_login or None),
            google_password=(data.google_password or None),
            position=(max_position or 0) + 1,
        )
        session.add(store)
        session.flush()
        _remember_name(session, store.name)
        session.commit()
        session.refresh(store)
        return store.to_dict()
    finally:
        session.close()


@router.put("/api/stores/{store_id}")
async def update_store(store_id: int, data: StoreUpdate):
    session = get_session()
    try:
        store = session.query(ShopifyStore).filter(ShopifyStore.id == store_id).first()
        if not store:
            raise HTTPException(status_code=404, detail="Sklep nie istnieje.")

        fields = data.model_dump(exclude_unset=True) if hasattr(data, 'model_dump') \
            else data.dict(exclude_unset=True)

        if 'name' in fields:
            name = (fields['name'] or "").strip()
            if not name:
                raise HTTPException(status_code=400, detail="Podaj nazwę sklepu.")
            store.name = name[:255]
        if 'url' in fields:
            url = _normalize_url(fields['url'])
            if not url:
                raise HTTPException(status_code=400, detail="Podaj link do sklepu.")
            store.url = url[:500]
        if 'domain' in fields:
            domain = (fields['domain'] or "").strip()
            if not domain:
                raise HTTPException(status_code=400, detail="Podaj aktualną domenę.")
            store.domain = domain[:255]
        if 'google_login' in fields:
            store.google_login = (fields['google_login'] or "").strip() or None
        if 'google_password' in fields:
            store.google_password = (fields['google_password'] or "").strip() or None

        session.flush()
        _remember_name(session, store.name)
        session.commit()
        session.refresh(store)
        return store.to_dict()
    finally:
        session.close()


@router.delete("/api/stores/{store_id}")
async def delete_store(store_id: int):
    session = get_session()
    try:
        store = session.query(ShopifyStore).filter(ShopifyStore.id == store_id).first()
        if not store:
            raise HTTPException(status_code=404, detail="Sklep nie istnieje.")
        # Unlink any calculators pointing at this store - they keep counting
        # down, they just lose the store badge.
        session.query(GmcTimer).filter(GmcTimer.store_id == store_id).update(
            {GmcTimer.store_id: None}
        )
        session.delete(store)
        session.commit()
        return {"deleted": store_id}
    finally:
        session.close()


@router.get("/api/name-history")
async def name_history():
    """Store names ever used - feed the /panel form's datalist pick-list."""
    session = get_session()
    try:
        names = [row.name for row in session.query(StoreNameHistory).order_by(
            StoreNameHistory.id.desc()
        ).limit(NAME_HISTORY_LIMIT).all()]
        existing = {s.name for s in session.query(ShopifyStore.name).all()}
        merged = []
        seen = set()
        for n in names + sorted(existing):
            if n and n not in seen:
                seen.add(n)
                merged.append(n)
        return {'names': merged}
    finally:
        session.close()
