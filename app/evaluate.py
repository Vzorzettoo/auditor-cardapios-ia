import json
from sklearn.metrics import classification_report, f1_score
from app.audit import Auditor, ROOT
def evaluate():
    auditor=Auditor()
    test=[r for r in auditor.rows if r['split']=='test']
    x=[r['text'] for r in test]; y=[r['category'] for r in test]
    report={'data':'72 exemplos sintéticos autorais: 48 treino, 24 teste. Vocabulário compartilhado; resultado não comprova generalização real.','models':{}}
    for name,model in auditor.models.items():
        pred=model.predict(x)
        report['models'][name]={'macro_f1':round(f1_score(y,pred,average='macro'),4),'per_class':classification_report(y,pred,output_dict=True,zero_division=0)}
    selective=auditor.predict(x); covered=[i for i,p in enumerate(selective) if not p['abstained']]
    report['selective']={'threshold':auditor.threshold,'coverage':len(covered)/len(test),'accuracy_on_covered':sum(selective[i]['category']==y[i] for i in covered)/len(covered) if covered else None}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
if __name__=='__main__': print(json.dumps(evaluate(),ensure_ascii=False,indent=2))
