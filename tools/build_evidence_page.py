# -*- coding: utf-8 -*-
"""يبني صفحة أدلة واحدة (docs/EVIDENCE.html) من تقارير JSON — وسيط قابل للفحص والمشاركة."""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p, d=None):
    try:
        return json.loads((ROOT / p).read_text(encoding="utf-8"))
    except Exception:
        return d or {}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    st = load("tests/selftest_report.json")
    fp = load("tests/failure_paths_report.json")
    sm = load("tests/failure_smoke.json")
    e2e = load("tools/e2e_report.json")
    ac = load("tests/acceptance_check.json")
    cmds = load("tools/telegram_commands.json")

    rows = []
    for r in (sm.get("checks") or []):
        rows.append(("check", r.get("check"), r.get("ok"), r.get("note")))
    for r in (fp.get("results") or [])[:20]:
        rows.append(("failure", r.get("test"), r.get("ok"), r.get("note")))
    for r in (e2e.get("results") or []):
        rows.append(("e2e", r.get("command"), not r.get("errors"), ",".join(r.get("errors") or []) or "ok"))

    html = f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>صفحة الأدلة — بوت القرآن الموحّد</title>
<style>body{{font-family:-apple-system,"Segoe UI",Tahoma,sans-serif;max-width:66ch;margin:0 auto;padding:40px 18px;line-height:1.7;color:#111}}
h1{{font-size:1.5rem}} h2{{font-size:1.1rem;margin-top:1.8em}} table{{border-collapse:collapse;width:100%;font-size:.9rem}}
th,td{{border-bottom:1px solid #eee;padding:.35em .4em;text-align:right}} .ok{{color:#1f7a4d}} .bad{{color:#b3541e}}
code{{background:#f4f4f4;padding:0 .25em}} .kpi{{font-size:1.05rem}}</style></head><body>
<h1>صفحة الأدلة — بوت القرآن الموحّد</h1>
<p class="kpi">
الاختبار الذاتي: <b>{st.get('passed')}/{st.get('total')}</b> ·
مسارات استثنائية: <b>{fp.get('passed')}/{fp.get('total')}</b> ·
فحص دخان: <b>{sm.get('passed')}/{sm.get('total')}</b> ·
اختبار تليجرام الحقيقي: <b>{(e2e.get('total',0)-e2e.get('failures',0))}/{e2e.get('total',0)}</b> ·
معايير القبول: <b>{ac.get('criteria_done')}/{ac.get('criteria_total')}</b> ·
أوامر تليجرام: <b>{cmds.get('verified_count')}</b>
</p>
<p>مُولّدة: {esc(datetime.now().astimezone().isoformat(timespec='seconds'))} · البوت: <code>@{esc(e2e.get('bot',''))}</code> · حساب الاختبار: <code>{esc(e2e.get('tester_account',''))}</code></p>
<h2>سجلّ الفحوصات (check / failure / e2e)</h2>
<table><thead><tr><th>النوع</th><th>البند</th><th>النتيجة</th><th>ملاحظة</th></tr></thead><tbody>
{''.join(f"<tr><td>{esc(t)}</td><td>{esc(n)}</td><td class='{'ok' if ok else 'bad'}'>{'PASS' if ok else 'FAIL'}</td><td>{esc(note)}</td></tr>" for (t,n,ok,note) in rows)}
</tbody></table>
<h2>ملفات الأدلة</h2>
<ul>
<li><code>tests/selftest_report.json</code></li><li><code>tests/failure_paths_report.json</code></li>
<li><code>tests/failure_smoke.json</code></li><li><code>tools/e2e_report.json</code></li>
<li><code>tests/acceptance_check.json</code></li><li><code>tools/telegram_commands.json</code></li>
</ul>
</body></html>"""
    (ROOT / "docs" / "EVIDENCE.html").write_text(html, encoding="utf-8")
    print("wrote docs/EVIDENCE.html", len(html), "bytes; rows:", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
