#!/usr/bin/env python3
"""ULTIMECIA War Room - Research Runner v3.
Local, loopback-only research worker with controlled read-only GitHub/web evidence collection,
pluggable OpenAI-compatible synthesis, durable job traces and a hard human production gate.
Stdlib only. It never writes to GitHub or production repositories.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, quote_plus
from urllib.request import Request, urlopen
import json,time,uuid,threading,os,hashlib,re,html

HOST='127.0.0.1';PORT=8765;ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data';DATA.mkdir(exist_ok=True);DB=DATA/'jobs.json';LOCK=threading.Lock();PROTOCOL='ultimecia.research.runner/v1'
UA='ULTIMECIA-Research-Runner/3.0 (+read-only research)'

def load():
    try:return json.loads(DB.read_text(encoding='utf-8'))
    except Exception:return {'jobs':{}}
def save(db):
    t=DB.with_suffix('.tmp');t.write_text(json.dumps(db,ensure_ascii=False,indent=2),encoding='utf-8');t.replace(DB)
def response(j):return {k:v for k,v in j.items() if k!='envelope'}
def checkpoint(j,step,status='ok',detail=''):j.setdefault('trace',[]).append({'at':time.time(),'step':step,'status':status,'detail':detail});j['checkpoint']=step

def cfg():
    return {'base_url':os.getenv('ULTIMECIA_LLM_BASE_URL','').rstrip('/'),'api_key':os.getenv('ULTIMECIA_LLM_API_KEY',''),'model':os.getenv('ULTIMECIA_LLM_MODEL',''),'timeout':int(os.getenv('ULTIMECIA_LLM_TIMEOUT','120')),'github_token':os.getenv('ULTIMECIA_GITHUB_TOKEN',''),'web':os.getenv('ULTIMECIA_RESEARCH_WEB','1')!='0','github':os.getenv('ULTIMECIA_RESEARCH_GITHUB','1')!='0','max_evidence':int(os.getenv('ULTIMECIA_RESEARCH_MAX_EVIDENCE','12'))}
def provider_ready(c):return bool(c['base_url'] and c['api_key'] and c['model'])
def get_json(url,c,github=False):
    h={'User-Agent':UA,'Accept':'application/vnd.github+json' if github else 'application/json'}
    if github and c['github_token']:h['Authorization']='Bearer '+c['github_token']
    with urlopen(Request(url,headers=h),timeout=20) as r:return json.loads(r.read().decode('utf-8','replace'))
def get_text(url):
    with urlopen(Request(url,headers={'User-Agent':UA,'Accept':'text/html,text/plain'}),timeout=20) as r:return r.read(350000).decode('utf-8','replace')
def strip_html(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()
def ev(kind,claim,ref,excerpt='',meta=None):return {'type':kind,'claim':claim,'ref':ref,'excerpt':excerpt[:1200],'meta':meta or {}}

def github_snapshot(repo,c):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo or ''):return []
    base='https://api.github.com/repos/'+repo;out=[]
    try:
        r=get_json(base,c,True);branch=r.get('default_branch','main');out.append(ev('github','Estado público do repositório alvo consultado.',r.get('html_url',base),'default_branch='+branch,{'stars':r.get('stargazers_count'),'updated_at':r.get('updated_at')}))
        b=get_json(base+'/branches/'+quote_plus(branch),c,True);sha=((b.get('commit') or {}).get('sha') or '');out.append(ev('github','HEAD real da branch padrão capturado.',(b.get('_links') or {}).get('html') or r.get('html_url',''),sha,{'branch':branch,'sha':sha}))
        try:
            commits=get_json(base+'/commits?sha='+quote_plus(branch)+'&per_page=5',c,True)
            for x in commits[:5]:out.append(ev('github','Commit recente do AS-IS.',x.get('html_url',''),((x.get('commit') or {}).get('message') or '').split('\n')[0],{'sha':x.get('sha','')[:12]}))
        except Exception:pass
        try:
            tree=get_json(base+'/git/trees/'+quote_plus(branch)+'?recursive=1',c,True);paths=[x.get('path') for x in tree.get('tree',[]) if x.get('type')=='blob'][:2500];out.append(ev('github','Inventário de arquivos do AS-IS capturado.',r.get('html_url',''),', '.join(paths[:120]),{'fileCount':len(paths),'paths':paths[:500]}))
        except Exception:pass
    except Exception as e:out.append(ev('gap','Falha ao consultar GitHub AS-IS.',base,type(e).__name__+': '+str(e)[:240]))
    return out

def github_refs(wp,c):
    out=[]
    for x in (wp.get('repositoryLinks') or [])[:5]:
        u=x.get('url','');m=re.search(r'github\.com/([^/]+/[^/#?]+)',u)
        if m:out.extend(github_snapshot(m.group(1).removesuffix('.git'),c)[:3])
    return out

def web_sources(wp,c):
    out=[]
    for x in (wp.get('sourceLinks') or [])[:6]:
        u=x.get('url','')
        if not u.startswith(('http://','https://')):continue
        try:
            p=urlparse(u)
            if p.scheme!='https':continue
            txt=get_text(u);title='';mt=re.search(r'<title[^>]*>(.*?)</title>',txt,re.I|re.S)
            if mt:title=strip_html(mt.group(1))[:240]
            body=strip_html(txt)[:2200];out.append(ev('web','Fonte indicada no estudo foi consultada.',u,body,{'title':title,'host':p.netloc}))
        except Exception as e:out.append(ev('gap','Fonte indicada não pôde ser consultada.',u,type(e).__name__))
    return out

def collect_evidence(wp,c):
    out=[];repo=wp.get('targetRepo','')
    if c['github'] and repo:out.extend(github_snapshot(repo,c))
    if c['github']:out.extend(github_refs(wp,c))
    if c['web']:out.extend(web_sources(wp,c))
    # Dedupe + immutable hashes for provenance
    seen=set();clean=[]
    for x in out:
        k=(x['type'],x['ref'],x['claim'])
        if k in seen:continue
        seen.add(k);x['capturedAt']=time.time();x['contentHash']=hashlib.sha256((x.get('excerpt','')+x.get('ref','')).encode()).hexdigest()[:20];clean.append(x)
    return clean[:max(1,min(c['max_evidence'],30))]

def compact(wp):
    ks=['workPackageId','ideaId','title','kind','priority','originStudy','originTitle','targetRepo','targetArea','authority','objective','asIs','context','constraints','steps','acceptance','sourceLinks','repositoryLinks','deliverables','executionEnvelope'];return {k:wp.get(k) for k in ks if k in wp}
def system_prompt():return '''Você é o Research Executor da ULTIMECIA War Room. Analise pesquisa; NÃO implemente produção. Evidência coletada por ferramentas read-only é separada do Work Package. Não invente. Cite evidenceId em toda afirmação externa relevante. Preserve authorities/owners; diferencie capability gap de certification gap. Se insuficiente, DEFER. Apenas JSON válido. Decisões: ADOPT, ADAPT, DEFER, REJECT, CERTIFY. ADOPT/ADAPT/CERTIFY sempre exigem gate humano.'''
def user_prompt(wp,evidence):
    indexed=[dict({'evidenceId':'EV-'+str(i+1).zfill(3)},**x) for i,x in enumerate(evidence)]
    schema={'decision':'ADOPT|ADAPT|DEFER|REJECT|CERTIFY','summary':'...','confidence':0,'findings':[{'claim':'...','evidenceIds':['EV-001']}],'risks':['...'],'dependencies':['...'],'recommendedNextSteps':['...'],'productionImpact':'none|candidate','requiresHumanGate':True}
    return 'SCHEMA:\n'+json.dumps(schema,ensure_ascii=False)+'\nWORK PACKAGE:\n'+json.dumps(compact(wp),ensure_ascii=False)+'\nEVIDENCE LEDGER (read-only, cite IDs):\n'+json.dumps(indexed,ensure_ascii=False)
def call_provider(wp,evidence,c):
    payload={'model':c['model'],'messages':[{'role':'system','content':system_prompt()},{'role':'user','content':user_prompt(wp,evidence)}],'temperature':0.1,'response_format':{'type':'json_object'}}
    req=Request(c['base_url']+'/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+c['api_key']},method='POST')
    with urlopen(req,timeout=c['timeout']) as r:data=json.loads(r.read().decode())
    text=data['choices'][0]['message']['content'];o=json.loads(text);allowed={'ADOPT','ADAPT','DEFER','REJECT','CERTIFY'}
    if o.get('decision') not in allowed:raise ValueError('invalid_decision')
    valid={'EV-'+str(i+1).zfill(3) for i in range(len(evidence))}
    for f in o.get('findings',[]):
        if isinstance(f,dict):f['evidenceIds']=[x for x in f.get('evidenceIds',[]) if x in valid]
    o['requiresHumanGate']=o['decision'] in {'ADOPT','ADAPT','CERTIFY'} or bool(o.get('requiresHumanGate',False));o['productionImpact']='candidate' if o['decision'] in {'ADOPT','ADAPT','CERTIFY'} else 'none';o['provider']={'model':c['model'],'endpoint':c['base_url'],'responseHash':hashlib.sha256(text.encode()).hexdigest()[:20]};return o

def execute(jid):
    with LOCK:
        db=load();j=db['jobs'].get(jid)
        if not j:return
        j['status']='RUNNING';j['startedAt']=time.time();checkpoint(j,'VALIDATE');save(db)
    with LOCK:
        db=load();j=db['jobs'][jid];env=j['envelope'];wp=env.get('job',{});c=cfg();checkpoint(j,'POLICY_CHECK','ok','research-only; productionWrite=false');save(db)
    if env.get('requested',{}).get('productionWrite') is not False or wp.get('authority') not in ('research-only','none'):
        with LOCK:db=load();j=db['jobs'][jid];j['status']='DENIED';j['result']={'decision':'REJECT','summary':'Authority proibida.','requiresHumanGate':True};checkpoint(j,'FAIL_CLOSED','denied');save(db)
        return
    with LOCK:db=load();j=db['jobs'][jid];checkpoint(j,'READ_AS_IS','running','coleta read-only');save(db)
    evidence=collect_evidence(wp,c)
    with LOCK:db=load();j=db['jobs'][jid];j['evidenceLedger']=[dict({'evidenceId':'EV-'+str(i+1).zfill(3)},**x) for i,x in enumerate(evidence)];checkpoint(j,'EVIDENCE','ok',str(len(evidence))+' itens');save(db)
    if not provider_ready(c):
        with LOCK:db=load();j=db['jobs'][jid];j['status']='WAITING_EXECUTOR';j['result']={'decision':'DEFER','summary':'Evidências read-only coletadas, mas provider inteligente não configurado. Nenhuma conclusão substantiva foi inventada.','findings':[],'evidenceCount':len(evidence),'requiresHumanGate':False};checkpoint(j,'PROVIDER','waiting');save(db)
        return
    try:
        result=call_provider(wp,evidence,c);result['evidenceCount']=len(evidence)
        with LOCK:db=load();j=db['jobs'][jid];j['result']=result;j['status']='WAITING_HUMAN' if result['requiresHumanGate'] else 'DONE';j['finishedAt']=time.time();checkpoint(j,'SYNTHESIZE');checkpoint(j,'GATE','waiting' if j['status']=='WAITING_HUMAN' else 'closed',result['decision']);save(db)
    except Exception as e:
        with LOCK:db=load();j=db['jobs'][jid];j['status']='FAILED';j['error']=type(e).__name__+': '+str(e)[:500];checkpoint(j,'PROVIDER','error',j['error']);save(db)

class H(BaseHTTPRequestHandler):
    def _send(self,n,o):
        raw=json.dumps(o,ensure_ascii=False).encode();self.send_response(n);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','Content-Type');self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_OPTIONS(self):self._send(200,{'ok':True})
    def do_GET(self):
        p=urlparse(self.path).path;c=cfg()
        if p=='/health':return self._send(200,{'ok':True,'service':'ultimecia-research-runner','version':3,'bind':HOST,'provider':{'configured':provider_ready(c),'model':c['model'] or None},'research':{'githubReadOnly':c['github'],'webReadOnly':c['web'],'maxEvidence':c['max_evidence']},'capabilities':['durable-local-jobs','checkpoint','evidence-ledger','github-read-only','web-source-read-only','pluggable-llm','fail-closed-production','human-gate']})
        if p.startswith('/v1/jobs/'):
            jid=p.rsplit('/',1)[-1];j=load()['jobs'].get(jid);return self._send(200,response(j)) if j else self._send(404,{'error':'job_not_found'})
        return self._send(404,{'error':'not_found'})
    def do_POST(self):
        if urlparse(self.path).path!='/v1/jobs':return self._send(404,{'error':'not_found'})
        try:n=int(self.headers.get('Content-Length','0'));env=json.loads(self.rfile.read(n) or b'{}')
        except Exception:return self._send(400,{'error':'invalid_json'})
        if env.get('protocol')!=PROTOCOL:return self._send(400,{'error':'unsupported_protocol'})
        wp=env.get('job') or {};req=env.get('requested') or {}
        if req.get('productionWrite') is not False or wp.get('authority') not in ('research-only','none'):return self._send(403,{'error':'authority_denied'})
        jid='JOB-'+uuid.uuid4().hex[:12].upper();now=time.time();lease=int((env.get('lease') or {}).get('seconds',900));j={'jobId':jid,'workPackageId':wp.get('workPackageId'),'status':'QUEUED','createdAt':now,'leaseExpiresAt':now+max(60,min(3600,lease)),'trace':[{'at':now,'step':'ACCEPT','status':'ok'}],'envelope':env}
        with LOCK:db=load();db['jobs'][jid]=j;save(db)
        threading.Thread(target=execute,args=(jid,),daemon=True).start();return self._send(202,response(j))
    def log_message(self,fmt,*args):print('[runner]',fmt%args)
if __name__=='__main__':
    c=cfg();print(f'ULTIMECIA Research Runner v3 em http://{HOST}:{PORT}');print('Provider:',c['model'] if provider_ready(c) else 'NAO CONFIGURADO');print('Research tools: GitHub read-only=',c['github'],' Web read-only=',c['web']);print('Fail-closed: SEM escrita em produção. Ctrl+C para encerrar.');ThreadingHTTPServer((HOST,PORT),H).serve_forever()
