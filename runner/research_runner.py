#!/usr/bin/env python3
"""ULTIMECIA War Room - local Research Runner v1.
Loopback-only durable-ish worker bridge. Stdlib only. It never writes to production repos.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json, time, uuid, threading

HOST='127.0.0.1'; PORT=8765
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
DB=DATA/'jobs.json'
LOCK=threading.Lock()

def load():
    try:return json.loads(DB.read_text(encoding='utf-8'))
    except Exception:return {'jobs':{}}
def save(db):
    tmp=DB.with_suffix('.tmp');tmp.write_text(json.dumps(db,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(DB)
def response(job):
    return {k:v for k,v in job.items() if k not in ('envelope',)}
def execute_stub(job_id):
    """Safe v1: validates and checkpoints package, but does not pretend to perform AI/web research."""
    with LOCK:
        db=load();j=db['jobs'].get(job_id)
        if not j:return
        j['status']='RUNNING';j['startedAt']=time.time();j['trace'].append({'at':time.time(),'step':'VALIDATE','status':'ok'});save(db)
    time.sleep(.25)
    with LOCK:
        db=load();j=db['jobs'].get(job_id);env=j['envelope'];wp=env.get('job',{});forbidden=wp.get('executionEnvelope',{}).get('forbidden',[])
        j['status']='WAITING_EXECUTOR';j['trace'].append({'at':time.time(),'step':'CHECKPOINT','status':'ready','detail':'Envelope validado. Aguardando executor inteligente configurado.'})
        j['result']={'decision':'DEFER','summary':'Runner local validou e persistiu o Work Package, mas nenhum provedor de pesquisa/LLM foi configurado. Nenhuma conclusão substantiva foi inventada.','findings':[f"Pacote {wp.get('workPackageId')} aceito.",f"Authority: {wp.get('authority')}",f"Production write solicitado: {env.get('requested',{}).get('productionWrite')}",f"Restrições de produção: {len(forbidden)}"],'evidence':[],'artifacts':[],'trace':j['trace']}
        save(db)

class H(BaseHTTPRequestHandler):
    def _send(self,code,obj):
        raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','Content-Type');self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_OPTIONS(self):self._send(200,{'ok':True})
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/health':return self._send(200,{'ok':True,'service':'ultimecia-research-runner','version':1,'bind':HOST,'capabilities':['durable-local-jobs','lease-metadata','checkpoint','result-contract','fail-closed-production']})
        if p.startswith('/v1/jobs/'):
            jid=p.rsplit('/',1)[-1];db=load();j=db['jobs'].get(jid);return self._send(200,response(j)) if j else self._send(404,{'error':'job_not_found'})
        return self._send(404,{'error':'not_found'})
    def do_POST(self):
        p=urlparse(self.path).path
        if p!='/v1/jobs':return self._send(404,{'error':'not_found'})
        try:n=int(self.headers.get('Content-Length','0'));env=json.loads(self.rfile.read(n) or b'{}')
        except Exception:return self._send(400,{'error':'invalid_json'})
        if env.get('protocol')!='ultimecia.research.runner/v1':return self._send(400,{'error':'unsupported_protocol'})
        wp=env.get('job') or {};req=env.get('requested') or {}
        if req.get('productionWrite') is not False or wp.get('authority') not in ('research-only','none'):return self._send(403,{'error':'authority_denied'})
        jid='JOB-'+uuid.uuid4().hex[:12].upper();lease=int((env.get('lease') or {}).get('seconds',900));now=time.time();j={'jobId':jid,'workPackageId':wp.get('workPackageId'),'status':'QUEUED','createdAt':now,'leaseExpiresAt':now+max(60,min(3600,lease)),'trace':[{'at':now,'step':'ACCEPT','status':'ok'}],'envelope':env}
        with LOCK:db=load();db['jobs'][jid]=j;save(db)
        threading.Thread(target=execute_stub,args=(jid,),daemon=True).start();return self._send(202,response(j))
    def log_message(self,fmt,*args):print('[runner]',fmt%args)

if __name__=='__main__':
    print(f'ULTIMECIA Research Runner v1 em http://{HOST}:{PORT}')
    print('Fail-closed: sem escrita em produção. Ctrl+C para encerrar.')
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
