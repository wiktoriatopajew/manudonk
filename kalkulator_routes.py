"""
GMC countdown calculators (/kalkulator)

Internal tool: each timer answers "products went into GMC at X, when can I run
the ad?". Stored in its own `gmc_timers` table so nothing here can touch the
shop's data.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func

from database.models import GmcTimer, get_session

router = APIRouter(prefix="/api/kalkulator", tags=["kalkulator"])

MAX_TIMERS = GmcTimer.MAX_TIMERS
DEFAULT_OFFSET_HOURS = 19.0


def _to_naive_utc(value: datetime) -> datetime:
    """Normalize an incoming instant to naive UTC, matching the rest of the schema."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


class TimerCreate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=80)
    start_at: Optional[datetime] = None
    offset_hours: float = Field(default=DEFAULT_OFFSET_HOURS, ge=0, le=8760)
    note: Optional[str] = Field(default=None, max_length=255)


class TimerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=80)
    start_at: Optional[datetime] = None
    offset_hours: Optional[float] = Field(default=None, ge=0, le=8760)
    note: Optional[str] = Field(default=None, max_length=255)


@router.get("")
@router.get("/")
async def list_timers():
    """All calculators, in display order"""
    session = get_session()
    try:
        timers = session.query(GmcTimer).order_by(
            GmcTimer.position.asc(), GmcTimer.id.asc()
        ).all()
        return {
            'timers': [t.to_dict() for t in timers],
            'max_timers': MAX_TIMERS,
            'server_time': datetime.utcnow().isoformat() + 'Z',
        }
    finally:
        session.close()


@router.post("")
@router.post("/")
async def create_timer(data: TimerCreate):
    """Add a calculator (hard-capped at MAX_TIMERS)"""
    session = get_session()
    try:
        count = session.query(func.count(GmcTimer.id)).scalar() or 0
        if count >= MAX_TIMERS:
            raise HTTPException(
                status_code=400,
                detail=f"Limit {MAX_TIMERS} kalkulatorow osiagniety. Usun jakis, zeby dodac nowy."
            )

        name = (data.name or "").strip() or f"GMC {count + 1}"
        start_at = _to_naive_utc(data.start_at) if data.start_at else datetime.utcnow()
        max_position = session.query(func.max(GmcTimer.position)).scalar()

        timer = GmcTimer(
            name=name[:80],
            start_at=start_at,
            offset_hours=data.offset_hours,
            note=(data.note or None),
            position=(max_position or 0) + 1,
        )
        session.add(timer)
        session.commit()
        session.refresh(timer)
        return timer.to_dict()
    finally:
        session.close()


@router.patch("/{timer_id}")
async def update_timer(timer_id: int, data: TimerUpdate):
    """Partial update - the UI autosaves single fields as they change"""
    session = get_session()
    try:
        timer = session.query(GmcTimer).filter(GmcTimer.id == timer_id).first()
        if not timer:
            raise HTTPException(status_code=404, detail="Kalkulator nie istnieje")

        # pydantic v2 renamed .dict() -> .model_dump(); requirements don't pin it
        fields = (data.model_dump(exclude_unset=True) if hasattr(data, 'model_dump')
                  else data.dict(exclude_unset=True))

        if 'name' in fields:
            name = (fields['name'] or "").strip()
            timer.name = (name or timer.name)[:80]
        if 'start_at' in fields and fields['start_at'] is not None:
            timer.start_at = _to_naive_utc(fields['start_at'])
        if 'offset_hours' in fields and fields['offset_hours'] is not None:
            timer.offset_hours = fields['offset_hours']
        if 'note' in fields:
            note = (fields['note'] or "").strip()
            timer.note = note[:255] or None

        session.commit()
        session.refresh(timer)
        return timer.to_dict()
    finally:
        session.close()


@router.delete("/{timer_id}")
async def delete_timer(timer_id: int):
    """Remove a calculator"""
    session = get_session()
    try:
        timer = session.query(GmcTimer).filter(GmcTimer.id == timer_id).first()
        if not timer:
            raise HTTPException(status_code=404, detail="Kalkulator nie istnieje")
        session.delete(timer)
        session.commit()
        return {"deleted": timer_id}
    finally:
        session.close()
