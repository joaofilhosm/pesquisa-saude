"""
Formatador de citações e referências no padrão ABNT (NBR 10520:2023)
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import re

# Compilar regex uma vez no módulo (performance)
_RE_INICIAIS = re.compile(r'^[A-Z]{1,3}$')
_RE_ANO = re.compile(r'(20\d{2})')


@dataclass
class Artigo:
    """Representa um artigo/publicação para formatação ABNT"""
    titulo: str
    autores: List[str] = field(default_factory=list)
    ano: Optional[int] = None
    fonte: str = ""
    url: str = ""
    doi: str = ""
    volume: str = ""
    numero: str = ""
    paginas: str = ""
    tipo: str = "artigo"  # artigo, protocolo, diretriz, pcdt

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> "Artigo":
        """Cria Artigo a partir de dicionário"""
        return cls(
            titulo=dados.get("titulo", ""),
            autores=dados.get("autores", []) or [],
            ano=dados.get("ano"),
            fonte=dados.get("fonte", ""),
            url=dados.get("url", "") or "",
            doi=dados.get("doi", "") or "",
            volume=dados.get("volume", "") or "",
            numero=dados.get("issue", "") or dados.get("numero", "") or "",
            paginas=dados.get("paginas", "") or "",
            tipo=dados.get("tipo", "artigo")
        )


class ABNTFormatador:
    """
    Formata citações e referências conforme NBR 10520:2023

    Exemplos:
    - Citação curta: (BRASIL, 2023) ou (SBMFC, 2022)
    - Referência completa: formatada conforme NBR 6023
    """

    # Mapeamento de fontes para nomes em citações
    INSTITUICOES = {
        "ministério da saúde": "BRASIL",
        "brasil": "BRASIL",
        "sbmfc": "SBMFC",
        "sociedade brasileira de medicina de família e comunidade": "SBMFC",
        "sbp": "SBP",
        "sociedade brasileira de pediatria": "SBP",
        "sbpt": "SBPT",
        "sociedade brasileira de pneumologia e tisiologia": "SBPT",
        "sbc": "SBC",
        "sociedade brasileira de cardiologia": "SBC",
        "anvisa": "BRASIL",
        "scielo": "SCIELO",
        "lilacs": "LILACS",
        "pubmed": "PUBMED",
        "hc-fmusp": "HC-FMUSP",
        "hospital das clínicas": "HC-FMUSP",
        "sírio-libanês": "HOSPITAL SÍRIO-LIBANÊS",
        "einstein": "HOSPITAL ALBERT EINSTEIN",
    }

    def formatar_citacao_curta(self, artigo: Artigo) -> str:
        """
        Formata citação curta no formato (AUTOR, ano)

        Para instituições: (BRASIL, 2023)
        Para autores pessoais: (SOBRENOME, 2023)
        """
        ano = artigo.ano or datetime.now().year

        # Se tem autores pessoais
        if artigo.autores and len(artigo.autores) > 0:
            primeiro_autor = artigo.autores[0]
            sobrenome = self._extrair_sobrenome(primeiro_autor)
            return f"({sobrenome}, {ano})"

        # Se é instituição/órgão
        if artigo.fonte:
            nome_citacao = self._normalizar_instituicao(artigo.fonte)
            return f"({nome_citacao}, {ano})"

        # Fallback
        return f"({artigo.titulo.split()[0].upper()}, {ano})"

    def formatar_referencia(self, artigo: Artigo) -> str:
        """
        Formata referência completa conforme NBR 6023

        Modelos:
        - Artigo: AUTORES. Título. Revista, v. X, n. Y, p. Z, ano.
        - Documento online: INSTITUIÇÃO. Título. Ano. Disponível em: URL.
        """
        # Autoria
        if artigo.autores and len(artigo.autores) > 0:
            autores_formatados = self._formatar_autores(artigo.autores)
        elif artigo.fonte:
            autores_formatados = self._normalizar_instituicao(artigo.fonte)
        else:
            autores_formatados = "S.N."  # sem nome

        # Título
        titulo = artigo.titulo
        if not titulo.endswith('.'):
            titulo += '.'

        # Tipo de documento
        if artigo.tipo in ['protocolo', 'diretriz', 'pcdt']:
            return self._formatar_documento_instituicao(
                autores_formatados, titulo, artigo
            )
        elif artigo.tipo == 'artigo':
            return self._formatar_artigo(
                autores_formatados, titulo, artigo
            )
        else:
            return self._formatar_generico(
                autores_formatados, titulo, artigo
            )

    def _extrair_sobrenome(self, autor: str) -> str:
        """Extrai sobrenome do autor para citação curta"""
        autor = autor.strip()
        partes = autor.split()

        if len(partes) == 1:
            return partes[0].upper()

        # Formato PubMed: "Silva JM" – última parte são iniciais maiúsculas
        ultima = partes[-1]
        if _RE_INICIAIS.match(ultima):
            # Sobrenome é tudo antes das iniciais
            return ' '.join(partes[:-1]).upper()

        # Formato "Sobrenome, Nome"
        if ',' in autor:
            return autor.split(',')[0].strip().upper()

        # Formato "Nome Sobrenome" – pegar última parte
        return partes[-1].upper()

    def _normalizar_instituicao(self, instituicao: str) -> str:
        """Normaliza nome de instituição para citação"""
        inst_lower = instituicao.lower().strip()

        for chave, valor in self.INSTITUICOES.items():
            if chave in inst_lower:
                return valor

        # Fallback: usar sigla ou primeira palavra em maiúsculas
        sigla = re.search(r'\b([A-Z]{2,5})\b', instituicao)
        if sigla:
            return sigla.group(1)

        return instituicao.split()[0].upper()

    def _formatar_autores(self, autores: List[str]) -> str:
        """Formata lista de autores no padrão ABNT NBR 6023"""
        if not autores:
            return "S.N."

        autores_formatados = []
        for autor in autores[:3]:  # Máximo 3 autores, depois usa et al.
            autor = autor.strip()
            if not autor:
                continue

            # Formato PubMed: "Silva JM" (sobrenome + iniciais sem vírgula)
            # Detectar: última "palavra" são iniciais maiúsculas
            partes = autor.split()
            if len(partes) >= 2:
                ultima = partes[-1]
                # Iniciais: string com 1-3 maiúsculas (sem pontos)
                if _RE_INICIAIS.match(ultima):
                    sobrenome = ' '.join(partes[:-1]).upper()
                    autores_formatados.append(f"{sobrenome}, {ultima}")
                    continue

            # Formato "Sobrenome, Nome" – já está no padrão ABNT
            if ',' in autor:
                partes_virgula = autor.split(',', 1)
                sobrenome = partes_virgula[0].strip().upper()
                nome = partes_virgula[1].strip()
                autores_formatados.append(f"{sobrenome}, {nome}")
                continue

            # Formato "Nome Sobrenome" – inverter
            if len(partes) >= 2:
                sobrenome = partes[-1].upper()
                nomes = ' '.join(partes[:-1])
                autores_formatados.append(f"{sobrenome}, {nomes}")
            else:
                autores_formatados.append(autor.upper())

        if not autores_formatados:
            return "S.N."

        if len(autores) > 3:
            return f"{autores_formatados[0]} et al."
        elif len(autores_formatados) == 1:
            return autores_formatados[0]
        else:
            return '; '.join(autores_formatados)

    def _formatar_documento_instituicao(
        self, autor: str, titulo: str, artigo: Artigo
    ) -> str:
        """Formata documento institucional (protocolos, diretrizes)"""
        ano = artigo.ano or datetime.now().year
        referencia = f"{autor} {titulo} {ano}."

        if artigo.url:
            referencia += f" Disponível em: {artigo.url}."
            referencia += f" Acesso em: {datetime.now().strftime('%d %b %Y')}."

        if artigo.doi:
            referencia += f" DOI: {artigo.doi}."

        return referencia

    def _formatar_artigo(
        self, autor: str, titulo: str, artigo: Artigo
    ) -> str:
        """Formata artigo científico no padrão ABNT NBR 6023"""
        ano = artigo.ano or datetime.now().year
        referencia = f"{autor} {titulo} "

        # Periódico (evitar nomes de bases como fonte)
        fontes_genericas = {'SciELO', 'PubMed', 'LILACS', 'BVS'}
        if artigo.fonte and artigo.fonte not in fontes_genericas:
            referencia += f"{artigo.fonte}"
            if artigo.volume:
                referencia += f", v. {artigo.volume}"
            if artigo.numero:
                referencia += f", n. {artigo.numero}"
            if artigo.paginas:
                referencia += f", p. {artigo.paginas}"
            referencia += f", {ano}."
        else:
            referencia += f"{ano}."

        if artigo.url:
            referencia += f" Disponível em: {artigo.url}."
            referencia += f" Acesso em: {datetime.now().strftime('%d %b. %Y')}."

        if artigo.doi:
            referencia += f" DOI: {artigo.doi}."

        return referencia

    def _formatar_generico(
        self, autor: str, titulo: str, artigo: Artigo
    ) -> str:
        """Formata referência genérica"""
        ano = artigo.ano or datetime.now().year
        referencia = f"{autor} {titulo} {ano}."

        if artigo.url:
            referencia += f" Disponível em: {artigo.url}."
            referencia += f" Acesso em: {datetime.now().strftime('%d %b %Y')}."

        return referencia

    def formatar_referencias_lista(
        self, artigos: List[Artigo], citacoes_no_texto: List[str] = None
    ) -> str:
        """
        Formata lista de referências para exibição no final

        Se citacoes_no_texto for fornecido, ordena conforme aparecem no texto
        """
        if not artigos:
            return ""

        referencias = []
        for artigo in artigos:
            ref = self.formatar_referencia(artigo)
            referencias.append(ref)

        # Ordenar alfabeticamente (padrão ABNT)
        referencias.sort()

        return "\n\n".join(referencias)


# Singleton
formatador = ABNTFormatador()
