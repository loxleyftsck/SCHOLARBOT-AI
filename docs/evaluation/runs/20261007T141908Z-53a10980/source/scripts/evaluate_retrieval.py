"""Reproducible Indonesian retrieval pilot. Run --dense for pinned local ONNX models."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import shutil
import sys
import time
import uuid
from datetime import datetime, timezone
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scholarbot"))
from services.chunker import Chunk
from services.retriever import retrieve, select_context_chunks
from services.ranking import bm25_retrieve, reciprocal_rank_fusion
from services.semantic_search import dense_rank, validate_embeddings

MODELS = {
    "minilm": {"id": "sentence-transformers/all-MiniLM-L6-v2", "revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41", "max_tokens": 256, "query_prefix": "", "passage_prefix": "", "quantization": "dynamic-int8-avx512-vnni-artifact", "onnx": "onnx/model_qint8_avx512_vnni.onnx", "tokenizer": "tokenizer.json"},
    "e5": {"id": "intfloat/multilingual-e5-small", "revision": "614241f622f53c4eeff9890bdc4f31cfecc418b3", "max_tokens": 512, "query_prefix": "query: ", "passage_prefix": "passage: ", "quantization": "dynamic-int8-avx512-vnni-artifact", "onnx": "onnx/model_qint8_avx512_vnni.onnx", "tokenizer": "tokenizer.json"},
}
CONFIG = {"k": [1, 3, 5], "context_chars": 1200, "bm25_k1": 1.5, "bm25_b": 0.75, "rrf_constant": 60, "dense_min_cosine": 0.0, "threads": 2, "batch_size": 8, "seed": 0, "tuning": "No parameter fitting; fixed defaults before held-out evaluation", "diversification": "keyword baseline round-robin; candidates global rank after relevance filter"}

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1048576), b""):
            h.update(block)
    return h.hexdigest()

def atomic_json(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)

def validate_dataset(data):
    ids = [c["id"] for c in data["chunks"]]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate chunk ID")
    keys = [(c["document"], c["chunk_index"]) for c in data["chunks"]]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate source key")
    groups, seen = {}, set()
    for q in data["questions"]:
        if q["id"] in seen or not set(q["gold_sources"]) <= set(ids):
            raise ValueError("Invalid question/source IDs")
        seen.add(q["id"])
        if q["split"] not in {"tune", "evaluation"}:
            raise ValueError("Invalid split")
        groups.setdefault(q["group"], set()).add(q["split"])
        if q["category"] == "no_answer" and q["gold_sources"]:
            raise ValueError("Unanswerable query with gold evidence")
    if any(len(splits) > 1 for splits in groups.values()):
        raise ValueError("Question family leaks across splits")

def download(model, filename):
    import httpx
    dest = ROOT / ".eval-cache" / model["revision"] / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        print("Downloading", model["id"], filename, flush=True)
        tmp = dest.with_suffix(dest.suffix + ".partial")
        with httpx.stream("GET", f"https://huggingface.co/{model['id']}/resolve/{model['revision']}/{filename}", follow_redirects=True, timeout=60) as response:
            response.raise_for_status()
            with tmp.open("wb") as file:
                for block in response.iter_bytes(1048576):
                    file.write(block)
        tmp.replace(dest)
    return dest

class LocalEncoder:
    def __init__(self, model):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        self.model = model
        onnx = download(model, model["onnx"])
        tokenizer = download(model, model["tokenizer"])
        self.artifacts = {"onnx_sha256": sha(onnx), "tokenizer_sha256": sha(tokenizer), "model_bytes": onnx.stat().st_size}
        options = ort.SessionOptions()
        options.intra_op_num_threads = CONFIG["threads"]
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(onnx), options, providers=["CPUExecutionProvider"])
        self.tokenizer = Tokenizer.from_file(str(tokenizer))
        self.tokenizer.enable_padding(pad_id=1 if "e5" in model["id"] else 0)
        self.tokenizer.enable_truncation(max_length=model["max_tokens"])
        self.tokens = 0
        self.truncated = 0
    def encode(self, texts, purpose):
        vectors = []
        prefix = self.model[purpose + "_prefix"]
        for start in range(0, len(texts), CONFIG["batch_size"]):
            encoded = self.tokenizer.encode_batch([prefix + t for t in texts[start:start + CONFIG["batch_size"]]])
            self.tokens += sum(sum(e.attention_mask) for e in encoded)
            self.truncated += sum(bool(e.overflowing) for e in encoded)
            values = {"input_ids": np.asarray([e.ids for e in encoded], dtype=np.int64), "attention_mask": np.asarray([e.attention_mask for e in encoded], dtype=np.int64), "token_type_ids": np.asarray([e.type_ids for e in encoded], dtype=np.int64)}
            output = self.session.run(None, {i.name: values[i.name] for i in self.session.get_inputs()})[0]
            if output.ndim == 3:
                mask = values["attention_mask"][..., None]
                output = (output * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1)
            output = output / np.maximum(np.linalg.norm(output, axis=1, keepdims=True), 1e-12)
            valid = validate_embeddings(output, len(encoded), 384)
            if valid is None:
                raise ValueError("Invalid model output")
            vectors.extend(valid)
        return vectors

def metrics(rows):
    answerable = [r for r in rows if r["gold"]]
    no_answer = [r for r in rows if not r["gold"]]
    def mean(values): return float(np.mean(values)) if values else None
    result = {"n": len(rows), "answerable_n": len(answerable), "no_answer_n": len(no_answer)}
    for k in CONFIG["k"]:
        result[f"recall_at_{k}"] = mean([len(set(r["retrieved"][:k]) & set(r["gold"])) / len(r["gold"]) for r in answerable])
    result["all_gold_at_5"] = mean([set(r["gold"]) <= set(r["retrieved"]) for r in answerable])
    result["precision_at_5_answerable"] = mean([len(set(r["retrieved"]) & set(r["gold"])) / len(r["retrieved"]) if r["retrieved"] else 0 for r in answerable])
    result["context_source_recall"] = mean([len(set(r["context"]) & set(r["gold"])) / len(r["gold"]) for r in answerable])
    result["context_source_precision_answerable"] = mean([len(set(r["context"]) & set(r["gold"])) / len(r["context"]) if r["context"] else 0 for r in answerable])
    result["no_answer_empty_retrieval_rate"] = mean([not r["retrieved"] for r in no_answer])
    result["latency_ms_p50"] = float(np.percentile([r["latency_ms"] for r in rows], 50)) if rows else None
    result["latency_ms_p95"] = float(np.percentile([r["latency_ms"] for r in rows], 95)) if rows else None
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dense", action="store_true")
    parser.add_argument("--dataset", type=Path, default=ROOT / "docs/evaluation/dataset.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/evaluation/runs")
    args = parser.parse_args()
    data = json.loads(args.dataset.read_text(encoding="utf-8")); validate_dataset(data)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    out = args.output_dir / run_id; out.mkdir(parents=True)
    git = lambda *a: subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    packages = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}
    manifest = {"run_id": run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "status": "running", "commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain")), "dataset_sha256": sha(args.dataset), "source_hashes": {name: sha(ROOT / name) for name in ["scripts/evaluate_retrieval.py", "scholarbot/services/ranking.py", "scholarbot/services/semantic_search.py", "scholarbot/services/retriever.py"]}, "config": CONFIG, "environment": {"python": sys.version, "os": platform.platform(), "processor": platform.processor(), "packages": packages}, "models": {}, "provider_calls": 0, "provider_cost_usd": 0, "llm_tokens": 0, "claim_support": "not_measured", "citation_correctness": "not_measured", "answer_abstention": "not_measured", "errors": []}
    for name in [*manifest["source_hashes"], "scholarbot/services/chunker.py", "docs/evaluation/dataset.json"]:
        target = out / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    manifest["source_snapshot"] = "source/ (synthetic corpus and code only; no environment secrets)"
    atomic_json(out / "manifest.json", manifest)
    chunks = [Chunk(c["text"], c["chunk_index"], c["document"]) for c in data["chunks"]]
    key_ids = {(c["document"], c["chunk_index"]): c["id"] for c in data["chunks"]}
    dense_data = {}
    if args.dense:
        import psutil
        for name, spec in MODELS.items():
            print("Loading", name, flush=True); start = time.perf_counter()
            try:
                encoder = LocalEncoder(spec)
                load_ms = (time.perf_counter() - start) * 1000
                start = time.perf_counter(); vectors = encoder.encode([c.content for c in chunks], "passage")
                index_ms = (time.perf_counter() - start) * 1000
                queries, times = {}, {}
                for q in data["questions"]:
                    start = time.perf_counter(); queries[q["id"]] = encoder.encode([q.get("resolved_query", q["question"])], "query")[0]
                    times[q["id"]] = (time.perf_counter() - start) * 1000
                memory = psutil.Process().memory_info()
                manifest["models"][name] = {**spec, **encoder.artifacts, "status": "completed", "load_including_download_ms": load_ms, "index_ms": index_ms, "encoded_tokens_including_prefix": encoder.tokens, "truncated_inputs": encoder.truncated, "process_rss_bytes": memory.rss, "process_peak_working_set_bytes": getattr(memory, "peak_wset", None), "query_encoding_ms_p50": float(np.percentile(list(times.values()),50))}
                dense_data[name] = vectors, queries, times
                del encoder
            except Exception as error:
                manifest["models"][name] = {**spec, "status": "failed", "error_type": type(error).__name__}
                manifest["errors"].append({"model": name, "error_type": type(error).__name__})
                print(name, "FAILED", type(error).__name__, flush=True)
            atomic_json(out / "manifest.json", manifest)
    else:
        manifest["models"] = {n: {**s, "status": "not_run"} for n,s in MODELS.items()}
    methods = ["keyword", "bm25"] + [method + "_" + name for name in dense_data for method in ["dense", "rrf"]]
    predictions, summaries = {}, {}
    for method in methods:
        rows = []
        for q in data["questions"]:
            query = q.get("resolved_query", q["question"])
            start = time.perf_counter(); encode_ms = 0
            if method == "keyword": results = retrieve(query, chunks, top_k=5)
            elif method == "bm25": results = bm25_retrieve(query, chunks)
            else:
                family, name = method.split("_", 1); vectors, query_vectors, times = dense_data[name]
                encode_ms = times[q["id"]]
                dense = dense_rank(query_vectors[q["id"]], chunks, vectors, top_k=len(chunks), min_cosine=CONFIG["dense_min_cosine"])
                results = dense[:5] if family == "dense" else reciprocal_rank_fusion([bm25_retrieve(query, chunks, top_k=len(chunks)), dense], constant=CONFIG["rrf_constant"])
            ranking_ms = (time.perf_counter()-start)*1000
            selected = select_context_chunks(results, CONFIG["context_chars"])
            source_ids = lambda cs: [key_ids[(c.source_filename,c.chunk_index)] for c in cs]
            rows.append({"id":q["id"], "category":q["category"], "split":q["split"], "gold":q["gold_sources"], "retrieved":source_ids(results), "scores":[c.score for c in results], "context":source_ids(selected), "context_lengths":[len(c.content) for c in selected], "latency_ms":ranking_ms+encode_ms, "ranking_cached_query_ms":ranking_ms})
        predictions[method] = rows
        summaries[method] = {split:metrics([r for r in rows if r["split"]==split]) for split in ["tune","evaluation"]}
        summaries[method]["evaluation_by_category"] = {category: metrics([r for r in rows if r["split"]=="evaluation" and r["category"]==category]) for category in sorted({r["category"] for r in rows})}
    atomic_json(out/"predictions.json", predictions); atomic_json(out/"metrics.json",summaries)
    manifest["status"] = "completed_with_model_errors" if manifest["errors"] else "completed"
    manifest["result_hashes"] = {name:sha(out/name) for name in ["predictions.json","metrics.json"]}
    atomic_json(out/"manifest.json",manifest)
    print("RUN", out, flush=True)
    for method, s in summaries.items(): print(method,json.dumps(s["evaluation"]))
if __name__ == "__main__": main()
