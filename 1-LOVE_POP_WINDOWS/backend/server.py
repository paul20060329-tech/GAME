import argparse
import json
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, desc, func, insert, select, text
from sqlalchemy.engine import Engine

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_env(name: str) -> Optional[str]:
    value = os.environ.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _clamp_len(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[:limit]


def _safe_json_loads(raw: bytes) -> Dict[str, object]:
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _guess_type(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".html"):
        return "text/html; charset=utf-8"
    if lower.endswith(".css"):
        return "text/css; charset=utf-8"
    if lower.endswith(".js"):
        return "application/javascript; charset=utf-8"
    if lower.endswith(".json"):
        return "application/json; charset=utf-8"
    if lower.endswith(".svg"):
        return "image/svg+xml"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


@dataclass(frozen=True)
class AdminConfig:
    username: str
    password: Optional[str]


class Store:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine = self._create_engine(database_url)
        self.metadata = MetaData()
        self.survey = Table(
            "survey",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("created_at", String, nullable=False),
            Column("name", String),
            Column("age_range", String),
            Column("gender", String),
            Column("city", String),
            Column("occupation", String),
            Column("contact", String),
            Column("purpose", String),
            Column("feedback", String),
            Column("consent", Integer, nullable=False),
            Column("user_agent", String),
            Column("ip", String),
        )
        self.metadata.create_all(self.engine)
        self._ensure_indexes()

    def _create_engine(self, database_url: str) -> Engine:
        connect_args: Dict[str, object] = {}
        if database_url.startswith("sqlite:"):
            connect_args["check_same_thread"] = False
        return create_engine(database_url, pool_pre_ping=True, future=True, connect_args=connect_args)

    def _ensure_indexes(self) -> None:
        with self.engine.begin() as conn:
            if self.database_url.startswith("sqlite:"):
                conn.execute(text("create index if not exists idx_survey_created_at on survey(created_at)"))
                conn.execute(
                    text(
                        """
                        create table if not exists reviews (
                            id integer primary key autoincrement,
                            created_at text not null,
                            name text,
                            score integer,
                            comment text,
                            ip text
                        )
                        """
                    )
                )
                conn.execute(text("create index if not exists idx_reviews_created_at on reviews(created_at)"))
            else:
                conn.execute(text("create index if not exists idx_survey_created_at on survey(created_at)"))
                conn.execute(
                    text(
                        """
                        create table if not exists reviews (
                            id serial primary key,
                            created_at text not null,
                            name text,
                            score integer,
                            comment text,
                            ip text
                        )
                        """
                    )
                )
                conn.execute(text("create index if not exists idx_reviews_created_at on reviews(created_at)"))

    def insert_survey(self, payload: Dict[str, object], *, user_agent: str, ip: str) -> int:
        name = _clamp_len(str(payload.get("name") or "").strip(), 80)
        age_range = _clamp_len(str(payload.get("ageRange") or "").strip(), 40)
        gender = _clamp_len(str(payload.get("gender") or "").strip(), 40)
        city = _clamp_len(str(payload.get("city") or "").strip(), 80)
        occupation = _clamp_len(str(payload.get("occupation") or "").strip(), 80)
        contact = _clamp_len(str(payload.get("contact") or "").strip(), 120)
        purpose = _clamp_len(str(payload.get("purpose") or "").strip(), 240)
        feedback = _clamp_len(str(payload.get("feedback") or "").strip(), 2000)
        consent = 1 if bool(payload.get("consent")) else 0
        created_at = _utc_now_iso()

        with self.engine.begin() as conn:
            result = conn.execute(
                insert(self.survey).values(
                    created_at=created_at,
                    name=name,
                    age_range=age_range,
                    gender=gender,
                    city=city,
                    occupation=occupation,
                    contact=contact,
                    purpose=purpose,
                    feedback=feedback,
                    consent=consent,
                    user_agent=_clamp_len(user_agent, 320),
                    ip=_clamp_len(ip, 80),
                )
            )
            try:
                return int(result.inserted_primary_key[0])
            except Exception:
                row_id = result.scalar_one_or_none()
                return int(row_id or 0)

    def insert_review(self, payload: Dict[str, object], *, ip: str) -> int:
        name = _clamp_len(str(payload.get("name") or "匿名用户").strip(), 80)
        try:
            score = int(payload.get("score") or 5)
        except Exception:
            score = 5
        score = max(1, min(score, 5))
        comment = _clamp_len(str(payload.get("comment") or "").strip(), 2000)
        created_at = _utc_now_iso()

        with self.engine.begin() as conn:
            cur = conn.execute(
                text(
                    """
                    insert into reviews (
                        created_at, name, score, comment, ip
                    ) values (:created_at, :name, :score, :comment, :ip)
                    """
                ),
                {
                    "created_at": created_at,
                    "name": name,
                    "score": score,
                    "comment": comment,
                    "ip": _clamp_len(ip, 80),
                },
            )
            try:
                return int(cur.lastrowid)
            except Exception:
                return 0

    def list_reviews(self, *, limit: int = 100) -> List[Dict[str, object]]:
        limit = max(1, min(limit, 500))
        with self.engine.connect() as conn:
            cur = conn.execute(
                text(
                    """
                    select
                        id, created_at, name, score, comment, ip
                    from reviews
                    order by id desc
                    limit :limit
                    """
                ),
                {"limit": limit},
            )
            return [dict(r._mapping) for r in cur.fetchall()]

    def list_surveys(self, *, limit: int = 200) -> List[Dict[str, object]]:
        limit = max(1, min(limit, 2000))
        with self.engine.begin() as conn:
            rows = (
                conn.execute(
                    select(
                        self.survey.c.id,
                        self.survey.c.created_at,
                        self.survey.c.name,
                        self.survey.c.age_range,
                        self.survey.c.gender,
                        self.survey.c.city,
                        self.survey.c.occupation,
                        self.survey.c.contact,
                        self.survey.c.purpose,
                        self.survey.c.feedback,
                        self.survey.c.consent,
                        self.survey.c.user_agent,
                        self.survey.c.ip,
                    )
                    .order_by(desc(self.survey.c.id))
                    .limit(limit)
                )
                .mappings()
                .all()
            )
            return list(rows)

    def stats(self) -> Dict[str, object]:
        with self.engine.begin() as conn:
            total = int(conn.execute(select(func.count()).select_from(self.survey)).scalar_one())
            today_prefix = datetime.now(timezone.utc).date().isoformat()
            today = int(
                conn.execute(
                    select(func.count())
                    .select_from(self.survey)
                    .where(self.survey.c.created_at.like(f"{today_prefix}%"))
                ).scalar_one()
            )
            age = conn.execute(
                select(self.survey.c.age_range.label("k"), func.count().label("c"))
                .select_from(self.survey)
                .group_by(self.survey.c.age_range)
                .order_by(desc("c"))
            ).mappings().all()
            gender = conn.execute(
                select(self.survey.c.gender.label("k"), func.count().label("c"))
                .select_from(self.survey)
                .group_by(self.survey.c.gender)
                .order_by(desc("c"))
            ).mappings().all()
            city = conn.execute(
                select(self.survey.c.city.label("k"), func.count().label("c"))
                .select_from(self.survey)
                .group_by(self.survey.c.city)
                .order_by(desc("c"))
                .limit(8)
            ).mappings().all()
        return {
            "total": total,
            "today": today,
            "ageRange": [(r["k"] or "未填写", int(r["c"])) for r in age],
            "gender": [(r["k"] or "未填写", int(r["c"])) for r in gender],
            "topCities": [(r["k"] or "未填写", int(r["c"])) for r in city],
        }


class Sessions:
    def __init__(self) -> None:
        self._sessions: Dict[str, float] = {}

    def create(self, *, ttl_seconds: int = 6 * 60 * 60) -> str:
        sid = secrets.token_urlsafe(24)
        self._sessions[sid] = time.time() + ttl_seconds
        return sid

    def validate(self, sid: str) -> bool:
        exp = self._sessions.get(sid)
        if exp is None:
            return False
        if time.time() > exp:
            self._sessions.pop(sid, None)
            return False
        return True

    def delete(self, sid: str) -> None:
        self._sessions.pop(sid, None)


def _parse_cookies(header: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for part in header.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _parse_origins(value: Optional[str]) -> List[str]:
    if value is None:
        return []
    value = value.strip()
    if not value:
        return []
    parts = [p.strip() for p in value.split(",")]
    return [p for p in parts if p]


def _read_body(handler: BaseHTTPRequestHandler, *, limit: int = 64_000) -> bytes:
    length_raw = handler.headers.get("Content-Length", "0").strip()
    try:
        length = int(length_raw)
    except ValueError:
        length = 0
    length = max(0, min(length, limit))
    if length == 0:
        return b""
    return handler.rfile.read(length)


def _iter_rows_csv(rows: Iterable[Mapping[str, object]]) -> Iterable[str]:
    header = [
        "id",
        "created_at",
        "name",
        "age_range",
        "gender",
        "city",
        "occupation",
        "contact",
        "purpose",
        "feedback",
        "consent",
        "ip",
        "user_agent",
    ]
    yield ",".join(header) + "\n"
    for r in rows:
        values = [str(r.get(k, "") or "") for k in header]
        escaped = []
        for v in values:
            v = v.replace('"', '""')
            if any(ch in v for ch in [",", "\n", "\r", '"']):
                v = f'"{v}"'
            escaped.append(v)
        yield ",".join(escaped) + "\n"


def _admin_login_page(*, message: str) -> bytes:
    msg = _html_escape(message)
    html = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Admin Login</title>
    <style>
      body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; font-family: "Microsoft YaHei", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: #fff6fa; color: rgba(20, 22, 26, 0.92); }}
      .card {{ width: min(420px, calc(100vw - 40px)); padding: 18px; border-radius: 18px; border: 1px solid rgba(255, 179, 198, 0.55); background: rgba(255, 255, 255, 0.75); box-shadow: 0 20px 55px rgba(16, 18, 22, 0.12); }}
      h1 {{ margin: 0 0 12px; font-size: 18px; }}
      .msg {{ margin: 0 0 12px; color: rgba(20, 22, 26, 0.62); font-size: 12px; }}
      label {{ display: grid; gap: 6px; margin: 10px 0; font-size: 12px; font-weight: 800; color: rgba(20, 22, 26, 0.72); }}
      input {{ padding: 10px 12px; border-radius: 14px; border: 1px solid rgba(20, 22, 26, 0.14); background: rgba(255, 255, 255, 0.85); font-weight: 800; }}
      button {{ width: 100%; margin-top: 12px; padding: 10px 12px; border-radius: 14px; border: 1px solid rgba(255, 179, 198, 0.65); background: linear-gradient(135deg, rgba(255, 209, 220, 0.88), rgba(205, 239, 253, 0.78)); font-weight: 900; cursor: pointer; }}
      .foot {{ margin-top: 10px; font-size: 12px; color: rgba(20, 22, 26, 0.5); }}
      a {{ color: rgba(255, 77, 109, 0.9); text-decoration: none; font-weight: 900; }}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>管理员登录</h1>
      <p class="msg">{msg}</p>
      <form method="post" action="/admin/login">
        <label>用户名<input name="username" autocomplete="username" /></label>
        <label>密码<input name="password" type="password" autocomplete="current-password" /></label>
        <button type="submit">登录</button>
      </form>
      <div class="foot"><a href="/">返回网站</a></div>
    </div>
  </body>
</html>"""
    return html.encode("utf-8")


def _admin_dashboard_page(*, stats: Dict[str, object], rows: List[sqlite3.Row]) -> bytes:
    def _pairs(items: List[Tuple[str, int]]) -> str:
        chunks = []
        for k, c in items[:12]:
            chunks.append(f"<span class='pill'><b>{_html_escape(k)}</b><em>{c}</em></span>")
        return "".join(chunks) if chunks else "<span class='muted'>暂无</span>"

    total = int(stats.get("total") or 0)
    today = int(stats.get("today") or 0)
    age = stats.get("ageRange") or []
    gender = stats.get("gender") or []
    cities = stats.get("topCities") or []

    trs = []
    for r in rows:
        trs.append(
            "<tr>"
            f"<td>{r['id']}</td>"
            f"<td>{_html_escape(str(r['created_at'] or ''))}</td>"
            f"<td>{_html_escape(str(r['name'] or ''))}</td>"
            f"<td>{_html_escape(str(r['age_range'] or ''))}</td>"
            f"<td>{_html_escape(str(r['gender'] or ''))}</td>"
            f"<td>{_html_escape(str(r['city'] or ''))}</td>"
            f"<td>{_html_escape(str(r['occupation'] or ''))}</td>"
            f"<td>{_html_escape(str(r['purpose'] or ''))}</td>"
            f"<td>{_html_escape(str(r['contact'] or ''))}</td>"
            "</tr>"
        )

    table = "".join(trs) if trs else "<tr><td colspan='9' class='muted'>暂无数据</td></tr>"

    html = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Admin</title>
    <style>
      body {{ margin: 0; font-family: "Microsoft YaHei", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: #fff6fa; color: rgba(20, 22, 26, 0.92); }}
      header {{ position: sticky; top: 0; padding: 14px 16px; display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(16px); border-bottom: 1px solid rgba(255, 179, 198, 0.35); }}
      h1 {{ margin: 0; font-size: 16px; }}
      .btns {{ display: flex; gap: 10px; }}
      a.btn, button.btn {{ display: inline-flex; align-items: center; justify-content: center; padding: 9px 12px; border-radius: 14px; border: 1px solid rgba(20, 22, 26, 0.14); background: rgba(255, 255, 255, 0.75); color: rgba(20, 22, 26, 0.9); text-decoration: none; font-weight: 900; cursor: pointer; }}
      a.btn.primary {{ border-color: rgba(255, 179, 198, 0.65); background: linear-gradient(135deg, rgba(255, 209, 220, 0.88), rgba(205, 239, 253, 0.78)); }}
      main {{ padding: 16px; display: grid; gap: 14px; }}
      .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
      .card {{ padding: 14px; border-radius: 18px; border: 1px solid rgba(255, 179, 198, 0.35); background: rgba(255, 255, 255, 0.75); box-shadow: 0 20px 55px rgba(16, 18, 22, 0.08); }}
      .kpi {{ display: flex; gap: 12px; align-items: baseline; }}
      .kpi b {{ font-size: 30px; letter-spacing: .3px; }}
      .kpi span {{ color: rgba(20, 22, 26, 0.6); font-weight: 800; }}
      .muted {{ color: rgba(20, 22, 26, 0.56); font-weight: 800; }}
      .pillRow {{ display: flex; flex-wrap: wrap; gap: 8px; }}
      .pill {{ display: inline-flex; gap: 8px; align-items: baseline; padding: 7px 10px; border-radius: 999px; border: 1px solid rgba(20, 22, 26, 0.12); background: rgba(255, 255, 255, 0.85); }}
      .pill b {{ font-size: 12px; }}
      .pill em {{ font-style: normal; color: rgba(20, 22, 26, 0.56); font-weight: 900; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 10px 10px; border-bottom: 1px solid rgba(20, 22, 26, 0.08); vertical-align: top; }}
      th {{ text-align: left; font-size: 12px; color: rgba(20, 22, 26, 0.62); }}
      td {{ font-size: 12px; }}
      .tableWrap {{ overflow: auto; border-radius: 14px; border: 1px solid rgba(20, 22, 26, 0.08); background: rgba(255, 255, 255, 0.8); }}
      form {{ margin: 0; }}
      @media (max-width: 960px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <header>
      <h1>用户调查后台</h1>
      <div class="btns">
        <a class="btn" href="/">回到网站</a>
        <a class="btn primary" href="/admin/export.csv">导出调查 CSV</a>
        <a class="btn primary" href="/admin/export_reviews.csv" style="background:#fff3b0; color:#111; border-color:#ffe7c7;">导出评价 CSV</a>
        <form method="post" action="/admin/logout"><button class="btn" type="submit">退出</button></form>
      </div>
    </header>
    <main>
      <section class="grid">
        <div class="card">
          <div class="muted">总提交数</div>
          <div class="kpi"><b>{total}</b><span>条</span></div>
        </div>
        <div class="card">
          <div class="muted">今天(UTC)</div>
          <div class="kpi"><b>{today}</b><span>条</span></div>
        </div>
        <div class="card">
          <div class="muted">Top 城市</div>
          <div class="pillRow">{_pairs(cities)}</div>
        </div>
      </section>

      <section class="grid">
        <div class="card">
          <div class="muted">年龄段</div>
          <div class="pillRow">{_pairs(age)}</div>
        </div>
        <div class="card">
          <div class="muted">性别</div>
          <div class="pillRow">{_pairs(gender)}</div>
        </div>
        <div class="card">
          <div class="muted">最近提交</div>
          <div class="muted">默认显示最近 200 条</div>
        </div>
      </section>

      <section class="card">
        <div class="tableWrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>时间(UTC)</th>
                <th>姓名/昵称</th>
                <th>年龄段</th>
                <th>性别</th>
                <th>城市</th>
                <th>职业</th>
                <th>用途</th>
                <th>联系方式</th>
              </tr>
            </thead>
            <tbody>
              {table}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </body>
</html>"""
    return html.encode("utf-8")


class App:
    def __init__(self, *, root_dir: Path, store: Store, sessions: Sessions, admin: AdminConfig) -> None:
        self.root_dir = root_dir
        self.web_dir = root_dir / "web"
        self.store = store
        self.sessions = sessions
        self.admin = admin

    def static_path(self, req_path: str) -> Optional[Path]:
        if req_path == "/":
            candidate = self.web_dir / "index.html"
        else:
            rel = req_path.lstrip("/")
            rel = unquote(rel)
            if ".." in rel.replace("\\", "/").split("/"):
                return None
            candidate = self.web_dir / rel
        try:
            resolved = candidate.resolve()
        except Exception:
            return None
        if self.web_dir not in resolved.parents and resolved != self.web_dir:
            return None
        if not resolved.exists() or not resolved.is_file():
            return None
        return resolved


class Handler(BaseHTTPRequestHandler):
    server_version = "LovePopUpHTTP/1.0"

    def _app(self) -> App:
        return self.server.app  # type: ignore[attr-defined]

    def _send(self, status: int, body: bytes, *, content_type: str, headers: Optional[List[Tuple[str, str]]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if headers:
            for k, v in headers:
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _json(self, status: int, data: Dict[str, object], *, headers: Optional[List[Tuple[str, str]]] = None) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, raw, content_type="application/json; charset=utf-8", headers=headers)

    def _cors_headers_for_api(self) -> List[Tuple[str, str]]:
        origin = (self.headers.get("Origin") or "").strip()
        allow = _read_env("CORS_ALLOW_ORIGINS")
        allow_list = _parse_origins(allow)

        headers: List[Tuple[str, str]] = [
            ("Access-Control-Allow-Methods", "POST, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type"),
            ("Access-Control-Max-Age", "600"),
        ]

        if not origin:
            return headers

        if allow == "*":
            headers.append(("Access-Control-Allow-Origin", "*"))
            return headers

        if origin in allow_list:
            headers.append(("Access-Control-Allow-Origin", origin))
            headers.append(("Vary", "Origin"))
        return headers

    def _is_admin(self) -> bool:
        cookie = self.headers.get("Cookie") or ""
        sid = _parse_cookies(cookie).get("sid") or ""
        return bool(sid) and self._app().sessions.validate(sid)

    def _client_ip(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0]

    def do_OPTIONS(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/survey" or path == "/api/reviews":
            headers = self._cors_headers_for_api()
            headers.append(("Access-Control-Allow-Methods", "POST, OPTIONS"))
            headers.append(("Access-Control-Allow-Headers", "Content-Type"))
            self._send(204, b"", content_type="text/plain", headers=headers)
            return
        self._send(204, b"", content_type="text/plain")

    def do_GET(self) -> None:
        app = self._app()
        path = urlparse(self.path).path

        if path == "/api/reviews":
            rows = app.store.list_reviews(limit=50)
            data = [{"name": r["name"], "score": r["score"], "comment": r["comment"], "created_at": r["created_at"]} for r in rows]
            self._json(200, {"ok": True, "data": data}, headers=_cors_headers())
            return

        if path == "/health":
            self._json(200, {"ok": True})
            return

        if path == "/admin" or path == "/admin/":
            if not self._is_admin():
                self._redirect("/admin/login")
                return
            stats = app.store.stats()
            rows = app.store.list_surveys(limit=200)
            self._send(200, _admin_dashboard_page(stats=stats, rows=rows), content_type="text/html; charset=utf-8")
            return

        if path == "/admin/login":
            if self._is_admin():
                self._redirect("/admin")
                return
            message = "请输入管理员账号"
            if app.admin.password is None:
                message = "未设置 ADMIN_PASSWORD，当前无法登录后台。请先在环境变量中设置 ADMIN_PASSWORD。"
            self._send(200, _admin_login_page(message=message), content_type="text/html; charset=utf-8")
            return

        if path == "/admin/export_reviews.csv":
            if not self._is_admin():
                self._redirect("/admin/login")
                return
            rows = app.store.list_reviews(limit=2000)
            header = "id,created_at,name,score,comment\n"
            lines = [header]
            for r in rows:
                v_id = str(r.get("id", ""))
                v_at = str(r.get("created_at", ""))
                v_name = str(r.get("name", "")).replace('"', '""')
                v_score = str(r.get("score", ""))
                v_comment = str(r.get("comment", "")).replace('"', '""')
                lines.append(f'{v_id},{v_at},"{v_name}",{v_score},"{v_comment}"\n')
            raw = "".join(lines).encode("utf-8")
            headers = [("Content-Disposition", 'attachment; filename="reviews.csv"')]
            self._send(200, raw, content_type="text/csv; charset=utf-8", headers=headers)
            return

        if path == "/admin/export.csv":
            if not self._is_admin():
                self._redirect("/admin/login")
                return
            rows = app.store.list_surveys(limit=2000)
            raw = "".join(_iter_rows_csv(rows)).encode("utf-8")
            headers = [("Content-Disposition", 'attachment; filename="survey.csv"')]
            self._send(200, raw, content_type="text/csv; charset=utf-8", headers=headers)
            return

        file_path = app.static_path(path)
        if file_path is None:
            self._send(404, b"Not Found", content_type="text/plain; charset=utf-8")
            return
        try:
            raw = file_path.read_bytes()
        except Exception:
            self._send(500, b"Internal Server Error", content_type="text/plain; charset=utf-8")
            return
        self._send(200, raw, content_type=_guess_type(file_path.name))

    def do_POST(self) -> None:
        app = self._app()
        path = urlparse(self.path).path
        cors_headers = self._cors_headers_for_api()

        if path == "/api/reviews":
            raw = _read_body(self, limit=32_000)
            data = _safe_json_loads(raw)
            if not data.get("comment"):
                self._json(400, {"ok": False, "error": "comment_required"}, headers=cors_headers)
                return
            rec_id = app.store.insert_review(data, ip=self._client_ip())
            self._json(200, {"ok": True, "id": rec_id}, headers=cors_headers)
            return

        if path == "/api/survey":
            raw = _read_body(self, limit=96_000)
            data = _safe_json_loads(raw)
            consent = bool(data.get("consent"))
            if not consent:
                self._json(400, {"ok": False, "error": "consent_required"}, headers=cors_headers)
                return
            rec_id = app.store.insert_survey(data, user_agent=self.headers.get("User-Agent") or "", ip=self._client_ip())
            self._json(200, {"ok": True, "id": rec_id}, headers=cors_headers)
            return

        if path == "/admin/login":
            if app.admin.password is None:
                self._send(403, _admin_login_page(message="未设置 ADMIN_PASSWORD，无法登录。"), content_type="text/html; charset=utf-8")
                return
            raw = _read_body(self, limit=32_000)
            form = parse_qs(raw.decode("utf-8", errors="ignore"))
            username = (form.get("username") or [""])[0].strip()
            password = (form.get("password") or [""])[0]

            if username == app.admin.username and secrets.compare_digest(password, app.admin.password):
                sid = app.sessions.create()
                headers = [("Set-Cookie", f"sid={sid}; HttpOnly; SameSite=Lax; Path=/")]
                self._send(303, b"", content_type="text/plain; charset=utf-8", headers=headers + [("Location", "/admin")])
                return
            self._send(401, _admin_login_page(message="用户名或密码错误"), content_type="text/html; charset=utf-8")
            return

        if path == "/admin/logout":
            cookie = self.headers.get("Cookie") or ""
            sid = _parse_cookies(cookie).get("sid") or ""
            if sid:
                app.sessions.delete(sid)
            headers = [("Set-Cookie", "sid=; Max-Age=0; HttpOnly; SameSite=Lax; Path=/")]
            self._send(303, b"", content_type="text/plain; charset=utf-8", headers=headers + [("Location", "/admin/login")])
            return

        self._send(404, b"Not Found", content_type="text/plain; charset=utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5173)
    return p


def main() -> None:
    args = build_parser().parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    default_sqlite = (root_dir / "backend" / "data" / "survey.sqlite3").resolve()
    default_url = f"sqlite:///{default_sqlite.as_posix()}"
    database_url = _read_env("DATABASE_URL") or default_url
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://") :]
    store = Store(database_url)
    sessions = Sessions()

    admin_user = _read_env("ADMIN_USERNAME") or "admin"
    admin_pass = _read_env("ADMIN_PASSWORD")
    admin = AdminConfig(username=admin_user, password=admin_pass)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.app = App(root_dir=root_dir, store=store, sessions=sessions, admin=admin)  # type: ignore[attr-defined]
    print(f"Serving on http://{args.host}:{args.port}/")
    print("Admin:", f"http://{args.host}:{args.port}/admin")
    if admin_pass is None:
        print("Set ADMIN_PASSWORD to enable admin login.")
    server.serve_forever()


if __name__ == "__main__":
    main()
