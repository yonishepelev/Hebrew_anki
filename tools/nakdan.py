#!/usr/bin/env python3
"""Автоматическая огласовка через Dicta Nakdan (nakdan.dicta.org.il).

    python3 tools/nakdan.py "הוא שוחרר מהצבא"      # огласованный текст
    python3 tools/nakdan.py -a "שוחרר"              # + варианты для каждого слова

Накдан — нейросеть, а не словарь: результат проверять (Pealim, ИРИС).
Мета́г (U+05BD) и служебные метки убираются.
"""
import json
import re
import sys
import urllib.request

URL = "https://nakdan-u2-1a.loadbalancer.dicta.org.il/api"


def clean(w):
    return re.sub(r"[ֽ|]", "", w)


def nakdan(text):
    body = json.dumps({"addmorph": True, "keepmetagim": True, "keepqq": False,
                       "nodageshdefmem": False, "patachma": False, "task": "nakdan",
                       "data": text, "useTokenization": True, "genre": "modern"}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]


if __name__ == "__main__":
    args = sys.argv[1:]
    alts = bool(args) and args[0] == "-a"
    if alts:
        args = args[1:]
    data = nakdan(" ".join(args))
    out, notes = [], []
    for t in data:
        opts = t["nakdan"]["options"]
        if t["sep"] or not opts:
            out.append(t["str"])
            continue
        out.append(clean(opts[0]["w"]))
        if alts:
            seen = []
            for o in opts:
                w = clean(o["w"])
                if w not in seen:
                    seen.append(w)
            notes.append(f'{t["str"]}: ' + " / ".join(seen))
    print("".join(out))
    for n in notes:
        print("  " + n)
