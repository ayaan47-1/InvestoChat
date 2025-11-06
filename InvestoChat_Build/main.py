import os
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
import argparse
import re

DOMAIN_TERMS = {"bhk","sq","sft","sqft","acre","acres","tower","core","aravalli","gurgaon","gurugram","sector",
                "clp","plp","possession","rera","super","area","carpet","price","launch","amenities","lakh","crore",
                "flexi","payment","green","club","wellness","noida"}

SAFE_CHARS = r"[^a-z0-9 ₹.%/-]+"
def tokenize(text: str):
    t = re.sub(SAFE_CHARS, " ", text.lower())
    raw = [w for w in t.split() if w]
    stop = {"the","a","an","and","or","of","to","in","on","for","with","at","by","from","is","are","was","were","be","as","that","this","these","those"}
    keep = []
    for w in raw:
        if w in stop:
            continue
        if w in DOMAIN_TERMS:
            keep.append(w); continue
        if w.replace(".","",1).isdigit():
            keep.append(w); continue
        if any(s in w for s in ["bhk","sq","ft","sft","₹","cr","lakh","%"]):
            keep.append(w); continue
        keep.append(w)
    if os.getenv("DEBUG_RAG") == "1":
        print("[tokens]", keep[:40])
    return keep

def score(doc: str, meta: dict, qtokens) -> float:
    dl = doc.lower()
    overlap = sum(1 for t in qtokens if f" {t} " in f" {dl} ")
    boost = 0.0
    for key in ("source","project","section","doc_id"):
        v = str(meta.get(key,"")).lower()
        if v:
            boost += 1.5 * sum(1 for t in qtokens if t in v)
    length = max(50, len(dl.split()))
    length_norm = min(1.0, 600/length)
    return (overlap + boost) * length_norm

def _sim_token_overlap(si: set, sj: set) -> float:
    inter = len(si & sj)
    return inter / max(1, min(len(si), len(sj)))

def mmr(documents, metadatas, qtokens, lambda_=0.75, topk=3):
    cand = list(range(len(documents)))
    selected = []
    token_sets = [set(d.lower().split()) for d in documents]
    while cand and len(selected) < topk:
        best, best_s = None, -1e9
        for i in cand:
            rel = score(documents[i], metadatas[i], qtokens)
            div = 0 if not selected else max(_sim_token_overlap(token_sets[i], token_sets[j]) for j in selected)
            s = lambda_*rel - (1-lambda_)*div
            if s > best_s:
                best, best_s = i, s
        selected.append(best)
        cand.remove(best)
    return [documents[i] for i in selected], [metadatas[i] for i in selected]

load_dotenv()  
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")

CHROMA_TENANT = os.getenv("CHROMA_TENANT")

# Check for missing Chroma Cloud credentials
missing_chroma_creds = (not CHROMA_API_KEY) or (not CHROMA_TENANT)
if missing_chroma_creds:
    print("[warning] Missing Chroma Cloud credentials → using local PersistentClient at ./.chroma")

client_oa = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

'''
def test_oa():
    """Quick test call to OpenAI."""
    if not client_oa:
        print("[openai] OPENAI_API_KEY not set; skipping test.")
        return
    resp = client_oa.responses.create(
        model="gpt-4o-mini",
        input="Summarize this project in 3 lines.",
        store=False,
    )
    print(resp.output_text)
'''

# Initialize Chroma client
if missing_chroma_creds:
    client = chromadb.PersistentClient(path=".chroma")
else:
    client = chromadb.CloudClient(
        api_key=CHROMA_API_KEY,
        tenant=CHROMA_TENANT,
        database="InvestoChat",
    )

collection = client.get_or_create_collection("investochat_projects")

# Validate collection accessibility early
try:
    _ = collection.count()
except Exception as e:
    print("[chroma] collection access failed. Check CHROMA_API_KEY/CHROMA_TENANT/database and server collection config.")
    raise

def search(query, k=5):
    results = collection.query(query_texts=[query], n_results=k)
    return results

def retrieve(q: str, k: int = 3, overfetch: int = 30):
    """
    Generic retriever with MMR. Overfetch from Chroma, then re-rank by token overlap
    with optional metadata boosts and diversity.
    """
    r = search(q, overfetch)
    docs = r.get("documents", [[]])[0]
    metas = r.get("metadatas", [[]])[0]

    if not docs:
        return {"documents": [[]], "metadatas": [[]]}

    qtokens = tokenize(q)
    if not qtokens:
        top_docs = docs[:max(1, k)]
        top_metas = metas[:max(1, k)]
        return {"documents": [list(top_docs)], "metadatas": [list(top_metas)]}

    ranked = sorted(zip(docs, metas), key=lambda t: score(t[0], t[1], qtokens), reverse=True)
    if ranked:
        docs_sorted, metas_sorted = zip(*ranked)
        docs_sorted, metas_sorted = list(docs_sorted), list(metas_sorted)
    else:
        docs_sorted, metas_sorted = [], []

    top_docs, top_metas = mmr(docs_sorted, metas_sorted, qtokens, lambda_=0.75, topk=max(1, k))

    if os.getenv("DEBUG_RAG") == "1":
        try:
            ids = [m.get("doc_id","unknown") for m in top_metas]
            print("[retrieve-doc-ids]", ids)
        except Exception:
            pass

    return {"documents": [list(top_docs)], "metadatas": [list(top_metas)]}

def show(q: str, k: int = 3):
    """
    Print top-k retrieved chunks with their doc_id for quick inspection.
    """
    r = retrieve(q, k)
    docs = r.get("documents", [[]])[0]
    metas = r.get("metadatas", [[]])[0]
    for i, (doc, meta) in enumerate(zip(docs, metas), 1):
        doc_id = meta.get("doc_id", "unknown")
        print(f"{i}) {doc_id}\n{doc[:600]}\n")

def normalize(ctx: str) -> str:
    # normalize bullets, spaces, and line breaks while keeping INR and percent symbols
    ctx = ctx.replace("•", "- ")
    ctx = ctx.replace("–", "-")
    ctx = re.sub(r"[ \t]+", " ", ctx)
    ctx = re.sub(r"\r?\n[ \t]+", "\n", ctx)
    # collapse excessive blank lines
    ctx = re.sub(r"\n{3,}", "\n\n", ctx)
    return ctx


def rag(q: str, k: int = 3, model: str = "gpt-4o-mini"):
    """
    Retrieve top-k chunks, build a grounded prompt, and return the LLM answer.
    Answer ONLY with facts found in <context>. If the facts are missing, return exactly: 'Not in the documents.'
    """
    r = retrieve(q, k)
    ctx_docs = r.get("documents", [[]])[0]
    if not ctx_docs:
        return "Not in the documents."
    ctx = "\n\n".join(ctx_docs)

    if os.getenv("DEBUG_RAG") == "1":
        metas = r.get("metadatas", [[]])[0]
        print("[ctx-ids]", [m.get("doc_id","unknown") for m in metas])
        print("[ctx-preview]", ctx[:400].replace("\n", " ") + " ...")

    ctx = normalize(ctx)

    if not client_oa:
        return "Not in the documents."

    prompt = (
        "You are a project-information assistant for real-estate brochures.\n"
        "Use ONLY facts found in <context>. Formatting instructions (like bullets) do not need to appear in context.\n"
        "If no relevant facts exist, reply exactly: 'Not in the documents.'\n"
        "Use concise bullets when listing items. Do not provide opinions or financial advice.\n"
        "<context>\n" + ctx + "\n</context>\n"
        f"Question: {q}\n"
        "Answer:"
    )

    try:
        resp = client_oa.responses.create(
            model=model,
            input=prompt,
            temperature=0
        )
        return resp.output_text
    except Exception as e:
        return f"[openai-error] {type(e).__name__}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InvestoChat query tester")
    parser.add_argument("--show", type=str, help="Query to show top-k retrieved chunks")
    parser.add_argument("-k", type=int, default=3, help="Top-k results")
    parser.add_argument("--rag", type=str, help="Query to run full RAG (retrieve + generate)")
    args = parser.parse_args()

    print(f"Chroma collection '{collection.name}' ready with {collection.count()} documents.")
    print("OpenAI:", "configured" if client_oa else "not configured")
    if args.show:
        show(args.show, args.k)
    if args.rag:
        ans = rag(args.rag, args.k)
        print(ans)
