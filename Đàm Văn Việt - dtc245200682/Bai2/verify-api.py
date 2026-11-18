import json, subprocess, time, urllib.request, urllib.error
import re, socket, threading
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
root=Path(__file__).resolve().parent
stamp = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec='seconds')
logs=[f'Bai 2 - verification at {stamp}', 'Student: Dam Van Viet - dtc245200682', 'SDK: ' + subprocess.check_output(['dotnet', '--version'], text=True).strip()]
responses=[]
evidence=root/'evidence'
evidence.mkdir(exist_ok=True)
def request(base, method, path, expected, body=None, content_type='application/json', code=None):
    data=None if body is None else (body.encode() if isinstance(body,str) else json.dumps(body).encode())
    req=urllib.request.Request(base+path,data=data,method=method,headers={'Content-Type':content_type} if data is not None else {})
    try: r=urllib.request.urlopen(req,timeout=5)
    except urllib.error.HTTPError as e: r=e
    raw=r.read().decode(); status=r.status
    assert status==expected,(method,path,status,raw)
    obj=json.loads(raw) if raw and 'application/json' in r.headers.get('Content-Type','') else None
    if code: assert obj['code']==code,obj
    responses.append({'method':method, 'url':base+path, 'expected':expected, 'status':status,
                      'headers':dict(r.headers), 'body':raw})
    logs.append(f'{method} {path} -> {status}'+(f' {code}' if code else ''))
    return obj,r.headers,raw

def start(project,port):
    with socket.socket() as probe:
        assert probe.connect_ex(('localhost', port)) != 0, f'Port {port} already in use; stop verification to avoid touching another API.'
    dll=root/project/'bin/Debug/net10.0'/f'{project.name}.dll'
    p=subprocess.Popen(['dotnet',str(dll),'--urls',f'http://localhost:{port}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            urllib.request.urlopen(f'http://localhost:{port}/',timeout=.3).close();return p
        except Exception:
            if p.poll() is not None: raise RuntimeError('API failed to start')
            time.sleep(.1)
    p.terminate();p.wait(timeout=10);raise RuntimeError('API startup timeout')

def client(project,base,label):
    result=subprocess.run(['dotnet',str(root/project/'bin/Debug/net10.0'/f'{project.name}.dll'),base],capture_output=True,text=True,timeout=25)
    assert result.returncode==0,result.stdout+result.stderr
    assert all(f'{i}.' in result.stdout for i in range(1,5)),result.stdout
    assert 'HTTP 201' in result.stdout and 'HTTP 400' in result.stdout,result.stdout
    assert ('INVALID_PRODUCT' if project.name=='Catalog.Client' else 'INVALID_SUBMISSION') in result.stdout
    logs.append('\n'+label+'\n'+result.stdout)
    (evidence/(label.replace(' ', '-')+'.txt')).write_text(result.stdout,encoding='utf-8')

def run_http_file(file,base):
    """Execute the checked-in REST Client cases, including named response IDs and JSON files."""
    named={}
    count=0
    for block in file.read_text(encoding='utf-8-sig').split('###')[1:]:
        title=block.splitlines()[0]
        match=re.search(r'^(GET|POST|PUT|DELETE)\s+(.+)$',block,re.M)
        assert match, title
        method,url=match.groups()
        url=url.strip().replace('{{api}}',base)
        for name,obj in named.items():
            url=url.replace('{{'+name+'.response.body.$.id}}',str(obj['id']))
        assert '{{' not in url,url
        rest=block[match.end():].lstrip('\r\n')
        head,_,body=rest.partition('\n\n')
        content_type=re.search(r'^Content-Type:\s*(.+)',head,re.M)
        body=body.strip() or None
        if body and body.startswith('< '):
            body=(file.parent/body[2:].strip()).read_text(encoding='utf-8-sig')
        expected=int(re.search(r'->\s*(\d{3})',title).group(1))
        code=re.search(r'\b(?:PRODUCT_NOT_FOUND|INVALID_PRODUCT|ASSIGNMENT_NOT_FOUND|INVALID_SUBMISSION|SUBMISSION_NOT_FOUND|ASSIGNMENT_CLOSED)\b',title)
        obj,_,_=request(base,method,url.removeprefix(base),expected,body,
                        content_type.group(1).strip() if content_type else 'application/json',
                        code.group(0) if code else None)
        name=re.search(r'^# @name (\w+)',block,re.M)
        if name: named[name.group(1)]=obj
        count+=1
    logs.append(f'{file.relative_to(root)}: {count}/{count} requests PASS')
    return count

def failure_client_cases(project):
    """Real HTTP responses isolate HTTP errors from connection and JSON errors."""
    dll=str(root/project/'bin/Debug/net10.0'/f'{project.name}.dll')
    cases=[(404,'','HTTP 404'), (500,'{"code":"SERVER_ERROR","message":"Test error"}','SERVER_ERROR'),
           (200,'{broken','JSON tu API'), (200,'null','Loi hop dong API')]
    for status,body,expected in cases:
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(status)
                self.send_header('Content-Type','application/json')
                self.end_headers()
                self.wfile.write(body.encode())
            def log_message(self,*args): pass
        with ThreadingHTTPServer(('localhost',0),Handler) as server:
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                result=subprocess.run(['dotnet',dll,f'http://localhost:{server.server_port}'],capture_output=True,text=True,timeout=20)
                assert result.returncode==1 and expected in result.stdout,result.stdout+result.stderr
                logs.append(f'{project.name}: test server HTTP {status}, body={body!r} -> exit 1; '+result.stdout.strip())
            finally: server.shutdown();thread.join()
    result=subprocess.run(['dotnet',dll,'not-a-url'],capture_output=True,text=True,timeout=20)
    assert result.returncode==1 and 'HTTP/HTTPS' in result.stdout,result.stdout+result.stderr
    logs.append(f'{project.name}: invalid URL -> exit 1; '+result.stdout.strip())

for kind,folder,port in [('Catalog','CatalogApi',15100),('Submission','RestfulClientServer',15000)]:
    api=Path(folder)/'src'/f'{kind}.Api'; base=f'http://localhost:{port}'
    p=start(api,port)
    try:
        request(base,'GET','/',200)
        if kind=='Catalog':
            assert len(request(base,'GET','/api/products',200)[0])==3
            request(base,'GET','/api/products/1',200)
            request(base,'GET','/api/products/999',404,code='PRODUCT_NOT_FOUND')
            assert request(base,'GET','/api/products/abc',404)[2]==''
            body=json.loads((root/folder/'src/Catalog.Api/sp-hop-le.json').read_text(encoding='utf-8-sig'))
            obj,headers,_=request(base,'POST','/api/products',201,body)
            assert obj['price']==80000
            read,_,_=request(base,'GET',headers['Location'],200); assert read==obj
            request(base,'POST','/api/products',400,{'name':'','price':-1},code='INVALID_PRODUCT')
            request(base,'POST','/api/products',415,body,'application/x-www-form-urlencoded')
            assert run_http_file(root/folder/'requests.http',base)==8
        else:
            request(base,'GET','/api/assignments',200)
            request(base,'GET','/api/assignments/1',200)
            request(base,'GET','/api/assignments/999',404,code='ASSIGNMENT_NOT_FOUND')
            assert request(base,'GET','/api/assignments/abc',404)[2]==''
            body={'studentCode':' SV001 ','repositoryUrl':' https://example.com/repo '}
            obj,headers,_=request(base,'POST','/api/assignments/1/submissions',201,body)
            assert obj['studentCode']=='SV001' and obj['status']=='received'
            old_location=headers['Location']
            read,_,_=request(base,'GET',old_location,200);assert read==obj
            request(base,'POST','/api/assignments/1/submissions',400,{'studentCode':'','repositoryUrl':''},code='INVALID_SUBMISSION')
            request(base,'POST','/api/assignments/1/submissions',400,{'studentCode':'SV001'},code='INVALID_SUBMISSION')
            request(base,'POST','/api/assignments/3/submissions',400,body,code='ASSIGNMENT_CLOSED')
            request(base,'POST','/api/assignments/999/submissions',404,body,code='ASSIGNMENT_NOT_FOUND')
            request(base,'POST','/api/assignments/1/submissions',415,body,'application/x-www-form-urlencoded')
            request(base,'POST','/api/assignments/1/submissions',400,'{"studentCode":')
            request(base,'PUT','/api/assignments/1',405)
            request(base,'GET','/api/submissions/00000000-0000-0000-0000-000000000000',404,code='SUBMISSION_NOT_FOUND')
            for invalid in [{'studentCode':None,'repositoryUrl':None}, {'studentCode':'  ','repositoryUrl':'  '}]:
                request(base,'POST','/api/assignments/1/submissions',400,invalid,code='INVALID_SUBMISSION')
            request(base,'POST','/api/assignments/999/submissions',404,{},code='ASSIGNMENT_NOT_FOUND')
            request(base,'POST','/api/assignments/3/submissions',400,{},code='ASSIGNMENT_CLOSED')
            assert run_http_file(root/'requests.http',base)==7
            assert run_http_file(root/folder/'requests.http',base)==14
        client(Path(folder)/'src'/f'{kind}.Client',base,kind+' client lan 1')
        client(Path(folder)/'src'/f'{kind}.Client',base,kind+' client lan 2')
    finally:
        p.terminate();p.wait(timeout=10)
    failed=subprocess.run(['dotnet',str(root/folder/'src'/f'{kind}.Client'/'bin/Debug/net10.0'/f'{kind}.Client.dll'),base],capture_output=True,text=True,timeout=25)
    assert failed.returncode==1 and 'Loi ket noi' in failed.stdout
    logs.append(kind+': API tat -> client bao Loi ket noi (exit 1)')
    logs.append(failed.stdout.strip())
    wrong=subprocess.run(['dotnet',str(root/folder/'src'/f'{kind}.Client'/'bin/Debug/net10.0'/f'{kind}.Client.dll'),'http://localhost:15999'],capture_output=True,text=True,timeout=25)
    assert wrong.returncode==1 and 'Loi ket noi' in wrong.stdout,wrong.stdout+wrong.stderr
    logs.append(kind+': sai cong 15999 -> client bao Loi ket noi (exit 1)')
    p=start(api,port)
    try:
        if kind=='Catalog': assert len(request(base,'GET','/api/products',200)[0])==3
        else: request(base,'GET',old_location,404,code='SUBMISSION_NOT_FOUND')
        logs.append(kind+': khoi dong lai -> du lieu RAM duoc reset')
    finally: p.terminate();p.wait(timeout=10)
    failure_client_cases(Path(folder)/'src'/f'{kind}.Client')
logs.append(f'PASS: {len(responses)} HTTP assertions; 29 checked-in HTTP requests; 4 complete client runs; 2 stopped-API, 2 wrong-port, 10 client error cases; 2 RAM reset checks.')
(root/'verification-results.txt').write_text('\n'.join(logs),encoding='utf-8')
(evidence/'http-responses.json').write_text(json.dumps({'verified_at':stamp,'responses':responses},ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(logs))
