import csv, io, json, re, unicodedata
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel, Field, ConfigDict

ROOT=Path(__file__).resolve().parent.parent
CATEGORIES={'pizza','bebida','sobremesa','lanche','refeicao','salada'}
def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))
class AuditRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    csv_text:str=Field(min_length=10,max_length=500000)
def train_models():
    rows=json.loads((ROOT/'data/labeled.json').read_text(encoding='utf-8'))
    train=[r for r in rows if r['split']=='train']
    models={}
    for name, estimator in [('naive_bayes',MultinomialNB()),('linear_svc',LinearSVC(random_state=42))]:
        model=make_pipeline(TfidfVectorizer(strip_accents='unicode',ngram_range=(1,2)),estimator)
        model.fit([r['text'] for r in train],[r['category'] for r in train]); models[name]=model
    return models,rows

class Auditor:
    def __init__(self):
        self.models,self.rows=train_models()
        self.model=self.models['linear_svc']
        self.threshold=.2 # score gap, not a calibrated probability
    def predict(self,texts):
        scores=self.model.decision_function(texts)
        labels=self.model.classes_
        predictions=[]
        for row in scores:
            order=np.argsort(row); gap=float(row[order[-1]]-row[order[-2]])
            predictions.append({'category':str(labels[order[-1]]) if gap>=self.threshold else None,'candidate':str(labels[order[-1]]),'margin':round(gap,4),'abstained':gap<self.threshold})
        return predictions
    def audit(self,csv_text):
        reader=csv.DictReader(io.StringIO(csv_text.lstrip('\ufeff')))
        required={'id','name','description','category','price'}
        if not required.issubset(reader.fieldnames or []): raise ValueError('CSV deve conter id,name,description,category,price. Separador: vírgula.')
        rows=[]; ids=set()
        for row in reader:
            if len(rows)>=500: raise ValueError('Limite de 500 produtos por auditoria.')
            if None in row or any(v is None for v in row.values()): raise ValueError('CSV malformado: revise aspas e quantidade de colunas.')
            row={k:v.strip() for k,v in row.items()}
            if not row['id'] or row['id'] in ids: raise ValueError('IDs devem ser preenchidos e únicos.')
            if any(len(v)>2000 for v in row.values()): raise ValueError('Campo excede 2000 caracteres.')
            ids.add(row['id']); rows.append(row)
        if not rows: raise ValueError('CSV não contém produtos.')
        texts=[r['name']+' '+r['description'] for r in rows]
        predictions=self.predict(texts)
        issues=[]
        def add(row,code,severity,evidence,suggestion):
            issues.append({'product_id':row['id'],'name':row['name'],'code':code,'severity':severity,'evidence':evidence,'suggestion':suggestion,'requires_review':True})
        for row,pred in zip(rows,predictions):
            if len(row['name'])<3: add(row,'missing_name','high','Nome ausente ou muito curto.','Informar nome claro do produto.')
            if len(row['description'])<15: add(row,'short_description','medium','Descrição com menos de 15 caracteres.','Descrever ingredientes e porção com informações verificadas.')
            if row['category'] not in CATEGORIES: add(row,'invalid_category','high',row['category'],'Usar uma categoria suportada.')
            elif pred['category'] and pred['category']!=row['category']:
                add(row,'category_mismatch','medium',f"Cadastrada: {row['category']}; sugerida: {pred['category']}; margem: {pred['margin']}.",'Revisar a categoria; o modelo pode errar.')
            if pred['abstained']: add(row,'uncertain_category','low','Diferença entre os dois maiores scores abaixo de 0,2.','Classificar manualmente.')
            try:
                price=float(row['price'])
                if not np.isfinite(price) or price<=0: raise ValueError
            except ValueError: add(row,'invalid_price','high',row['price'],'Informar preço positivo usando ponto decimal.')
            full=normalize(row['name']+' '+row['description'])
            if re.search(r'\bvegan[oa]\b',full) and re.search(r'\b(carne|frango|peixe|queijo|leite|ovos?|manteiga|mel)\b',normalize(row['description'])):
                add(row,'diet_conflict','high',row['description'],'Confirmar ingredientes: uma alegação vegana conflita com termos de origem animal. Regra conservadora pode gerar falso positivo, como leite vegetal.')
        # Pairwise similarity bounded by the 500-row input limit.
        if len(rows)>1 and any(t.strip() for t in texts):
            try:
                matrix=TfidfVectorizer(strip_accents='unicode',analyzer='char_wb',ngram_range=(3,5)).fit_transform(texts)
                similarity=cosine_similarity(matrix)
                for i in range(len(rows)):
                    for j in range(i):
                        if similarity[i,j]>=.88:
                            add(rows[i],'possible_duplicate','medium',f"Similaridade {similarity[i,j]:.3f} com produto {rows[j]['id']}.",'Verificar duplicação ou diferença de tamanho/variante.')
            except ValueError: pass
        return {'products':len(rows),'issues':issues,'summary':{severity:sum(i['severity']==severity for i in issues) for severity in ['high','medium','low']},'predictions':[{'product_id':r['id'],**p} for r,p in zip(rows,predictions)],'notice':'Sugestões para revisão humana. Nenhuma alteração foi aplicada. Scores não são probabilidades. Modelo treinado em dados sintéticos.'}
