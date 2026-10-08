"""Verify artifacts, recompute aggregates, and compare two local pilot runs."""
import argparse
import json
from evaluate_retrieval import sha, metrics

def verify(run):
    manifest=json.loads((run/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"]=="completed"
    for name,digest in manifest["result_hashes"].items():assert sha(run/name)==digest
    for name,digest in manifest["source_hashes"].items():assert sha(run/"source"/name)==digest
    assert sha(run/"source/docs/evaluation/dataset.json")==manifest["dataset_sha256"]
    predictions=json.loads((run/"predictions.json").read_text(encoding="utf-8"))
    saved=json.loads((run/"metrics.json").read_text(encoding="utf-8"))
    for method,rows in predictions.items():
        for split in ["tune","evaluation"]:
            calculated=metrics([r for r in rows if r["split"]==split]);assert calculated==saved[method][split]
    return manifest,predictions

def main():
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument("first",type=Path);parser.add_argument("second",type=Path);args=parser.parse_args()
    a,pa=verify(args.first);b,pb=verify(args.second)
    assert a["dataset_sha256"]==b["dataset_sha256"]
    assert a["source_hashes"]==b["source_hashes"]
    assert a["config"]==b["config"]
    assert set(pa)==set(pb)
    checked=0
    for method in pa:
        for row_a,row_b in zip(pa[method],pb[method],strict=True):
            without_timing=lambda r:{k:v for k,v in r.items() if k not in {"latency_ms","ranking_cached_query_ms"}}
            assert without_timing(row_a)==without_timing(row_b)
            checked+=1
    result={"status":"passed","first":a["run_id"],"second":b["run_id"],"identical_rankings_scores_and_contexts":checked,"aggregate_metrics_recomputed":True,"hashes_verified":True,"latency_exact_reproduction":False}
    from evaluate_retrieval import atomic_json
    atomic_json(args.second/"reproduction.json",result)
    print(json.dumps(result))
if __name__=="__main__":main()
