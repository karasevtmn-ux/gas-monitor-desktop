import logging
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Dict, Any, List
from core.util import normalize_whitespace, detect_link_type

log = logging.getLogger("parsers")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GASMonitor/0.2"

@dataclass
class ParseResult:
    snapshot: Dict[str, Any]
    act_texts: List[str]

def _fetch_html(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return r.text

def _extract_tabs_generic(soup: BeautifulSoup) -> List[str]:
    tabs = []
    for a in soup.select("a"):
        t = normalize_whitespace(a.get_text(" "))
        if any(k in t for k in ["Дело", "Движение дела", "Стороны", "Документы", "Судебные акты", "Акты"]):
            if len(t) <= 60:
                tabs.append(t)
    uniq = []
    for t in tabs:
        if t not in uniq:
            uniq.append(t)
    return uniq[:30]

def parse_case(url: str) -> ParseResult:
    t = detect_link_type(url)
    html = _fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    tabs = _extract_tabs_generic(soup)

    page_text = normalize_whitespace(soup.get_text(" "))
    page_text = page_text[:15000]

    act_texts: List[str] = []

    if t == "mos":
        keywords = ["Решение", "Определение", "Постановление", "Приговор", "Судебный акт"]
        if "Документы" in page_text:
            for k in keywords:
                if k in page_text:
                    idx = page_text.find(k)
                    if idx != -1:
                        act_texts.append(page_text[max(0, idx-500):min(len(page_text), idx+2000)])
                        break

    if t == "sudrf":
        if any("Судебные акты" in x or "Акты" == x for x in tabs):
            keywords = ["СУДЕБНЫЙ АКТ", "РЕШЕНИЕ", "ОПРЕДЕЛЕНИЕ", "ПОСТАНОВЛЕНИЕ", "ПРИГОВОР"]
            up = page_text.upper()
            for k in keywords:
                if k in up:
                    idx = up.find(k)
                    act_texts.append(page_text[max(0, idx-500):min(len(page_text), idx+4000)])
                    break

    snapshot = {
        "tabs": tabs,
        "page_text_hash_basis": page_text,
        "link_type": t,
    }
    return ParseResult(snapshot=snapshot, act_texts=act_texts)
