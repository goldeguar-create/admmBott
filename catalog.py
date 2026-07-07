# -*- coding: utf-8 -*-
import json
import re
import difflib
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "catalog.json"

# Botda ko'rsatiladigan asosiy brendlar (tugmalar uchun)
BRANDS = ["SKF", "KOYO", "NSK", "C&U", "BYZ", "VPZ", "FAG", "HRB"]


def load_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CATALOG = load_catalog()


def _norm(s: str) -> str:
    """Qidiruv uchun matnni normallashtirish: kichik harf, ortiqcha bo'shliqlarsiz."""
    s = s.lower()
    s = s.replace("&", " ")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def filter_by_brand(brand: str):
    if not brand or brand.lower() == "barchasi":
        return CATALOG
    b = brand.lower()
    return [item for item in CATALOG if b in _norm(item["name"])]


def search(query: str, brand: str = None, limit: int = 8):
    """
    Modelni qidiradi.
    1) Aniq/qisman mos kelish (substring) - brand ichida, keyin butun katalogda.
    2) Agar hech narsa topilmasa - o'xshash nomlarni (fuzzy) qaytaradi.
    Natija: (exact_matches: list, suggestions: list)
    """
    q = _norm(query)
    if not q:
        return [], []

    pool = filter_by_brand(brand) if brand else CATALOG
    tokens = q.split()

    def all_tokens_match(item):
        n = _norm(item["name"])
        return all(t in n for t in tokens)

    # 1) barcha so'zlar (masalan model raqami + brend nomi) mos kelishi kerak - tanlangan brend ichida
    exact = [item for item in pool if all_tokens_match(item)]
    if exact:
        return exact[:limit], []

    # 2) agar brend ichida topilmasa, butun katalogdan qidiramiz
    if brand:
        exact_all = [item for item in CATALOG if all_tokens_match(item)]
        if exact_all:
            return exact_all[:limit], []

    # 3) o'xshashlarini taklif qilamiz (fuzzy match)
    names = [item["name"] for item in (pool if pool else CATALOG)]
    close = difflib.get_close_matches(query, names, n=limit, cutoff=0.4)
    if not close:
        # so'nggi chora: so'z bo'yicha qisman moslik
        tokens = q.split()
        scored = []
        for item in (pool if pool else CATALOG):
            n = _norm(item["name"])
            score = sum(1 for t in tokens if t in n)
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: -x[0])
        close_items = [item for _, item in scored[:limit]]
    else:
        by_name = {item["name"]: item for item in CATALOG}
        close_items = [by_name[n] for n in close if n in by_name]

    return [], close_items


def format_item(item) -> str:
    price = f"{item['price']:,}".replace(",", " ")
    return f"🔩 {item['name']}\n💰 Narxi: {price} so'm"
