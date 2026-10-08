"""Small live Groq sample; only synthetic corpus sent. No automated claim judge."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import uuid
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scholarbot"))
from dotenv import load_dotenv
load_dotenv(ROOT/"scholarbot/.env")
from core.llm_client import get_client, DEFAULT_MODEL
from core.session_helpers import build_system_prompt
from core.rag_context import build_rag_system_prompt, build_citation_map
from services.chunker import Chunk
from services.ranking import bm25_retrieve
from services.retriever import select_context_chunks
from evaluate_retrieval import atomic_json, sha

SAMPLE_IDS=['d06','d08','p07','m04','m06','m07','f04','n04','n05','n06','n07','n08','n09','n10']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',type=Path);args=parser.parse_args()
    dataset=ROOT/'docs/evaluation/dataset.json';data=json.loads(dataset.read_text(encoding='utf-8'))
    out=args.resume or ROOT/'docs/evaluation/answers'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True,exist_ok=True)
    path=out/'responses.json'
    report=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'status':'running','model':DEFAULT_MODEL,'temperature':0.7,'max_tokens':900,'sample_ids':SAMPLE_IDS,'dataset_sha256':sha(dataset),'scope':'RAG prompt + BM25 top3, no full API/UI/session workflow','manual_claim_review':'pending','provider_cost_usd':None,'calls':0,'rows':[]}
    client=get_client()
    if client is None:
        report['status']='unavailable';report['reason']='Missing Groq credential';atomic_json(path,report);print(report['reason']);return
    chunks=[Chunk(c['text'],c['chunk_index'],c['document']) for c in data['chunks']]
    done={r['id'] for r in report['rows'] if r.get('status')=='completed'}
    # Remove failed entries only on explicit resume; preserved in prior_error_attempts.
    failed=[r for r in report['rows'] if r.get('status')!='completed']
    if failed:report.setdefault('prior_error_attempts',[]).extend(failed);report['rows']=[r for r in report['rows'] if r.get('status')=='completed']
    for q in data['questions']:
        if q['id'] not in SAMPLE_IDS or q['id'] in done:continue
        query=q.get('resolved_query',q['question']);evidence=select_context_chunks(bm25_retrieve(query,chunks,top_k=3))
        prompt=build_rag_system_prompt(build_system_prompt('Santai & Friendly'),evidence) if evidence else build_system_prompt('Santai & Friendly')+'\nMateri diunggah, tetapi tidak ditemukan potongan yang relevan. Nyatakan sumber belum cukup; jangan mengarang sitasi.'
        start=time.perf_counter();report['calls']+=1
        try:
            response=client.chat.completions.create(model=DEFAULT_MODEL,messages=[{'role':'system','content':prompt},{'role':'user','content':query}],temperature=0.7,max_tokens=900,stream=False)
            text=response.choices[0].message.content or '';markers=[int(x) for x in re.findall(r'\[(\d+)\]',text)]
            row={'id':q['id'],'status':'completed','category':q['category'],'question':query,'gold_answer':q['gold_answer'],'sources':build_citation_map(evidence,snippet_chars=0),'answer':text,'finish_reason':response.choices[0].finish_reason,'citation_ids':markers,'citation_ids_valid':all(1<=i<=len(evidence) for i in markers),'latency_ms':(time.perf_counter()-start)*1000,'usage':response.usage.model_dump() if response.usage else None,'manual_claim_support':None,'manual_abstention':None}
            report['rows'].append(row);print(q['id'],'completed',flush=True)
        except Exception as error:
            report['rows'].append({'id':q['id'],'status':'failed','error_type':type(error).__name__});report['status']='partial';atomic_json(path,report);print(q['id'],type(error).__name__,flush=True);return
        atomic_json(path,report)
    report['status']='completed';atomic_json(path,report);print('ANSWERS',out,flush=True)
if __name__=='__main__':main()
