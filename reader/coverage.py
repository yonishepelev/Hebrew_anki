#!/usr/bin/env python3
"""Покрытие текста знакомыми словами.

Знакомые = записи колоды с рангом <= MAX_RANK + изученные в Anki (progress.json)
+ их формы (FORMS, PRES, PARADIGMS, мн. ч. из заметок, полные парадигмы Pealim)
+ интернационализмы (loanwords.txt) + имена/новые слова главы (# known: в файле главы).

    python3 reader/coverage.py reader/texts/ch01.txt
"""
import json, re, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAX_RANK = 1000
NQ = re.compile('[֑-ׇ]')
FINAL = str.maketrans('ךםןףץ', 'כמנפצ')
PREFIXES = 'והבלמשכ'


def plain(s):
    return NQ.sub('', s).replace('־', ' ').replace('״', '"').replace('׳', "'")


def skel(w):
    """Скелет слова без огласовок и матерей чтения ו/י — сравнение полного и дефектного письма."""
    w = w.translate(FINAL)
    return w[0] + re.sub('[וי]', '', w[1:]) if w else w


def he_words(s):
    return re.findall(r"[א-ת]+(?:['\"][א-ת]+)?", plain(s))


def adj_forms(w):
    out = {w}
    base = w[:-1] if w.endswith('ה') or w.endswith('י') and len(w) > 3 else w
    for suf in ('ה', 'ת', 'ים', 'ות', 'ית', 'יים', 'יות'):
        out.add(w + suf)
        out.add(base + suf)
    return out


def load_known():
    src = (ROOT.parent / 'make_deck.py').read_text().split('\nALL = ')[0]
    ns = {}
    exec(src, ns)
    entries = [e[:5] for e in ns['W']] + [e[:5] for e in ns['W_MORE']]
    studied = set(json.loads((ROOT / 'progress.json').read_text())['studied_ranks'])
    pealim = json.loads((ROOT / 'pealim_forms.json').read_text())
    known = set()
    for r, he, nq, ru, note in entries:
        if r > MAX_RANK and r not in studied:
            continue
        words = set(he_words(he)) | set(he_words(nq))
        for m in re.finditer(r'(?:мн\.|ж\.р\.)\s*([^;,(]+)', note):
            words |= set(he_words(m.group(1)))
        for m in re.finditer(r'прил\.\s*([^;,(—]+)', note):
            for w in he_words(m.group(1)):
                words |= adj_forms(w)
        for f in (ns['FORMS'].get(r, ()), ns['PRES'].get(r, ())):
            for x in f:
                words |= set(he_words(x))
        words |= set(pealim.get(str(r), ()))
        if note.startswith(('прил', 'сущ', 'числ')) or 'прил' in note[:12]:
            for w in list(words):
                words |= adj_forms(w)
        known |= words
    for x in ns.get('PARADIGMS', {}).values():
        for f in x:
            known |= set(he_words(f))
    for lw in (ROOT / 'loanwords.txt', ROOT / 'basic.txt'):
        if not lw.exists():
            continue
        for line in lw.read_text().splitlines():
            line = line.split('#')[0]
            for w in he_words(line):
                known |= adj_forms(w)
    return {skel(w) for w in known if w}


def is_known(w, K):
    if skel(w) in K:
        return True
    for i in range(1, 4):  # до трёх приставок: ו+ש+ב…
        if len(w) - i < 2 or any(c not in PREFIXES for c in w[:i]):
            break
        rest = w[i:]
        if skel(rest) in K:
            return True
        # ב/ל/כ после артикля «съедают» ה: בבית, לבית
    return False


def analyze(text, extra=()):
    K = load_known() | {skel(w) for x in extra for w in he_words(x)}
    toks = he_words(text)
    unknown = [w for w in toks if not is_known(w, K)]
    return toks, unknown


if __name__ == '__main__':
    path = Path(sys.argv[1])
    raw = path.read_text()
    meta = lambda tag: [l.split(':', 1)[1] for l in raw.splitlines() if l.startswith(tag)]
    names, new = meta('# known:'), meta('# new:')
    body = '\n'.join(l for l in raw.splitlines() if not l.startswith('#'))
    toks, unk = analyze(body, names)
    newset = {skel(w) for x in new for w in he_words(x)}
    still = [w for w in unk if not any(skel(w[i:]) in newset for i in range(4))]
    cov = 1 - len(unk) / max(len(toks), 1)
    print(f'слов: {len(toks)}  знакомых: {cov:.1%}  новых (# new): {len(unk) - len(still)}  не объяснённых: {len(still)}')
    print('OK' if cov >= 0.97 and not still else 'FAIL: нужно ≥97% знакомых и 0 не объяснённых')
    from collections import Counter
    for w, n in Counter(unk).most_common():
        print(f'  {w} ×{n}' + ('' if w in still else '  (new)'))
