#!/usr/bin/env python3
"""Step 2: Reconstruct real bibliographic references from the cited PDFs.

Corpus ids are internal keys (and automated author-year keying collides, e.g.
`Sowa-2008-b/-c/-d` are three different papers). This step opens each cited
paper's parsed header and has an LLM extract the true authors/title/journal/
year/volume/pages, inventing nothing. Writes bib.json for the paper generator.

LLM (not regex) is used deliberately: parsed headers are messy and varied, and
this is a judgment task, not fixed-schema parsing.

Usage:
    python 02_extract_citations.py --source /path/to/corpus \
        --answers answers.json --out bib.json
"""
import argparse
import json
import os
import re
import sys
import urllib.request

from arca.config import DEFAULT


def head_text(source_dir, pid, n=2200):
    for ext in (".md", ".mmd"):
        fp = os.path.join(source_dir, pid + ext)
        if os.path.exists(fp):
            return open(fp, errors="ignore").read(n)
    return ""


def llm_extract(heads):
    """One batched call: id -> bibliographic dict."""
    blob = "\n\n".join(f"=== id: {pid} ===\n{txt[:1600]}" for pid, txt in heads.items())
    prompt = (
        "Below are parsed first-page headers of scientific papers, each with an "
        "internal id. For EACH id, extract the real bibliographic reference. Return "
        "STRICT JSON mapping id -> {\"authors\":\"Last FM, ...\",\"title\":\"...\","
        "\"journal\":\"...\",\"year\":YYYY,\"volume\":\"...\",\"pages\":\"...\"}. Use "
        "\"\" for any field you cannot determine (do NOT invent). Authors in "
        "'Last FM' form, comma-separated; 'et al.' only if >6 authors. Return ONLY "
        "the JSON object.\n\n" + blob)
    body = json.dumps({
        "model": DEFAULT.gen_model,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        DEFAULT.gen_base_url.rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {DEFAULT.gen_api_key}",
                 "Content-Type": "application/json"})
    txt = json.loads(urllib.request.urlopen(req, timeout=180).read())
    content = txt["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", content, re.S)
    return json.loads(m.group(0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="dir with parsed .md/.mmd")
    ap.add_argument("--answers", default="answers.json")
    ap.add_argument("--out", default="bib.json")
    a = ap.parse_args()

    answers = json.load(open(a.answers))
    cited = sorted({pid for v in answers.values() for pid in v.get("doc_ids", [])})
    heads = {pid: head_text(a.source, pid) for pid in cited}
    heads = {k: v for k, v in heads.items() if v.strip()}
    print(f"extracting refs for {len(heads)} cited papers")

    refs = llm_extract(heads)
    # stable numbering, alphabetical by first-author surname then year
    order = sorted(refs, key=lambda p: (refs[p].get("authors", "zzz").split()[:1],
                                        str(refs[p].get("year", ""))))
    num = {pid: i + 1 for i, pid in enumerate(order)}
    json.dump({"refs": refs, "num": num, "order": order}, open(a.out, "w"), indent=2)
    print(f"wrote {a.out} ({len(order)} references)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
