#!/usr/bin/env python3
"""ULTIMECIA War Room - local Research Runner v2.
Loopback-only research worker. Supports a pluggable OpenAI-compatible LLM provider,
persists jobs/checkpoints, and never writes to production repositories.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json, time, uuid, threading, os, hashlib

HOST='127.0.0.1'; PORT=8765
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
DB=DATA/'jobs.json'; LOCK=threading.Lock()
PROTOCOL='ultimecia.research.runner/v1'

def load():
    try:return json.loads(DB.read_text(encoding='utf-8'))
    except Exception:return {'jobs':{}}
def save(db):
    tmp=DB.with_suffix('.tmp');tmp.write_text(json.dumps(db,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(DB)
def response(job): return {k:v for k,v in job.items() if k!='envelope'}
def checkpoint(j,step,status='ok',detail=''):
    j.setdefault('trace',[]).append({'at':time.time(),'step':step,'status':status,'detail':detail})
    j['checkpoint']=step

def provider_config():
    return {
      'base_url':os.getenv('ULTIMECIA_LLM_BASE_URL','').rstrip('/'),
      'api_key':os.getenv('ULTIMECIA_LLM_API_KEY',''),
      'model':os.getenv('ULTIMECIA_LLM_MODEL',''),
      'timeout':int(os.getenv('ULTIMECIA_LLM_TIMEOUT','120')),
    }
def provider_ready(c): return bool(c['base_url'] and c['api_key'] and c['model'])

def compact_job(wp):
    keys=['workPackageId','ideaId','title','kind','priority','originStudy','originTitle','targetRepo','targetArea','authority','objective','asIs','context','constraints','steps','acceptance','sourceLinks','repositoryLinks','deliverables','executionEnvelope']
    return {k:wp.get(k) for k in keys if k in wp}

def system_prompt():
    return '''Você é o Research Executor da ULTIMECIA War Room. Sua função é analisar um Work Package de pesquisa, NÃO implementar mudanças de produção.
Regras constitucionais:
1. Não invente evidências, arquivos, testes, commits, resultados web ou estado de repositório que não estejam no pacote.
2. Diferencie claramente: conteúdo fornecido, inferência e lacuna que exige verificação externa.
3. Preserve owners/authorities existentes. Não recomende nova authority sem necessidade demonstrada.
4. Distingua capacidade ausente de certification/evidence gap.
5. Nenhuma resposta autoriza escrita, merge, cutover ou remoção de legado.
6. Se a evidência for insuficiente, DEFER é preferível a fingir certeza.
7. Produza APENAS JSON válido, sem markdown, no schema solicitado.
Decisões permitidas: ADOPT, ADAPT, DEFER, REJECT, CERTIFY.'''

def user_prompt(wp):
    schema={'decision':'ADOPT|ADAPT|DEFER|REJECT|CERTIFY','summary':'síntese objetiva','confidence':0,'findings':['...'],'evidence':[{'type':'package|source|repository|inference|gap','claim':'...','ref':'...'}],'risks':['...'],'dependencies':['...'],'recommendedNextSteps':['...'],'productionImpact':'none|candidate','requiresHumanGate':True}
    return 'Analise o Work Package abaixo. Use somente o que ele sustenta; marque lacunas explicitamente.\nSCHEMA DE SAÍDA:\n'+json.dumps(schema,ensure_ascii=False)+'\nWORK PACKAGE:\n'+json.dumps(compact_job(wp),ensure_ascii=False)

def call_provider(wp,cfg):
    payload={'model':cfg['model'],'messages':[{'role':'system','content':system_prompt()},{'role':'user','content':user_prompt(wp)}],'temperature':0.15,'response_format':{'type':'json_object'}}
    req=Request(cfg['base_url']+'/chat/completions',data=json.dumps(payload).encode('utf-8'),headers={'Content-Type':'application/json','Authorization':'Bearer '+cfg['api_key']},method='POST')
    with urlopen(req,timeout=cfg['timeout']) as r: data=json.loads(r.read().decode('utf-8'))
    text=data['choices'][0]['message']['content']; out=json.loads(text)
    allowed={'ADOPT','ADAPT','DEFER','REJECT','CERTIFY'}
    if out.get('decision') not in allowed: raise ValueError('invalid_decision')
    out['requiresHumanGate']=True if out.get('decision') in {'ADOPT','ADAPT','CERTIFY'} else bool(out.get('requiresHumanGate',False))
    out['productionImpact']='candidate' if out.get('decision') in {'ADOPT','ADAPT','CERTIFY'} else 'none'
    out['provider']={'model':cfg['model'],'endpoint':cfg['base_url'],'responseHash':hashlib.sha256(text.encode()).hexdigest()[:20]}
    return out

def execute(job_id):
    with LOCK:
        db=load();j=db['jobs'].get(job_id)
        if not j:return
        j['status']='RUNNING';j['startedAt']=time.time();checkpoint(j,'VALIDATE');save(db)
    with LOCK:
        db=load();j=db['jobs'][job_id];env=j['envelope'];wp=env.get('job',{});cfg=provider_config()
        checkpoint(j,'POLICY_CHECK','ok','research-only; productionWrite=false')
        if env.get('requested',{}).get('productionWrite') is not False or wp.get('authority') not in ('research-only','none'):
            j['status']='DENIED';j['result']={'decision':'REJECT','summary':'Execution envelope pediu authority proibida.','requiresHumanGate':True};checkpoint(j,'FAIL_CLOSED','denied');save(db);return
        if not provider_ready(cfg):
            j['status']='WAITING_EXECUTOR';j['result']={'decision':'DEFER','summary':'Work Package validado e persistido, mas o provider inteligente ainda não está configurado. Defina ULTIMECIA_LLM_BASE_URL, ULTIMECIA_LLM_API_KEY e ULTIMECIA_LLM_MODEL.','findings':['Nenhuma conclusão substantiva foi inventada.'],'evidence':[],'requiresHumanGate':False};checkpoint(j,'PROVIDER','waiting','provider não configurado');save(db);return
        checkpoint(j,'PROVIDER','ready',cfg['model']);save(db)
    try:
        result=call_provider(wp,cfg)
        with LOCK:
            db=load();j=db['jobs'][job_id];j['result']=result;j['status']='WAITING_HUMAN' if result.get('requiresHumanGate') else 'DONE';j['finishedAt']=time.time();checkpoint(j,'SYNTHESIZE');checkpoint(j,'GATE','waiting' if j['status']=='WAITING_HUMAN' else 'closed',result['decision']);save(db)
    except Exception as e:
        with LOCK:
            db=load();j=db['jobs'][job_id];j['status']='FAILED';j['error']=type(e).__name__+': '+str(e)[:500];checkpoint(j,'PROVIDER','error',j['error']);save(db)

class H(BaseHTTPRequestHandler):
    def _send(self,code,obj):
        raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','Content-Type');self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_OPTIONS(self):self._send(200,{'ok':True})
    def do_GET(self):
        p=urlparse(self.path).path;cfg=provider_config()
        if p=='/health':return self._send(200,{'ok':True,'service':'ultimecia-research-runner','version':2,'bind':HOST,'provider':{'configured':provider_ready(cfg),'model':cfg['model'] or None,'baseUrl':cfg['base_url'] or None},'capabilities':['durable-local-jobs','checkpoint','result-contract','pluggable-llm','fail-closed-production','human-gate']})
        if p.startswith('/v1/jobs/'):
            jid=p.rsplit('/',1)[-1];db=load();j=db['jobs'].get(jid);return self._send(200,response(j)) if j else self._send(404,{'error':'job_not_found'})
        return self._send(404,{'error':'not_found'})
    def do_POST(self):
        p=urlparse(self.path).path
        if p!='/v1/jobs':return self._send(404,{'error':'not_found'})
        try:n=int(self.headers.get('Content-Length','0'));env=json.loads(self.rfile.read(n) or b'{}')
        except Exception:return self._send(400,{'error':'invalid_json'})
        if env.get('protocol')!=PROTOCOL:return self._send(400,{'error':'unsupported_protocol'})
        wp=env.get('job') or {};req=env.get('requested') or {}
        if req.get('productionWrite') is not False or wp.get('authority') not in ('research-only','none'):return self._send(403,{'error':'authority_denied'})
        jid='JOB-'+uuid.uuid4().hex[:12].upper();lease=int((env.get('lease') or {}).get('seconds',900));now=time.time();j={'jobId':jid,'workPackageId':wp.get('workPackageId'),'status':'QUEUED','createdAt':now,'leaseExpiresAt':now+max(60,min(3600,lease)),'trace':[{'at':now,'step':'ACCEPT','status':'ok'}],'envelope':env}
        with LOCK:db=load();db['jobs'][jid]=j;save(db)
        threading.Thread(target=execute,args=(jid,),daemon=True).start();return self._send(202,response(j))
    def log_message(self,fmt,*args):print('[runner]',fmt%args)

if __name__=='__main__':
    cfg=provider_config();print(f'ULTIMECIA Research Runner v2 em http://{HOST}:{PORT}');print('Provider:',cfg['model'] if provider_ready(cfg) else 'NAO CONFIGURADO');print('Fail-closed: sem escrita em produção. Ctrl+C para encerrar.');ThreadingHTTPServer((HOST,PORT),H).serve_forever()
