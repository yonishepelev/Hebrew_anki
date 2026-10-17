#!/usr/bin/env python3
"""Запрос к словарю ИРИС (slovar.co.il, словарь Б. Подольского).

    python3 tools/slovar.py טיפול          # иврит → русский
    python3 tools/slovar.py -r слушать     # русский → иврит

Вывод: слово | транслит | перевод. Ударный слог (если словарь его отмечает)
отмечен знаком ˈ перед ним — и в иврите, и в транслите.
"""
import html
import re
import sys
import urllib.parse
import urllib.request

URL = "https://www.slovar.co.il/txajax.php"


def lookup(word, lang=1):
    q = urllib.parse.urlencode({"word": word, "word_enc": "", "lang": lang,
                                "nikud": 1, "transcription": 1})
    data = urllib.parse.urlencode({"xajax": "XTranslate",
                                   "xajaxargs[]": f"<xjxquery><q>{q}</q></xjxquery>"}).encode()
    with urllib.request.urlopen(URL, data, timeout=20) as r:
        s = r.read().decode("utf-8", "replace")
    s = re.sub(r"<!\[CDATA\[|\]\]>", "", s)
    s = re.sub(r'<span class="(?:word|translit)accent">(.*?)</span>', r"ˈ\1", s)
    out = []
    for block in re.split(r'<div class="cycle-?1">', s)[1:]:
        parts = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip()
                 for p in re.findall(r'<span class="(?:word|translit|translation)">(.*?)</span></div>', block, re.S)]
        out.append(" | ".join(re.sub(r"\s+", " ", p) for p in parts))
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    lang = 1
    if args and args[0] == "-r":
        lang, args = 2, args[1:]
    for line in lookup(" ".join(args), lang) or ["(ничего не найдено)"]:
        print(line)
