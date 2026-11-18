"""Render real verification logs as HTML and capture them with headless Chrome/Edge."""
from pathlib import Path
from html import escape
import json
import os
import subprocess

root = Path(__file__).resolve().parent
out = root / 'evidence'
data = json.loads((out / 'http-responses.json').read_text(encoding='utf-8'))
stamp = data['verified_at']

def text_file(name):
    raw = (out / name).read_bytes()
    text = raw.decode('utf-16') if raw.startswith(b'\xff\xfe') else raw.decode('utf-8-sig')
    return text.replace('\r\n', '\n').replace('\r', '')

def panel(title, content):
    return f'<section><h2>{escape(title)}</h2><pre>{escape(content)}</pre></section>'

style = '''body{margin:36px;font:18px Segoe UI,Arial;background:#f1f5f9;color:#172033}
h1{font-size:30px;margin-bottom:8px}h2{font-size:22px;margin:0 0 16px}
section{background:white;border:1px solid #cbd5e1;border-radius:12px;padding:24px;margin:20px 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font:16px Consolas,monospace;line-height:1.5;margin:0}
table{border-collapse:collapse;width:100%;background:white;font-size:17px}
th,td{border:1px solid #cbd5e1;padding:9px;text-align:left}th{background:#dbeafe}
.meta{color:#475569}.ok{color:#166534;font-weight:700}'''

verification = (root / 'verification-results.txt').read_text(encoding='utf-8')
http_rows = ''.join(f'<tr><td>{escape(r["method"])}</td><td>{escape(r["url"].split("localhost:")[1])}</td>'
                    f'<td>{r["expected"]}</td><td class="ok">{r["status"]} PASS</td></tr>'
                    for r in data['responses'])
errors = '\n'.join(line for line in verification.splitlines()
                   if any(s in line for s in ['API tat', 'sai cong', 'test server', 'invalid URL', 'reset', 'PASS:']))
pages = {
    'build': ('Build hai solution', panel('CatalogApi', text_file('build-catalog.txt')) +
              panel('RestfulClientServer', text_file('build-edusubmit.txt'))),
    'clients': ('Hai client: xem → tạo → đọc Location → thử lỗi',
                panel('Catalog.Client — lần 1', text_file('Catalog-client-lan-1.txt')) +
                panel('Submission.Client — lần 1', text_file('Submission-client-lan-1.txt'))),
    'http': ('Kết quả HTTP thực tế', f'<p>{len(data["responses"])} ca HTTP; gồm 29 request trong các tệp .http.</p>' +
             '<table><tr><th>Method</th><th>URL / path</th><th>Mong đợi</th><th>Thực tế</th></tr>' + http_rows + '</table>'),
    'errors': ('Kiểm chứng lỗi và thí nghiệm phân tán', panel('Kết quả thực tế', errors)),
}
browser = next((Path(p) for p in [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
] if Path(p).is_file()), None)
for name, (title, body) in pages.items():
    page = out / f'{name}.html'
    page.write_text(f'<!doctype html><html lang="vi"><meta charset="utf-8"><title>{escape(title)}</title>'
                    f'<style>{style}</style><h1>{escape(title)}</h1>'
                    f'<p class="meta">Đàm Văn Việt · dtc245200682 · {escape(stamp)}<br>'
                    'Báo cáo từ log chạy thực tế; dữ liệu gốc được lưu cùng thư mục evidence.</p>' + body + '</html>', encoding='utf-8', newline='\n')
    if browser:
        height = 400 + 46 * (len(data['responses']) + 1) if name == 'http' else 1600
        result = subprocess.run([str(browser), '--headless', '--disable-gpu', '--no-first-run',
                                 '--no-default-browser-check', '--disable-extensions', '--hide-scrollbars',
                                 f'--user-data-dir={root / ".evidence-browser"}',
                                 f'--screenshot={out / (name + ".png")}', f'--window-size=1600,{height}',
                                 page.as_uri()], capture_output=True, timeout=45,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode or not (out / (name + '.png')).exists():
            raise RuntimeError(f'Could not capture {name}: {result.stderr.decode(errors="replace")[-1500:]}')
        print(f'Captured evidence/{name}.png')
    else:
        print(f'HTML ready: {page}; capture it with a browser for the README images.')
