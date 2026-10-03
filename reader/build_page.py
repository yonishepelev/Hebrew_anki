#!/usr/bin/env python3
"""Собирает страницу главы: reader/texts/chNN.txt + chNN_questions.json → reader/site/chNN.html

    python3 reader/build_page.py 1
"""
import json, re, sys, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(n):
    raw = (ROOT / 'texts' / f'ch{n:02d}.txt').read_text()
    meta = {'title': '', 'gloss': []}
    body = []
    for line in raw.splitlines():
        if line.startswith('# title:'):
            meta['title'] = line.split(':', 1)[1].strip()
        elif line.startswith('# gloss:'):
            w, _, g = line.split(':', 1)[1].partition('=')
            meta['gloss'].append({'w': w.strip(), 'g': g.strip()})
        elif not line.startswith('#'):
            body.append(line)
    paras = [p.strip() for p in '\n'.join(body).split('\n\n') if p.strip()]
    q = json.loads((ROOT / 'texts' / f'ch{n:02d}_questions.json').read_text())
    return meta, paras, q


def mark_new(p, gloss):
    s = html.escape(p)
    for i, g in enumerate(gloss):
        s = re.sub(rf'(?<![א-ת]){re.escape(html.escape(g["w"]))}(?![א-ת])',
                   f'<button type="button" class="nw" data-g="{i}">{html.escape(g["w"])}</button>', s, count=1)
    return s


def build(n):
    meta, paras, q = load(n)
    tpl = (ROOT / 'page_template.html').read_text()
    words = sum(len(re.findall('[א-ת]+', p)) for p in paras)
    text_html = '\n'.join(
        f'<p class="quote">{mark_new(p, meta["gloss"])}</p>' if p.startswith('"') else f'<p>{mark_new(p, meta["gloss"])}</p>'
        for p in paras)
    data = {'chapter': n, 'title': meta['title'], 'text': '\n\n'.join(paras), 'gloss': meta['gloss'], 'q': q}
    out = (tpl.replace('{{N}}', str(n))
              .replace('{{TITLE}}', html.escape(meta['title']))
              .replace('{{WORDS}}', str(words))
              .replace('{{TEXT}}', text_html)
              .replace('{{DATA}}', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
    dst = ROOT / 'site' / f'ch{n:02d}.html'
    dst.parent.mkdir(exist_ok=True)
    dst.write_text(out)
    print(dst)


if __name__ == '__main__':
    build(int(sys.argv[1]))
