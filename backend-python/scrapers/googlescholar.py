"""
Scraper do Google Acadêmico (Google Scholar) via biblioteca scholarly

Utiliza o proxy SOCKS5 local configurado em GOOGLE_SCHOLAR_PROXY para
contornar o bloqueio de IPs de datacenters pelo Google Scholar.
Sem proxy configurado, o scraper retorna lista vazia imediatamente.

Referências:
  - scholarly: https://github.com/scholarly-python-package/scholarly
  - scholarly docs: https://scholarly.readthedocs.io/en/stable/

Variável de ambiente:
  GOOGLE_SCHOLAR_PROXY — ex.: socks5h://127.0.0.1:1080
    Use socks5h:// para DNS resolvido pelo proxy (mais seguro).
    Omitir ou deixar em branco desabilita a fonte sem erro.

Dependências extras (já em requirements.txt):
  scholarly>=1.7  PySocks>=1.7
"""
import asyncio
import os
import re
import threading
from typing import List, Dict, Any, Optional

from .cache import cache_medio

# --------------------------------------------------------------------------- #
# Inicialização do scholarly (uma vez por processo)                            #
# --------------------------------------------------------------------------- #

_proxy_url: Optional[str] = None
_scholarly_ready = False
_scholar_lock = threading.Semaphore(1)   # uma req. Scholar por vez (threading)

def _init_scholarly() -> bool:
    """
    Configura o scholarly com o proxy SOCKS5 definido em GOOGLE_SCHOLAR_PROXY.
    Retorna True se configurado com sucesso, False se sem proxy ou com erro.
    """
    global _proxy_url, _scholarly_ready

    proxy = os.getenv("GOOGLE_SCHOLAR_PROXY", "").strip()
    if not proxy:
        print("[GoogleScholar] GOOGLE_SCHOLAR_PROXY não definida. Desabilitando fonte.")
        return False

    # Normalizar formato do proxy para socks5h:// (DNS resolvido no proxy)
    proxy = proxy.replace("socks5://", "socks5h://", 1)
    if not proxy.startswith("socks5h://"):
        proxy = "socks5h://" + proxy

    try:
        from scholarly import scholarly as _scholarly, ProxyGenerator  # type: ignore
        pg = ProxyGenerator()
        # Configurar proxy SOCKS5 local (ex.: socks5h://127.0.0.1:1080)
        success = pg.SingleProxy(http=proxy, https=proxy)
        if success:
            _scholarly.use_proxy(pg)
            _proxy_url = proxy
            _scholarly_ready = True
            print(f"[GoogleScholar] Proxy configurado: {proxy}")
            return True
        else:
            print(f"[GoogleScholar] Falha ao configurar proxy: {proxy}")
            return False
    except ImportError:
        print("[GoogleScholar] scholarly não instalado. Adicione 'scholarly' ao requirements.txt.")
        return False
    except Exception as e:
        print(f"[GoogleScholar] Falha ao configurar proxy: {e}")
        return False


# Inicializa ao importar o módulo
_scholarly_ready = _init_scholarly()


# --------------------------------------------------------------------------- #
# Scraper                                                                      #
# --------------------------------------------------------------------------- #

class GoogleScholarScraper:
    """
    Scraper para Google Scholar usando a biblioteca scholarly com proxy SOCKS5.

    scholarly acessa o Google Scholar em HTML e analisa os resultados sem
    necessidade de API key — basta um proxy residencial ou SOCKS5 local.

    Se GOOGLE_SCHOLAR_PROXY não estiver definido, buscar() retorna [] sem erro.
    """

    # Número máximo de resultados por busca (cada resultado = 1 request ao Scholar)
    MAX_RESULTADOS = 15
    # Timeout total para a busca síncrona (segundos)
    TIMEOUT = 45

    def __init__(self):
        self._ready = _scholarly_ready

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos no Google Scholar via scholarly + proxy SOCKS5.

        Retorna lista vazia se proxy não configurado ou busca falhar.
        """
        if not self._ready:
            return []

        cache_key = f"googlescholar_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        try:
            resultados = await asyncio.wait_for(
                asyncio.to_thread(self._buscar_sync, termo, ano_min),
                timeout=self.TIMEOUT,
            )
        except asyncio.TimeoutError:
            print(f"[GoogleScholar] Timeout ({self.TIMEOUT}s) para '{termo}'")
            resultados = []
        except Exception as e:
            print(f"[GoogleScholar] Erro: {e}")
            resultados = []

        cache_medio.set(cache_key, resultados)
        return resultados

    def _buscar_sync(self, termo: str, ano_min: int) -> List[Dict[str, Any]]:
        """
        Executa a busca de forma síncrona (roda em thread separada).

        Usa _scholar_lock para impedir chamadas concorrentes ao Google Scholar,
        reduzindo a chance de CAPTCHA / bloqueio de IP.
        """
        acquired = _scholar_lock.acquire(timeout=30)
        if not acquired:
            print("[GoogleScholar] Semáforo ocupado — busca cancelada")
            return []

        try:
            from scholarly import scholarly as _scholarly  # type: ignore
            resultados: List[Dict[str, Any]] = []

            gen = _scholarly.search_pubs(termo)
            count = 0
            while count < self.MAX_RESULTADOS:
                try:
                    pub = next(gen)
                except StopIteration:
                    break
                except Exception as e:
                    print(f"[GoogleScholar] Erro ao iterar resultados: {e}")
                    break

                parsed = self._parse_pub(pub, termo, ano_min)
                if parsed:
                    resultados.append(parsed)
                    count += 1

            return resultados

        except Exception as e:
            print(f"[GoogleScholar] Erro na busca síncrona: {e}")
            return []
        finally:
            _scholar_lock.release()

    @staticmethod
    def _parse_pub(
        pub: Dict[str, Any], termo: str, ano_min: int
    ) -> Optional[Dict[str, Any]]:
        """Converte um resultado scholarly para o formato padrão do projeto."""
        try:
            bib: Dict[str, Any] = pub.get("bib") or {}

            titulo = (bib.get("title") or "").strip()
            if not titulo or len(titulo) < 5:
                return None

            # Ano de publicação
            ano_raw = bib.get("pub_year") or ""
            ano: Optional[int] = None
            try:
                ano = int(str(ano_raw).strip()[:4])
            except (ValueError, TypeError):
                pass

            # Filtro de ano mínimo
            if ano and ano < ano_min:
                return None

            # Autores — scholarly retorna string "A and B and C"
            autores: Optional[List[str]] = None
            autores_raw = bib.get("author") or ""
            if isinstance(autores_raw, list):
                autores = [str(a).strip() for a in autores_raw if str(a).strip()][:10]
            elif isinstance(autores_raw, str) and autores_raw.strip():
                autores = [
                    a.strip()
                    for a in re.split(r"\s+and\s+", autores_raw, flags=re.IGNORECASE)
                    if a.strip()
                ][:10]

            # URLs — preferir URL do paper real; fallback para URL Scholar
            url: Optional[str] = (
                bib.get("pub_url")
                or pub.get("pub_url")
                or bib.get("eprint_url")
                or pub.get("eprint_url")
                or None
            )

            # Abstract
            resumo_raw = (bib.get("abstract") or "").strip()
            resumo: Optional[str] = resumo_raw[:3000] if resumo_raw else None

            # Periódico / venue
            journal: Optional[str] = (bib.get("venue") or bib.get("journal") or None)
            if journal:
                journal = journal.strip() or None

            # Citações
            citation_count: Optional[int] = pub.get("num_citations")

            # Volume / issue / páginas
            volume = str(bib.get("volume") or "").strip()
            issue  = str(bib.get("number") or "").strip()
            paginas = str(bib.get("pages") or "").strip()

            return {
                "id": None,
                "titulo": titulo,
                "autores": autores,
                "resumo": resumo,
                "url": url,
                "fonte": "Google Scholar",
                "journal": journal,
                "volume": volume,
                "issue": issue,
                "paginas": paginas,
                "tipo": "artigo",
                "ano": ano,
                "doi": None,   # scholarly não retorna DOI diretamente
                "pmid": None,
                "citation_count": citation_count,
                "keywords": [termo],
            }
        except Exception:
            return None
