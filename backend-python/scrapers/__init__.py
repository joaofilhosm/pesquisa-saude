"""
Scrapers para fontes brasileiras de saúde
"""
from .ministerio_saude import MinisterioSaudeScraper
from .sbmfc import SBMFCScraper
from .sbp import SBPScraper
from .sbpt import SBPTScraper
from .sbc import SBCScraper
from .scielo import SciELOScraper
from .lilacs import LILACSScraper
from .pubmed import PubMedScraper

__all__ = [
    "MinisterioSaudeScraper",
    "SBMFCScraper",
    "SBPScraper",
    "SBPTScraper",
    "SBCScraper",
    "SciELOScraper",
    "LILACSScraper",
    "PubMedScraper"
]
