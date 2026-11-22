#!/usr/bin/env python3
"""Перенос прогресса пользователя в пересобранную колоду.

    python3 tools/merge_progress.py <экспорт_с_телефона.apkg> <hebrew_frequency.apkg> <выход.apkg>

Экспорт с телефона — колода «Иврит::Частотный словарь» в .apkg С РАСПИСАНИЕМ.
Что делает (официальная библиотека Anki, `pip install anki`):
  1. открывает экспорт во временной коллекции (интервалы, история ответов, FSRS-состояния сохраняются);
  2. импортирует поверх свежую сборку make_deck.py без расписания: заметки обновляются по GUID,
     новые добавляются;
  3. удаляет заметки, которых в сборке больше нет;
  4. новым карточкам ставит позицию в очереди новых = ранг (у форм «ф220» — 220), т.е. вперемешку
     со старыми новыми карточками по частотности;
  5. проверяет: у каждой оставшейся карточки расписание не изменилось, история ответов не потеряна;
  6. экспортирует колоду с расписанием и ещё раз проверяет результат, импортировав его заново.
На телефоне: удалить старую колоду и импортировать выход (в той же коллекции).
"""
import os
import re
import sqlite3
import sys
import tempfile
import zipfile

from anki.collection import (Collection, DeckIdLimit, ExportAnkiPackageOptions,
                             ImportAnkiPackageOptions, ImportAnkiPackageRequest)
from anki.import_export_pb2 import ImportAnkiPackageUpdateCondition as UC

DECK = "Иврит::Частотный словарь"
SCHED = "c.type, c.queue, c.due, c.ivl, c.factor, c.reps, c.lapses, c.left, c.odue, c.flags, c.data"


def new_col():
    return Collection(os.path.join(tempfile.mkdtemp(), "c.anki2"))


def import_pkg(col, path, sched, update=UC.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_IF_NEWER):
    col.import_anki_package(ImportAnkiPackageRequest(package_path=path, options=ImportAnkiPackageOptions(
        with_scheduling=sched, with_deck_configs=sched, update_notes=update, update_notetypes=update)))


def deck_id(col):
    return col.decks.id_for_name(DECK)


def cards(col):
    did = deck_id(col)
    rows = col.db.all(f"select n.guid, c.ord, {SCHED} from cards c join notes n on n.id=c.nid "
                      f"where c.did=? or c.odid=?", did, did)
    return {(r[0], r[1]): tuple(r[2:]) for r in rows}


def pkg_guids(path):
    d = tempfile.mkdtemp()
    with zipfile.ZipFile(path) as z:
        name = "collection.anki21" if "collection.anki21" in z.namelist() else "collection.anki2"
        z.extract(name, d)
    con = sqlite3.connect(os.path.join(d, name))
    return {g for (g,) in con.execute("select guid from notes")}


def main(user_pkg, new_pkg, out):
    col = new_col()
    import_pkg(col, user_pkg, True)
    before = cards(col)
    revlog = col.db.scalar("select count() from revlog")
    old_guids = {g for g, _ in before}
    print(f"экспорт: {len(old_guids)} заметок, {len(before)} карточек, история ответов {revlog}")

    import_pkg(col, new_pkg, False, UC.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_ALWAYS)
    keep = pkg_guids(new_pkg)
    gone = old_guids - keep
    if gone:
        nids = col.db.list(f"select id from notes where guid in ({','.join('?' * len(gone))})", *gone)
        col.remove_notes(nids)
    after = cards(col)

    # очередь новых карточек: по рангу (поле Rank: "220" — лемма, "ф220" — форма), леммы и формы вперемешку;
    # обе карточки заметки — с одной позицией. Меняется только порядок ещё не начатых карточек.
    added = col.db.scalar("select count() from cards c join notes n on n.id=c.nid where c.did=? and n.guid not in "
                          f"({','.join('?' * len(old_guids))})", deck_id(col), *old_guids)
    news = col.db.all("select c.id, n.id, n.flds from cards c join notes n on n.id=c.nid where c.did=? and c.type=0",
                      deck_id(col))
    def order(row):
        rank = row[2].split("\x1f")[5]
        return (int(re.sub(r"\D", "", rank)), rank.startswith("ф"), row[1])
    pos = {}
    for cid, nid, flds in sorted(news, key=order):
        pos.setdefault(nid, len(pos))
        col.db.execute("update cards set due=? where id=?", pos[nid], cid)

    # проверка: расписание оставшихся карточек не изменилось (у новых — кроме позиции в очереди)
    after = cards(col)
    kept = {k: v for k, v in before.items() if k[0] in keep}
    strip_due = lambda v: v[:2] + v[3:] if v and v[0] == 0 else v
    diff = [k for k, v in kept.items() if strip_due(after.get(k)) != strip_due(v)]
    assert not diff, f"изменилось расписание у {len(diff)} карточек: {diff[:5]}"
    assert col.db.scalar("select count() from revlog") == revlog, "история ответов изменилась"
    print(f"удалено заметок: {len(gone)} ({len(before) - len(kept)} карточек); добавлено карточек: {added}")

    col.export_anki_package(out_path=out, options=ExportAnkiPackageOptions(
        with_scheduling=True, with_deck_configs=True, with_media=False, legacy=False),
        limit=DeckIdLimit(deck_id=deck_id(col)))
    final = cards(col)
    col.close()

    # контроль: выход, импортированный заново, совпадает с тем, что собрали
    chk = new_col()
    import_pkg(chk, out, True)
    back = cards(chk)
    assert set(back) == set(final), "состав карточек в выходном файле отличается"
    bad = [k for k in kept if back[k] != final[k]]
    assert not bad, f"после повторного импорта отличается расписание у {len(bad)} карточек"
    print(f"выход: {out} — {len({g for g, _ in back})} заметок, {len(back)} карточек; "
          f"история ответов {chk.db.scalar('select count() from revlog')}")
    chk.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
