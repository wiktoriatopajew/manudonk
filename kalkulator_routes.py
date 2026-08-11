"""
GMC countdown calculators (/kalkulator)

Internal tool: each timer answers "products went into GMC at X, when can I run
the ad?". Stored in its own `gmc_timers` table so nothing here can touch the
shop's data.
"""
import asyncio
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func

from database.models import GmcTimer, get_session

router = APIRouter(prefix="/api/kalkulator", tags=["kalkulator"])

MAX_TIMERS = GmcTimer.MAX_TIMERS
DEFAULT_OFFSET_HOURS = 19.0
DEFAULT_NOTIFY_EMAIL = os.getenv("KALKULATOR_NOTIFY_EMAIL", "wiktoriatopajew@gmail.com")

# How often the worker looks for finished timers, and how far back it is still
# worth mailing about one - after a long outage nobody wants a burst of stale
# "you can run the ad now" mails for windows that closed days ago.
NOTIFY_POLL_SECONDS = 30
NOTIFY_MAX_LATE_HOURS = 24
NOTIFY_RETRY_MINUTES = 5  # after a rejected send, wait before trying again

# timer id -> earliest next attempt, kept in memory: a restart may retry sooner,
# which is the harmless direction.
_retry_after = {}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Times are stored in UTC but every reader of these mails lives in Poland.
try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo(os.getenv("KALKULATOR_TZ", "Europe/Warsaw"))
except Exception as e:  # missing tzdata in a slim image
    print(f"⚠️  Kalkulator: timezone database unavailable ({e}), falling back to UTC+02:00")
    LOCAL_TZ = timezone(timedelta(hours=2))

PL_DAYS = ['pon.', 'wt.', 'śr.', 'czw.', 'pt.', 'sob.', 'niedz.']
PL_MONTHS = ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca',
             'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia']


def _to_naive_utc(value: datetime) -> datetime:
    """Normalize an incoming instant to naive UTC, matching the rest of the schema."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _format_pl(dt_utc: datetime) -> str:
    """Render a stored UTC instant as Polish local time, e.g. 'wt. 12 sierpnia 2026, 15:00'"""
    local = dt_utc.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)
    return (f"{PL_DAYS[local.weekday()]} {local.day} {PL_MONTHS[local.month - 1]} "
            f"{local.year}, {local.strftime('%H:%M')}")


def _clean_email(value: Optional[str]) -> Optional[str]:
    """Empty input clears the notification; anything else must look like an address."""
    email = (value or "").strip()
    if not email:
        return None
    if not EMAIL_RE.match(email) or len(email) > 255:
        raise HTTPException(status_code=400, detail=f"Niepoprawny adres e-mail: {email}")
    return email


class TimerCreate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=80)
    start_at: Optional[datetime] = None
    offset_hours: float = Field(default=DEFAULT_OFFSET_HOURS, ge=0, le=8760)
    note: Optional[str] = Field(default=None, max_length=255)
    notify_email: Optional[str] = Field(default=None, max_length=255)


class TimerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=80)
    start_at: Optional[datetime] = None
    offset_hours: Optional[float] = Field(default=None, ge=0, le=8760)
    note: Optional[str] = Field(default=None, max_length=255)
    notify_email: Optional[str] = Field(default=None, max_length=255)


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

        notify_email = (_clean_email(data.notify_email) if data.notify_email is not None
                        else DEFAULT_NOTIFY_EMAIL)

        timer = GmcTimer(
            name=name[:80],
            start_at=start_at,
            offset_hours=data.offset_hours,
            note=(data.note or None),
            notify_email=notify_email,
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
            timer.notified_at = None  # a new schedule re-arms the email
        if 'offset_hours' in fields and fields['offset_hours'] is not None:
            timer.offset_hours = fields['offset_hours']
            timer.notified_at = None
        if 'note' in fields:
            note = (fields['note'] or "").strip()
            timer.note = note[:255] or None
        if 'notify_email' in fields:
            timer.notify_email = _clean_email(fields['notify_email'])

        session.commit()
        session.refresh(timer)
        return timer.to_dict()
    finally:
        session.close()


@router.post("/{timer_id}/test-email")
async def send_test_email(timer_id: int):
    """Send the notification right now, so delivery can be verified without waiting"""
    session = get_session()
    try:
        timer = session.query(GmcTimer).filter(GmcTimer.id == timer_id).first()
        if not timer:
            raise HTTPException(status_code=404, detail="Kalkulator nie istnieje")
        if not timer.notify_email:
            raise HTTPException(status_code=400, detail="Ten kalkulator nie ma ustawionego adresu e-mail")

        payload = _email_payload(timer)
    finally:
        session.close()

    sent = await asyncio.to_thread(_send_email, payload)
    if not sent:
        raise HTTPException(
            status_code=502,
            detail="Nie udało się wysłać e-maila. Sprawdź BREVO_API_KEY w Railway — szczegóły są w logach."
        )
    return {"sent_to": payload['to_email']}


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


# ---------------------------------------------------------------------------
# Background notifier
# ---------------------------------------------------------------------------

def _email_payload(timer: GmcTimer) -> dict:
    """Everything the mail needs, read while the session is still open."""
    return {
        'timer_id': timer.id,
        'to_email': timer.notify_email,
        'timer_name': timer.name,
        'uploaded_at': _format_pl(timer.start_at),
        'ready_at': _format_pl(timer.target_at),
        'offset_hours': timer.offset_hours,
        'note': timer.note,
    }


def _send_email(payload: dict) -> bool:
    """Blocking send - always call through asyncio.to_thread from the loop."""
    # Imported lazily so a mail-config problem can never break page rendering.
    from email_utils import send_gmc_timer_ready_email
    fields = {k: v for k, v in payload.items() if k != 'timer_id'}
    try:
        return bool(send_gmc_timer_ready_email(**fields))
    except Exception as e:
        print(f"❌ Kalkulator: email send failed for {payload.get('to_email')}: {e}")
        return False


def _collect_due_timers():
    """
    Timers past zero that still owe an email.

    Anything that finished more than NOTIFY_MAX_LATE_HOURS ago is marked as
    handled without sending: after downtime those mails would be noise, and
    the card already shows GOTOWE.
    """
    session = get_session()
    due = []
    try:
        now = datetime.utcnow()
        stamped_any = False
        candidates = session.query(GmcTimer).filter(
            GmcTimer.notified_at.is_(None),
            GmcTimer.notify_email.isnot(None),
        ).all()

        for timer in candidates:
            target = timer.target_at
            if target > now:
                continue
            if now - target <= timedelta(hours=NOTIFY_MAX_LATE_HOURS):
                if _retry_after.get(timer.id, now) <= now:
                    due.append(_email_payload(timer))
            else:
                # Stamped here and only here: giving up is final, delivery is not.
                print(f"⏭️  Kalkulator: '{timer.name}' finished {now - target} ago - marking without email")
                timer.notified_at = now
                stamped_any = True

        if stamped_any:
            session.commit()
    finally:
        session.close()
    return due


def _mark_notified(timer_id: int):
    """Stamp only after the provider accepted the message."""
    session = get_session()
    try:
        timer = session.query(GmcTimer).filter(GmcTimer.id == timer_id).first()
        if timer:
            timer.notified_at = datetime.utcnow()
            session.commit()
    finally:
        session.close()


async def _notify_loop():
    """Poll for finished timers and mail them out (single uvicorn worker => no dupes)."""
    while True:
        try:
            due = await asyncio.to_thread(_collect_due_timers)
            for payload in due:
                timer_id = payload['timer_id']
                if await asyncio.to_thread(_send_email, payload):
                    await asyncio.to_thread(_mark_notified, timer_id)
                    _retry_after.pop(timer_id, None)
                    print(f"✅ Kalkulator: notification sent for '{payload['timer_name']}'")
                else:
                    # Not stamped, so a fixed mail provider still delivers this
                    # one - but back off instead of retrying every poll.
                    _retry_after[timer_id] = datetime.utcnow() + timedelta(minutes=NOTIFY_RETRY_MINUTES)
                    print(f"⚠️  Kalkulator: delivery failed for '{payload['timer_name']}', "
                          f"retrying in {NOTIFY_RETRY_MINUTES} min")
        except Exception as e:
            print(f"⚠️  Kalkulator notifier error: {e}")
        await asyncio.sleep(NOTIFY_POLL_SECONDS)


def start_notifier():
    """Called from the app startup event"""
    asyncio.create_task(_notify_loop())
    print(f"⏱ Kalkulator: notifier running (every {NOTIFY_POLL_SECONDS}s, default → {DEFAULT_NOTIFY_EMAIL})")
