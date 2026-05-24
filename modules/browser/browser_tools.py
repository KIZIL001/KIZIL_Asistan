"""Web sayfası okuma, arama ve hava durumu araçları."""
import re
import requests
from bs4 import BeautifulSoup
from modules.tools.tool_manager import ToolManager

USER_AGENT = "KIZIL Asistan/2.0"
REQUEST_TIMEOUT = 10
MAX_REDIRECTS = 3
WHITESPACE_RE = re.compile(r'\s+')


def _normalize_text(text: str) -> str:
    return WHITESPACE_RE.sub(' ', text).strip()


def _make_session() -> requests.Session:
    """Her çağrı için yeni bir Session oluşturur. Çağıran with ile kullanmalı."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    session.verify = True
    session.max_redirects = MAX_REDIRECTS
    return session


def _web_oku(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "Hata: URL http:// veya https:// ile başlamalıdır."
    try:
        with _make_session() as session:
            resp = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        if resp.apparent_encoding and resp.encoding != resp.apparent_encoding:
            resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.content, "html.parser", from_encoding=resp.apparent_encoding)
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        # separator=" \n " ile satırlar anlamlı ayrılır, okunabilirlik artar
        text = soup.get_text(separator=" \n ", strip=True)
        clean = _normalize_text(text)
        if len(clean) > 5000:
            clean = clean[:5000] + "\n... (içerik kısaltıldı)"
        return clean if clean else "Sayfada okunabilir metin bulunamadı."
    except requests.exceptions.SSLError:
        return "SSL hatası: Sitenin sertifikası geçersiz veya güvenilir değil."
    except requests.exceptions.ConnectionError:
        return f"Bağlantı kurulamadı: {url}"
    except requests.exceptions.Timeout:
        return f"Zaman aşımı: {url} ({REQUEST_TIMEOUT} saniye)"
    except requests.exceptions.TooManyRedirects:
        return f"Çok fazla yönlendirme: {url} (maksimum: {MAX_REDIRECTS})"
    except requests.RequestException as e:
        return f"Sayfa alınamadı: {e}"


def _web_ara(sorgu: str) -> str:
    try:
        from duckduckgo_search import DDGS
        from duckduckgo_search.exceptions import DuckDuckGoSearchException, RatelimitException
        with DDGS() as ddgs:
            results = list(ddgs.text(sorgu, max_results=5))
        if not results:
            return "Sonuç bulunamadı."
        out = []
        for i, r in enumerate(results, 1):
            baslik = r.get("title", "Başlıksız")
            link = r.get("href") or r.get("url", "Link bulunamadı")
            ozet = r.get("body", "")
            out.append(f"{i}. {baslik}\n   {link}")
            if ozet:
                out.append(f"   Özet: {ozet}")
        return "\n\n".join(out)
    except ImportError:
        return "Hata: duckduckgo_search kütüphanesi yüklü değil."
    except RatelimitException:
        return "Arama motoru geçici olarak kullanılamıyor (hız sınırı)."
    except DuckDuckGoSearchException as e:
        return f"Arama motoru hatası: {e}"
    except Exception as e:
        return f"Arama hatası: {e}"


def _hava_durumu(sehir: str) -> str:
    try:
        url = f"https://wttr.in/{sehir}?format=%C+%t+%w+%h&lang=tr"
        with _make_session() as session:
            resp = session.get(url, timeout=5, allow_redirects=True)
        resp.raise_for_status()
        return f"{sehir} hava durumu: {resp.text.strip()}"
    except requests.exceptions.SSLError:
        return "SSL hatası: wttr.in sertifikası doğrulanamadı."
    except requests.exceptions.ConnectionError:
        return "Bağlantı kurulamadı: wttr.in"
    except requests.exceptions.Timeout:
        return "Hava durumu zaman aşımına uğradı."
    except requests.RequestException as e:
        return f"Hava durumu alınamadı: {e}"


def register_browser_tools(manager: ToolManager) -> None:
    manager.register(name="web_oku", description="Bir web sayfasının içeriğini okur.",
                     parameters={"url": "Okunacak web sayfasının adresi"}, func=_web_oku)
    manager.register(name="web_ara", description="DuckDuckGo'da arama yapar.",
                     parameters={"sorgu": "Aranacak kelime veya cümle"}, func=_web_ara)
    manager.register(name="hava_durumu", description="Bir şehrin anlık hava durumunu gösterir.",
                     parameters={"sehir": "Şehir adı"}, func=_hava_durumu)
