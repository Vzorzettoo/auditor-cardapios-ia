import pytest
from fastapi.testclient import TestClient
from app.main import app, auditor
from app.audit import ROOT
client=TestClient(app)
def test_sample_detects_expected_issues():
    d=client.post('/api/audit',json={'csv_text':(ROOT/'data/sample_menu.csv').read_text(encoding='utf-8')}).json()
    codes={i['code'] for i in d['issues']}
    assert {'possible_duplicate','diet_conflict','invalid_price','short_description','category_mismatch'}<=codes
    assert all(i['requires_review'] for i in d['issues'])
@pytest.mark.parametrize('csv',['id,name\\n1,x','id,name,description,category,price\\n1,x,d,pizza,1\\n1,y,d,pizza,2','id,name,description,category,price'])
def test_bad_input_is_rejected(csv):
    assert client.post('/api/audit',json={'csv_text':csv.replace('\\n','\n')}).status_code==422
def test_abstention_for_unseen_text():
    p=auditor.predict(['xyz abc zzz'])[0]
    assert p['abstained'] and p['category'] is None
def test_train_test_are_disjoint():
    train={r['text'] for r in auditor.rows if r['split']=='train'}
    test={r['text'] for r in auditor.rows if r['split']=='test'}
    assert not train&test
def test_health_and_ui():
    assert client.get('/').status_code==200
    assert client.get('/health').status_code==200
