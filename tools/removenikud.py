#!/usr/bin/env python3
"""Снятие огласовок по правилам полного письма (Dicta, removenikud.dicta.org.il).

    python3 tools/removenikud.py "טִפּוּל שֻׁחְרַר שֵׁנָה"   # → טיפול שוחרר שינה

Правила Академии: огласованный текст → ктив мале (вставка ו/י, удвоение וו/יי).
"""
import json
import re
import sys
import urllib.request

URL = "https://remove-nikud-2-0.loadbalancer2.dicta.org.il/api"


def remove_nikud(text):
    body = json.dumps({"data": text, "genre": "modern", "maqaf": 1, "fQQ": True}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return re.sub("ֽ", "", json.load(r)["results"])


if __name__ == "__main__":
    print(remove_nikud(" ".join(sys.argv[1:])))
