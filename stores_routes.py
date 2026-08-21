"""
Shopify store cards + reserves for the internal /panel dashboard.

/api/stores       - the store cards (name, link, active domain, Google account)
/api/domains      - purchased domains inventory (lifecycle below)
/api/gmc-accounts - Google Merchant Center accounts kept in reserve
/api/ads-accounts - Google Ads accounts kept in reserve
/api/name-history - store names ever used, for the form's pick-list

Domain lifecycle (matches how Google burns domains):
  available (inventory) -> assigned to a store = ACTIVE
  unassigned once        -> disabled, shown red (still in the list)
  re-assigned + removed  -> deleted for good (strike two, gone)

Everything lives in its own tables so nothing here can touch the shop's data.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func

from database.models import (
    ShopifyStore, StoreNameHistory, GmcTimer, Domain, GmcAccount, AdsAccount, get_session
)

router = APIRouter(tags=["stores"])

MAX_STORES = ShopifyStore.MAX_STORES
NAME_HISTORY_LIMIT = 200


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if not value.startswith("http://") and not value.startswith("https://"):
        value = "https://" + value
    return value


def _normalize_domain(value: str) -> str:
    clean = (value or "").strip().lower()
    for prefix in ("http://", "https://", "www."):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    return clean.rstrip("/").rstrip(".")


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


def _deactivate_domain(session, domain_row: Domain):
    """Unassign a domain. First strike -> red, second strike -> gone for good."""
    domain_row.deactivation_count += 1
    domain_row.store_id = None
    if domain_row.deactivation_count >= 2:
        session.delete(domain_row)
        print(f"🗑  Domain '{domain_row.domain}' deleted (2nd deactivation)")
    else:
        domain_row.status = 'disabled'
        print(f"🔴 Domain '{domain_row.domain}' disabled (strike {domain_row.deactivation_count})")


def _activate_domain(session, store: ShopifyStore, domain_text: str) -> Optional[Domain]:
    """Assign a domain to a store, creating the inventory entry on the fly."""
    clean = _normalize_domain(domain_text)
    if not clean:
        return None
    row = session.query(Domain).filter(Domain.domain == clean).first()
    if row is None:
        row = Domain(domain=clean, status='active', store_id=store.id)
        session.add(row)
        session.flush()
    else:
        if row.store_id and row.store_id != store.id:
            raise HTTPException(
                status_code=400,
                detail=f"Domena '{clean}' jest już przypisana do innego sklepu."
            )
        row.status = 'active'
        row.store_id = store.id
    return row


def _apply_domain_change(session, store: ShopifyStore, new_domain_text: str):
    """Swap the store's domain and run the old one through its lifecycle."""
    old_clean = _normalize_domain(store.domain)
    new_clean = _normalize_domain(new_domain_text)
    old_row = None
    if old_clean:
        old_row = session.query(Domain).filter(Domain.domain == old_clean).first()

    new_row = _activate_domain(session, store, new_clean) if new_clean else None

    if old_row and (new_row is None or old_row.id != new_row.id):
        _deactivate_domain(session, old_row)

    store.domain = new_clean


def _apply_account(session, store: ShopifyStore, model, field: str, account_id):
    """Assign/unassign a reserve account (GMC or Ads) to a store."""
    old_id = getattr(store, field)
    if old_id and old_id != account_id:
        old = session.query(model).filter(model.id == old_id).first()
        if old:
            old.store_id = None

    if account_id is not None:
        acc = session.query(model).filter(model.id == account_id).first()
        if not acc:
            raise HTTPException(status_code=400, detail="Konto nie istnieje.")
        if acc.store_id and acc.store_id != store.id:
            raise HTTPException(status_code=400, detail="To konto jest już przypisane do innego sklepu.")
        acc.store_id = store.id

    setattr(store, field, account_id)


# ---------------------------------------------------------------------------
# pydantic models
# ---------------------------------------------------------------------------

class StoreCreate(BaseModel):
    name: str = Field(..., max_length=255)
    url: str = Field(..., max_length=500)
    domain: str = Field(..., max_length=255)
    google_login: Optional[str] = Field(default=None, max_length=255)
    google_password: Optional[str] = Field(default=None, max_length=255)
    gmc_account_id: Optional[int] = None
    ads_account_id: Optional[int] = None


class StoreUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    url: Optional[str] = Field(default=None, max_length=500)
    domain: Optional[str] = Field(default=None, max_length=255)
    google_login: Optional[str] = Field(default=None, max_length=255)
    google_password: Optional[str] = Field(default=None, max_length=255)
    gmc_account_id: Optional[int] = None
    ads_account_id: Optional[int] = None


class DomainCreate(BaseModel):
    domain: str = Field(..., max_length=255)


class AccountCreate(BaseModel):
    name: str = Field(..., max_length=255)
    login: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, max_length=255)


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    login: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, max_length=255)


# ---------------------------------------------------------------------------
# stores
# ---------------------------------------------------------------------------

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
        domain_text = data.domain or ""
        if not name:
            raise HTTPException(status_code=400, detail="Podaj nazwę sklepu.")
        if not url:
            raise HTTPException(status_code=400, detail="Podaj link do sklepu.")
        if not _normalize_domain(domain_text):
            raise HTTPException(status_code=400, detail="Podaj aktualną domenę.")

        max_position = session.query(func.max(ShopifyStore.position)).scalar()
        store = ShopifyStore(
            name=name[:255],
            url=url[:500],
            domain=_normalize_domain(domain_text),
            google_login=(data.google_login or None),
            google_password=(data.google_password or None),
            position=(max_position or 0) + 1,
        )
        session.add(store)
        session.flush()

        _activate_domain(session, store, domain_text)
        if data.gmc_account_id is not None:
            _apply_account(session, store, GmcAccount, 'gmc_account_id', data.gmc_account_id)
        if data.ads_account_id is not None:
            _apply_account(session, store, AdsAccount, 'ads_account_id', data.ads_account_id)

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
            _apply_domain_change(session, store, fields['domain'])
        if 'google_login' in fields:
            store.google_login = (fields['google_login'] or "").strip() or None
        if 'google_password' in fields:
            store.google_password = (fields['google_password'] or "").strip() or None
        if 'gmc_account_id' in fields:
            _apply_account(session, store, GmcAccount, 'gmc_account_id', fields['gmc_account_id'])
        if 'ads_account_id' in fields:
            _apply_account(session, store, AdsAccount, 'ads_account_id', fields['ads_account_id'])

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

        # Domain goes through the deactivation lifecycle (red, then gone).
        if store.domain:
            old_row = session.query(Domain).filter(
                Domain.domain == _normalize_domain(store.domain)
            ).first()
            if old_row:
                _deactivate_domain(session, old_row)

        # Free any reserve accounts this store was using.
        for model, field in ((GmcAccount, 'gmc_account_id'), (AdsAccount, 'ads_account_id')):
            acc_id = getattr(store, field)
            if acc_id:
                acc = session.query(model).filter(model.id == acc_id).first()
                if acc:
                    acc.store_id = None

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


# ---------------------------------------------------------------------------
# domains inventory
# ---------------------------------------------------------------------------

@router.get("/api/domains")
async def list_domains():
    session = get_session()
    try:
        domains = session.query(Domain).order_by(Domain.id.desc()).all()
        return {'domains': [d.to_dict() for d in domains]}
    finally:
        session.close()


@router.post("/api/domains")
async def create_domain(data: DomainCreate):
    session = get_session()
    try:
        clean = _normalize_domain(data.domain)
        if not clean:
            raise HTTPException(status_code=400, detail="Podaj domenę.")
        row = session.query(Domain).filter(Domain.domain == clean).first()
        if row:
            # Re-adding a known domain just brings it back to the inventory
            # (it stays on the side panel, statuses intact).
            session.refresh(row)
            session.commit()
            return row.to_dict()
        row = Domain(domain=clean, status='available')
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.to_dict()
    finally:
        session.close()


@router.delete("/api/domains/{domain_id}")
async def delete_domain(domain_id: int):
    session = get_session()
    try:
        row = session.query(Domain).filter(Domain.id == domain_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Domena nie istnieje.")
        if row.store_id:
            # If it is assigned, free the store's domain field first.
            store = session.query(ShopifyStore).filter(ShopifyStore.id == row.store_id).first()
            if store:
                store.domain = ""
        session.delete(row)
        session.commit()
        return {"deleted": domain_id}
    finally:
        session.close()


# ---------------------------------------------------------------------------
# reserve accounts (GMC / Google Ads)
# ---------------------------------------------------------------------------

def _list_accounts(model):
    session = get_session()
    try:
        rows = session.query(model).order_by(model.id.desc()).all()
        return {'accounts': [a.to_dict() for a in rows]}
    finally:
        session.close()


def _create_account(model, data: AccountCreate):
    session = get_session()
    try:
        name = (data.name or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Podaj nazwę konta.")
        row = model(
            name=name[:255],
            login=(data.login or None),
            password=(data.password or None),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.to_dict()
    finally:
        session.close()


def _update_account(model, account_id: int, data: AccountUpdate):
    session = get_session()
    try:
        row = session.query(model).filter(model.id == account_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Konto nie istnieje.")
        fields = data.model_dump(exclude_unset=True) if hasattr(data, 'model_dump') \
            else data.dict(exclude_unset=True)
        if 'name' in fields:
            name = (fields['name'] or "").strip()
            if not name:
                raise HTTPException(status_code=400, detail="Podaj nazwę konta.")
            row.name = name[:255]
        if 'login' in fields:
            row.login = (fields['login'] or "").strip() or None
        if 'password' in fields:
            row.password = (fields['password'] or "").strip() or None
        session.commit()
        session.refresh(row)
        return row.to_dict()
    finally:
        session.close()


def _delete_account(model, account_id: int):
    session = get_session()
    try:
        row = session.query(model).filter(model.id == account_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Konto nie istnieje.")
        # Free the store reference if the account was in use.
        if row.store_id:
            store = session.query(ShopifyStore).filter(ShopifyStore.id == row.store_id).first()
            if store:
                field = 'gmc_account_id' if model is GmcAccount else 'ads_account_id'
                if getattr(store, field) == account_id:
                    setattr(store, field, None)
        session.delete(row)
        session.commit()
        return {"deleted": account_id}
    finally:
        session.close()


@router.get("/api/gmc-accounts")
def list_gmc_accounts():
    return _list_accounts(GmcAccount)


@router.post("/api/gmc-accounts")
def create_gmc_account(data: AccountCreate):
    return _create_account(GmcAccount, data)


@router.put("/api/gmc-accounts/{account_id}")
def update_gmc_account(account_id: int, data: AccountUpdate):
    return _update_account(GmcAccount, account_id, data)


@router.delete("/api/gmc-accounts/{account_id}")
def delete_gmc_account(account_id: int):
    return _delete_account(GmcAccount, account_id)


@router.get("/api/ads-accounts")
def list_ads_accounts():
    return _list_accounts(AdsAccount)


@router.post("/api/ads-accounts")
def create_ads_account(data: AccountCreate):
    return _create_account(AdsAccount, data)


@router.put("/api/ads-accounts/{account_id}")
def update_ads_account(account_id: int, data: AccountUpdate):
    return _update_account(AdsAccount, account_id, data)


@router.delete("/api/ads-accounts/{account_id}")
def delete_ads_account(account_id: int):
    return _delete_account(AdsAccount, account_id)
