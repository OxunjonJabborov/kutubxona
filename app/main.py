import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from . import config
from .database import Appeal, Base, SessionLocal, User, engine
from .security import DUMMY_HASH, hash_password, verify_password

BASE_DIR = Path(__file__).resolve().parent
TASHKENT = ZoneInfo("Asia/Tashkent")


def seed_user(db: Session) -> None:
    """Topshiriq talabi: foydalanuvchi bazada, parol faqat xesh ko'rinishida."""
    if len(config.SEED_PASSWORD) != 12:
        print("OGOHLANTIRISH: parol 12 belgidan iborat bo'lishi kerak")
    user = db.scalar(select(User).where(User.username == config.SEED_USERNAME))
    if user is None:
        user = User(
            username=config.SEED_USERNAME,
            password_hash=hash_password(config.SEED_PASSWORD),
        )
        db.add(user)
    user.full_name = config.SEED_FULL_NAME
    user.group_name = config.SEED_GROUP
    user.faculty = config.SEED_FACULTY
    user.age = config.SEED_AGE
    db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_user(db)
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    session_cookie="sid",
    max_age=config.SESSION_MAX_AGE,
    same_site="lax",
    https_only=config.HTTPS_ONLY,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


def local_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(TASHKENT).strftime("%d.%m.%Y %H:%M")


templates.env.filters["local_dt"] = local_dt


# ---------- yordamchilar ----------
def get_db():
    with SessionLocal() as db:
        yield db


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("uid")
    return db.get(User, user_id) if user_id is not None else None


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


def csrf_ok(request: Request, token: str) -> bool:
    expected = request.session.get("csrf")
    return bool(expected) and secrets.compare_digest(expected, token or "")


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def cabinet_response(request, db, user, status_code=200, **extra):
    appeals = db.scalars(
        select(Appeal).where(Appeal.user_id == user.id).order_by(Appeal.id.desc())
    ).all()
    context = {
        "user": user,
        "appeals": appeals,
        "csrf": csrf_token(request),
        "sent": request.query_params.get("sent") == "1",
        "error": None,
        "form": {"book_title": "", "message": ""},
        **extra,
    }
    # Chiqishdan keyin "orqaga" tugmasi kabinetni keshdan ko'rsatmasligi uchun
    return templates.TemplateResponse(
        request, "cabinet.html", context, status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


# ---------- yo'nalishlar ----------
@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"


@app.get("/")
def index(user: User | None = Depends(get_current_user)):
    return redirect("/cabinet" if user else "/login")


@app.get("/login")
def login_page(request: Request, user: User | None = Depends(get_current_user)):
    if user:
        return redirect("/cabinet")
    return templates.TemplateResponse(
        request, "login.html", {"csrf": csrf_token(request), "error": None, "username": ""}
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    csrf: str = Form(""),
    db: Session = Depends(get_db),
):
    username = username.strip()
    user = db.scalar(select(User).where(User.username == username)) if username else None
    # Parol serverda tekshiriladi: bazadagi xesh bilan solishtiriladi
    valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
    if not csrf_ok(request, csrf) or user is None or not valid:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"csrf": csrf_token(request), "error": "Login yoki parol noto‘g‘ri.", "username": username},
            status_code=401,
        )
    request.session.clear()  # eski sessiyani almashtirish
    request.session["uid"] = user.id
    csrf_token(request)
    return redirect("/cabinet")


@app.get("/cabinet")
def cabinet(
    request: Request,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user is None:
        return redirect("/login")
    return cabinet_response(request, db, user)


@app.post("/appeals")
def create_appeal(
    request: Request,
    book_title: str = Form(""),
    message: str = Form(""),
    csrf: str = Form(""),
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user is None:
        return redirect("/login")
    book_title, message = book_title.strip(), message.strip()
    error = None
    if not csrf_ok(request, csrf):
        error = "Sessiya eskirgan. Sahifani yangilab, qayta urinib ko‘ring."
    elif not 2 <= len(book_title) <= 200:
        error = "Kitob nomi 2 tadan 200 tagacha belgidan iborat bo‘lsin."
    elif not 10 <= len(message) <= 2000:
        error = "Murojaat matni 10 tadan 2000 tagacha belgidan iborat bo‘lsin."
    if error:
        return cabinet_response(
            request, db, user, status_code=422, error=error,
            form={"book_title": book_title, "message": message},
        )
    db.add(Appeal(user_id=user.id, book_title=book_title, message=message))
    db.commit()
    return redirect("/cabinet?sent=1")


@app.post("/logout")
def logout(request: Request, csrf: str = Form("")):
    if csrf_ok(request, csrf):
        request.session.clear()
    return redirect("/login")
