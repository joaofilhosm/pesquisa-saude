"""
Cliente Supabase para conexão com o banco de dados
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

load_dotenv()

class SupabaseDB:
    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL", "")
        self.key: str = os.getenv("SUPABASE_KEY", "")
        self.client: Client = create_client(self.url, self.key)

    # === CRUD de Artigos ===

    def inserir_artigo(self, artigo: Dict[str, Any]) -> str:
        """Insere um novo artigo e retorna o ID"""
        response = self.client.table("artigos").insert(artigo).execute()
        return response.data[0]["id"] if response.data else ""

    def buscar_artigo_por_doi(self, doi: str) -> Optional[Dict]:
        """Busca artigo por DOI"""
        response = self.client.table("artigos").select("*").eq("doi", doi).execute()
        return response.data[0] if response.data else None

    def buscar_artigo_por_pmid(self, pmid: str) -> Optional[Dict]:
        """Busca artigo por PMID"""
        response = self.client.table("artigos").select("*").eq("pmid", pmid).execute()
        return response.data[0] if response.data else None

    def atualizar_artigo(self, artigo_id: str, dados: Dict[str, Any]) -> bool:
        """Atualiza artigo existente"""
        response = self.client.table("artigos").update(dados).eq("id", artigo_id).execute()
        return response.data is not None

    # === Buscas ===

    def pesquisar(
        self,
        query: str,
        ano_min: int = 2016,
        fontes: Optional[List[str]] = None,
        tipos: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Pesquisa artigos no banco
        - query: termos de busca
        - ano_min: ano mínimo (padrão 2016 = últimos 10 anos)
        - fontes: filtrar por fontes específicas
        - tipos: filtrar por tipos (artigo, protocolo, diretriz, pcdt)
        """
        db_query = self.client.table("artigos").select("*")

        # Filtro por ano (últimos 10 anos)
        db_query = db_query.gte("ano", ano_min)

        # Filtro por fontes
        if fontes:
            db_query = db_query.in_("fonte", fontes)

        # Filtro por tipos
        if tipos:
            db_query = db_query.in_("tipo", tipos)

        # Ordenar por relevância (ano mais recente primeiro)
        db_query = db_query.order("ano", desc=True).limit(limit)

        response = db_query.execute()

        # Filtragem full-text no cliente (busca fuzzy nos campos)
        resultados = []
        query_lower = query.lower()
        for artigo in response.data:
            score = 0
            if artigo.get("titulo") and query_lower in artigo["titulo"].lower():
                score += 3
            if artigo.get("resumo") and query_lower in artigo["resumo"].lower():
                score += 2
            if artigo.get("keywords"):
                for kw in artigo["keywords"]:
                    if query_lower in kw.lower():
                        score += 1
            if score > 0:
                artigo["_score"] = score
                resultados.append(artigo)

        # Ordenar por score
        resultados.sort(key=lambda x: x.get("_score", 0), reverse=True)
        return resultados[:limit]

    # === Referências ABNT ===

    def salvar_referencia(self, artigo_id: str, citacao: str, referencia: str) -> str:
        """Salva referência formatada em ABNT"""
        response = self.client.table("referencias_abnt").insert({
            "artigo_id": artigo_id,
            "citacao_curta": citacao,
            "referencia_completa": referencia
        }).execute()
        return response.data[0]["id"] if response.data else ""

    def buscar_referencias(self, artigo_ids: List[str]) -> List[Dict]:
        """Busca referências ABNT para lista de artigos"""
        response = self.client.table("referencias_abnt").select(
            "artigo_id, citacao_curta, referencia_completa"
        ).in_("artigo_id", artigo_ids).execute()
        return response.data

    # === Cache de Buscas ===

    def salvar_busca_cache(self, query: str, resultados_ids: List[str], ttl_horas: int = 24) -> str:
        """Salva busca no cache"""
        import json
        response = self.client.table("buscas_cache").insert({
            "query": query,
            "resultados": json.dumps(resultados_ids),  # Converte lista para JSON string
            "expires_at": (datetime.now() + timedelta(hours=ttl_horas)).isoformat()
        }).execute()
        return response.data[0]["id"] if response.data else ""

    def buscar_cache(self, query: str) -> Optional[List[str]]:
        """Busca cache válido"""
        response = self.client.table("buscas_cache").select(
            "resultados"
        ).eq("query", query).gt("expires_at", datetime.now().isoformat()).execute()
        return response.data[0]["resultados"] if response.data else None

    # === Fontes ===

    def listar_fontes(self, ativas: bool = True) -> List[Dict]:
        """Lista fontes de pesquisa"""
        query = self.client.table("fontes").select("*")
        if ativas:
            query = query.eq("ativo", True)
        query = query.order("prioridade")
        response = query.execute()
        return response.data


# Singleton
db = SupabaseDB()
