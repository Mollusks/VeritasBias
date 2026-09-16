import re
from html.parser import HTMLParser
from urllib.parse import unquote
from urllib.request import Request, urlopen


LEFT_PATTERNS = [
    "universal healthcare",
    "affordable health coverage",
    "healthcare",
    "minimum wage",
    "paid leave",
    "worker protections",
    "workers rights",
    "workers protections",
    "union protections",
    "labor protections",
    "labor unions",
    "reduce inequality",
    "income inequality",
    "public housing",
    "social safety net",
    "stronger pay for workers",
    "worker protections",
    "fair minimum wage",
    "workers and reduce inequality",
]

GREEN_PATTERNS = [
    "climate justice",
    "green new deal",
    "just transition",
    "renewable energy",
    "environmental justice",
    "climate action",
    "carbon neutrality",
    "clean energy",
    "decarbonization",
    "climate crisis",
    "climate breakdown",
    "eco socialist",
    "fossil fuels",
    "green economy",
    "environmental protection",
]

CONSERVATIVE_PATTERNS = [
    "tax cuts",
    "family values",
    "strong borders",
    "limited government",
    "lower taxes",
    "protect our borders",
    "defend family life",
    "keep the state out of everyday decisions",
    "small government",
    "traditional values",
    "state out of everyday decisions",
    "limited state",
]

LIBERTARIAN_PATTERNS = [
    "stay out of private life",
    "cut regulations",
    "civil liberties",
    "individual freedom",
    "reduce regulation",
    "defend individual freedom",
    "government should stay out",
    "protect privacy",
    "limited government",
    "state out of everyday decisions",
    "private life",
    "regulations that invade civil liberties",
]


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text_parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        if self._skip_depth == 0 and data and not data.isspace():
            self._text_parts.append(data)

    def get_text(self):
        return " ".join(self._text_parts)


def _normalize_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _pattern_hits(text, patterns):
    hits = 0
    for pattern in patterns:
        if pattern in text:
            hits += 1
    return hits


def detect_bias(text):
    normalized = _normalize_text(text)
    if not normalized:
        return {
            "overall_label": "Moderate / Center",
            "confidence": 0.0,
            "party_candidates": [{"name": "Independent / Centrist Coalition", "score": 0.0}],
            "scores": {},
        }

    scores = {
        "Progressive / Left": 0,
        "Green / Eco-Socialist": 0,
        "Conservative / Right": 0,
        "Libertarian": 0,
    }

    scores["Progressive / Left"] += _pattern_hits(normalized, LEFT_PATTERNS) * 2
    scores["Green / Eco-Socialist"] += _pattern_hits(normalized, GREEN_PATTERNS) * 3
    scores["Conservative / Right"] += _pattern_hits(normalized, CONSERVATIVE_PATTERNS) * 2
    scores["Libertarian"] += _pattern_hits(normalized, LIBERTARIAN_PATTERNS) * 2

    if "healthcare" in normalized and not any(keyword in normalized for keyword in GREEN_PATTERNS):
        scores["Progressive / Left"] += 2

    if "minimum wage" in normalized or "union" in normalized or "workers" in normalized:
        scores["Progressive / Left"] += 1

    if "family values" in normalized or "tax cuts" in normalized or "lower taxes" in normalized or "strong borders" in normalized:
        scores["Conservative / Right"] += 1

    if "civil liberties" in normalized or "individual freedom" in normalized or "reduce regulation" in normalized:
        scores["Libertarian"] += 2

    if "government should stay out" in normalized or "stay out of private life" in normalized:
        scores["Libertarian"] += 3

    if not any(score > 0 for score in scores.values()):
        overall_label = "Moderate / Center"
    else:
        overall_label = max(scores, key=scores.get)

    party_candidates = []
    if overall_label == "Progressive / Left":
        party_candidates = [
            {"name": "Democratic Party", "score": 0.92},
            {"name": "Progressive Wing", "score": 0.88},
        ]
    elif overall_label == "Green / Eco-Socialist":
        party_candidates = [
            {"name": "Green Party", "score": 0.97},
            {"name": "Eco-Socialist Movement", "score": 0.9},
        ]
    elif overall_label == "Conservative / Right":
        party_candidates = [
            {"name": "Republican Party", "score": 0.94},
            {"name": "Conservative Coalition", "score": 0.88},
        ]
    elif overall_label == "Libertarian":
        party_candidates = [
            {"name": "Libertarian Party", "score": 0.96},
            {"name": "Classical Liberal Movement", "score": 0.84},
        ]
    else:
        party_candidates = [{"name": "Independent / Centrist Coalition", "score": 0.9}]

    return {
        "overall_label": overall_label,
        "confidence": float(max(scores.values()) * 15 if max(scores.values()) else 10),
        "party_candidates": party_candidates,
        "scores": scores,
    }


def extract_text_from_url(url):
    if not url or not isinstance(url, str):
        return ""

    if url.startswith("data:"):
        _, _, encoded = url.partition(",")
        html = unquote(encoded)
    else:
        headers = {"User-Agent": "Mozilla/5.0"}
        request = Request(url, headers=headers)
        with urlopen(request) as response:
            html = response.read().decode("utf-8", errors="ignore")

    parser = _HTMLTextExtractor()
    parser.feed(html)
    text = parser.get_text()
    return re.sub(r"\s+", " ", text).strip()
