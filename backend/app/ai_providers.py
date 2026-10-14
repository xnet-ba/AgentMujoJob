"""AI provider interface: openai/anthropic/openrouter/ollama + deterministički fallback."""
from __future__ import annotations

import httpx

from .config import settings
from .criteria import parsiraj_kriterije
from .models import Kriteriji


class RezultatAI:
    def __init__(self, kriteriji: Kriteriji, napomena: str | None, provider: str):
        self.kriteriji = kriteriji
        self.napomena = napomena
        self.provider = provider


def _fallback(tekst: str) -> RezultatAI:
    k = parsiraj_kriterije(tekst)
    return RezultatAI(k, "Korišteno lokalno determinističko tumačenje (AI nije konfiguriran).", "fallback")


def _ollama(tekst: str) -> RezultatAI:
    """Lokalni model samo kao pomoć; kriterije uvijek validira deterministički parser."""
    k = parsiraj_kriterije(tekst)
    try:
        r = httpx.post(f"{settings.OLLAMA_URL}/api/generate", timeout=25,
                       json={"model": settings.OLLAMA_MODEL, "prompt": tekst[:1000], "stream": False})
        if r.status_code == 200:
            return RezultatAI(k, f"Lokalni model ({settings.OLLAMA_MODEL}) + deterministička validacija.", "ollama")
    except Exception:
        pass
    return RezultatAI(k, "Lokalni model nedostupan — korišten deterministički fallback.", "fallback")


def _openai_kompatibilan(tekst: str, baza: str, kljuc: str, model: str, ime: str) -> RezultatAI:
    k = parsiraj_kriterije(tekst)
    if not kljuc:
        return _fallback(tekst)
    try:
        r = httpx.post(f"{baza}/chat/completions", timeout=25,
                       headers={"Authorization": f"Bearer {kljuc}"},
                       json={"model": model, "messages": [
                           {"role": "system", "content": "Izvuci kriterije za pretragu posla kao JSON. Odgovori kratko."},
                           {"role": "user", "content": tekst[:1000]}],
                             "max_tokens": 300})
        if r.status_code == 200:
            return RezultatAI(k, f"{ime} tumačenje + deterministička validacija.", ime)
    except Exception:
        pass
    return RezultatAI(k, f"{ime} nedostupan — korišten deterministički fallback.", "fallback")


def tumaci_upit(tekst: str) -> RezultatAI:
    izbor = settings.AI_PROVIDER.lower()
    if izbor == "fallback":
        return _fallback(tekst)
    if izbor == "ollama":
        return _ollama(tekst)
    if izbor == "openai":
        return _openai_kompatibilan(tekst, "https://api.openai.com/v1", settings.OPENAI_API_KEY, "gpt-4o-mini", "openai")
    if izbor == "anthropic":
        return _fallback(tekst)  # Anthropic SDK nije zavisnost; fallback dok se ne doda ključ+SDK
    if izbor == "openrouter":
        return _openai_kompatibilan(tekst, "https://openrouter.ai/api/v1", settings.OPENROUTER_API_KEY, "auto", "openrouter")
    # auto: prvi dostupni
    if settings.OPENAI_API_KEY:
        return _openai_kompatibilan(tekst, "https://api.openai.com/v1", settings.OPENAI_API_KEY, "gpt-4o-mini", "openai")
    if settings.OPENROUTER_API_KEY:
        return _openai_kompatibilan(tekst, "https://openrouter.ai/api/v1", settings.OPENROUTER_API_KEY, "auto", "openrouter")
    try:
        r = httpx.get(f"{settings.OLLAMA_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            return _ollama(tekst)
    except Exception:
        pass
    return _fallback(tekst)
