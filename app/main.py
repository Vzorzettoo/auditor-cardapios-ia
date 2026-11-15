from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from app.audit import Auditor, AuditRequest, ROOT
from app.web import configure
app=FastAPI(title='Auditor de Cardápios IA',version='1.0.0')
auditor=Auditor()
configure(app)
@app.get('/api/sample',response_class=PlainTextResponse)
def sample(): return (ROOT/'data/sample_menu.csv').read_text(encoding='utf-8')
@app.post('/api/audit')
def audit(body: AuditRequest):
    try: return auditor.audit(body.csv_text)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
