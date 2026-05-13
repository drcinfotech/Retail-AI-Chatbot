"""
Product catalog wrapper.

Loads products.json on construction and exposes search / filter methods.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional


DATA_PATH = Path(__file__).parent.parent / "data" / "products.json"


class ProductCatalog:
    def __init__(self, data_path: Path = DATA_PATH):
        with open(data_path, "r", encoding="utf-8") as f:
            self._products: list[dict] = json.load(f)
        self._by_id = {p["id"]: p for p in self._products}

    # ─── Lookup ─────────────────────────────────────────────
    def get(self, product_id: str) -> Optional[dict]:
        return self._by_id.get(product_id)

    def all(self) -> list[dict]:
        return list(self._products)

    # ─── Search / filter ────────────────────────────────────
    def search(
        self,
        categories: Optional[list[str]] = None,
        colors: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        gender: Optional[str] = None,
        price_max: Optional[int] = None,
        text: Optional[str] = None,
        limit: int = 3,
    ) -> list[dict]:
        """Return products matching the filters, scored by relevance."""
        results: list[tuple[float, dict]] = []

        for p in self._products:
            score = 0.0

            if categories:
                hits = sum(1 for c in categories
                           if c == p["category"] or c == p["subcategory"])
                if hits == 0:
                    # No category match — skip if categories were specified
                    continue
                score += hits * 2.0

            if colors:
                if any(c in p["color"].lower() for c in colors):
                    score += 1.0

            if tags:
                hits = sum(1 for t in tags if t in p["tags"])
                score += hits * 1.5

            if gender and gender != "unisex":
                if p["gender"] != gender and p["gender"] != "unisex":
                    continue
                if p["gender"] == gender:
                    score += 0.5

            if price_max is not None:
                if p["price"] > price_max:
                    continue
                score += 0.3  # bonus for being in budget

            if text:
                t = text.lower()
                if t in p["name"].lower() or t in p["brand"].lower() or t in p["description"].lower():
                    score += 1.0

            # Default tiny bonus from rating × log(reviews-ish)
            score += (p["rating"] - 4.0) * 0.4
            score += min(p["reviews"], 5000) / 50000.0

            if score > 0 or (not any([categories, colors, tags, gender, text]) and price_max is not None):
                results.append((score, p))

        results.sort(key=lambda x: -x[0])
        return [p for _, p in results[:limit]]

    def popular(self, limit: int = 3, category: Optional[str] = None) -> list[dict]:
        """Top-rated products, optionally within a category."""
        pool = self._products
        if category:
            pool = [p for p in pool if p["category"] == category or p["subcategory"] == category]
        ranked = sorted(pool, key=lambda p: (-p["rating"], -p["reviews"]))
        return ranked[:limit]

    def random_sample(self, k: int = 3) -> list[dict]:
        return random.sample(self._products, min(k, len(self._products)))


# Singleton instance the rest of the app uses
catalog = ProductCatalog()
