#!/usr/bin/env python3
"""Render weekly digest pages from reports/data/*.json and rebuild index.html.

Usage: python3 scripts/build.py            # render all
       python3 scripts/build.py --check    # validate data only

Data file format (reports/data/YYYY-MM-DD.json):
{
  "date": "2026-11-30",                       # run date (Monday)
  "period": {"from": "2026-11-23", "to": "2026-11-29"},
  "official": [Item], "media": [Item], "firms": [Item],
  "new_services": [{"firm": "...", "title": "...", "url": "..."}],
  "notes": ["free-text line", ...]            # e.g. sources that could not be read
}
Item = {"headline": "Short Russian headline", "url": "https://...",
        "source": "Gulf News", "date": "2026-11-25", "topic": "Налоги"}
"""
import html, json, pathlib, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "reports" / "data"
OUT = ROOT / "reports"
MAX_ITEMS = 50
SECTIONS = [
    ("official", "1. Официальные источники"),
    ("media", "2. СМИ и другие неофициальные источники"),
    ("firms", "3. Новости юридических фирм"),
]
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря"]

CSS = """
:root{--fg:#1d1d1f;--muted:#6e6e73;--line:#e5e5ea;--accent:#0b5cad;--bg:#fff;--chip:#f2f4f7}
@media (prefers-color-scheme:dark){:root{--fg:#f2f2f7;--muted:#a1a1a6;--line:#38383a;--accent:#64a8ff;--bg:#111;--chip:#1f1f22}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
main{max-width:820px;margin:0 auto;padding:32px 20px 64px}
header p{color:var(--muted);margin:4px 0 0}h1{font-size:26px;margin:0}h2{font-size:19px;margin:36px 0 8px;padding-bottom:6px;border-bottom:1px solid var(--line)}
ol{padding-left:22px;margin:0}li{margin:10px 0}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.meta{display:block;color:var(--muted);font-size:13px}.chip{display:inline-block;background:var(--chip);border-radius:6px;padding:0 6px;margin-right:6px;font-size:12px}
.empty{color:var(--muted);font-style:italic}.notes{color:var(--muted);font-size:14px}footer{margin-top:48px;color:var(--muted);font-size:13px}
.reports li{margin:6px 0}
"""


def ru_date(s):
    d = datetime.date.fromisoformat(s)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def page(title, body):
    return (f'<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><style>{CSS}</style></head><body><main>{body}'
            f'<footer>Автоматический обзор юридических и налоговых публикаций по ОАЭ. '
            f'<a href="/">Все выпуски</a></footer></main></body></html>')


def validate(d, name):
    errs = []
    total = sum(len(d.get(k, [])) for k, _ in SECTIONS)
    if total > MAX_ITEMS:
        errs.append(f"{name}: {total} items > {MAX_ITEMS}")
    seen = set()
    for k, _ in SECTIONS:
        for i, it in enumerate(d.get(k, [])):
            for f in ("headline", "url", "source"):
                if not it.get(f):
                    errs.append(f"{name}: {k}[{i}] missing {f}")
            u = it.get("url", "")
            if not u.startswith("http"):
                errs.append(f"{name}: {k}[{i}] bad url {u!r}")
            if u in seen:
                errs.append(f"{name}: duplicate url {u}")
            seen.add(u)
    return errs


def render_report(d):
    p = d["period"]
    body = [f'<header><h1>Обзор: право и налоги ОАЭ</h1>'
            f'<p>Неделя {ru_date(p["from"])} — {ru_date(p["to"])} · выпуск от {ru_date(d["date"])}</p></header>']
    for key, label in SECTIONS:
        items = d.get(key, [])
        body.append(f"<h2>{label}</h2>")
        if key == "firms" and d.get("new_services"):
            body.append("<p><strong>Новые разделы услуг на сайтах фирм:</strong></p><ul>")
            for s in d["new_services"]:
                body.append(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a>'
                            f'<span class="meta">{esc(s["firm"])}</span></li>')
            body.append("</ul><p><strong>Публикации:</strong></p>")
        if not items:
            body.append('<p class="empty">Нет отобранных публикаций за неделю.</p>')
            continue
        body.append("<ol>")
        for it in items:
            meta = esc(it["source"])
            if it.get("date"):
                meta += " · " + esc(ru_date(it["date"]))
            chip = f'<span class="chip">{esc(it["topic"])}</span>' if it.get("topic") else ""
            body.append(f'<li><a href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(it["headline"])}</a>'
                        f'<span class="meta">{chip}{meta}</span></li>')
        body.append("</ol>")
    if d.get("notes"):
        body.append('<h2>Примечания</h2><ul class="notes">' +
                    "".join(f"<li>{esc(n)}</li>" for n in d["notes"]) + "</ul>")
    return page(f'Обзор ОАЭ — {ru_date(d["date"])}', "".join(body))


def main():
    check_only = "--check" in sys.argv
    files = sorted(DATA.glob("*.json"))
    errs, reports = [], []
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        errs += validate(d, f.name)
        reports.append((f.stem, d))
    if errs:
        print("\n".join(errs))
        sys.exit(1)
    if check_only:
        print(f"OK: {len(files)} report(s) valid")
        return
    for stem, d in reports:
        (OUT / f"{stem}.html").write_text(render_report(d), encoding="utf-8")
    reports.sort(key=lambda x: x[0], reverse=True)
    if reports:
        latest = reports[0][1]
        lst = "".join(
            f'<li><a href="/reports/{s}.html">Выпуск от {ru_date(d["date"])}</a>'
            f'<span class="meta">{sum(len(d.get(k, [])) for k, _ in SECTIONS)} публикаций</span></li>'
            for s, d in reports)
        idx = render_report(latest).replace(
            "<footer>", f'<h2>Все выпуски</h2><ul class="reports">{lst}</ul><footer>', 1)
    else:
        idx = page("Обзор: право и налоги ОАЭ",
                   "<header><h1>Обзор: право и налоги ОАЭ</h1><p>Первый выпуск появится в понедельник в 10:00 (Дубай).</p></header>")
    (ROOT / "index.html").write_text(idx, encoding="utf-8")
    print(f"Built {len(reports)} report(s) + index.html")


if __name__ == "__main__":
    main()
