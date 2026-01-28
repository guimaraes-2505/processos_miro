"""
Parser de arquivos Markdown.
Pré-processa transcrições para extração via LLM.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.utils.exceptions import FileNotFoundError, InvalidFileFormatError, ParsingError
from src.utils.logger import get_logger

logger = get_logger()


class MarkdownParser:
    """
    Parser para arquivos Markdown de transcrições de processos.
    """

    def __init__(self):
        self.content: str = ""
        self.file_path: Optional[str] = None

    def load_file(self, file_path: str) -> str:
        """
        Carrega um arquivo Markdown.

        Args:
            file_path: Caminho para o arquivo .md

        Returns:
            Conteúdo do arquivo

        Raises:
            FileNotFoundError: Se o arquivo não existe
            InvalidFileFormatError: Se não é um arquivo .md
            ParsingError: Se há erro ao ler o arquivo
        """
        path = Path(file_path)

        # Verificar se arquivo existe
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(file_path)

        # Verificar extensão
        if path.suffix.lower() != '.md':
            logger.error(f"Invalid file format: {file_path}")
            raise InvalidFileFormatError(file_path, '.md')

        # Ler conteúdo
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            self.file_path = file_path
            logger.info(f"Loaded markdown file: {file_path} ({len(self.content)} chars)")
            return self.content
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise ParsingError(f"Failed to read file: {e}", file_path=file_path)

    def extract_title(self) -> Optional[str]:
        """
        Extrai o título principal (primeiro # H1).

        Returns:
            Título ou None se não encontrado
        """
        match = re.search(r'^#\s+(.+)$', self.content, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            logger.debug(f"Extracted title: {title}")
            return title
        return None

    def extract_sections(self) -> Dict[str, str]:
        """
        Extrai seções do markdown (baseado em headers ##).

        Returns:
            Dicionário com título da seção e conteúdo
        """
        sections = {}

        # Split por headers ##
        parts = re.split(r'^##\s+(.+)$', self.content, flags=re.MULTILINE)

        # Primeira parte é o conteúdo antes do primeiro ##
        if len(parts) > 1:
            # Pares: título, conteúdo, título, conteúdo...
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    section_title = parts[i].strip()
                    section_content = parts[i + 1].strip()
                    sections[section_title] = section_content

        logger.debug(f"Extracted {len(sections)} sections: {list(sections.keys())}")
        return sections

    def extract_lists(self) -> List[str]:
        """
        Extrai todas as listas (itens que começam com -, *, ou números).

        Returns:
            Lista de itens
        """
        items = []

        # Itens com - ou *
        bullet_items = re.findall(r'^\s*[-*]\s+(.+)$', self.content, re.MULTILINE)
        items.extend(bullet_items)

        # Itens numerados
        numbered_items = re.findall(r'^\s*\d+\.\s+(.+)$', self.content, re.MULTILINE)
        items.extend(numbered_items)

        logger.debug(f"Extracted {len(items)} list items")
        return items

    def identify_keywords(self) -> Dict[str, List[str]]:
        """
        Identifica palavras-chave relevantes para processos.

        Returns:
            Dicionário com tipo de keyword e lista de matches
        """
        keywords = {
            'responsaveis': [],
            'decisoes': [],
            'condicoes': [],
            'eventos': []
        }

        # Padrões para identificar responsáveis
        # Ex: "(Gerente)", "Responsável: João", "Executor: Maria"
        responsaveis = re.findall(
            r'\(([A-Z][^)]+)\)|(?:Responsável|Executor|Ator):\s*([^\n]+)',
            self.content,
            re.IGNORECASE
        )
        for match in responsaveis:
            resp = match[0] or match[1]
            if resp.strip():
                keywords['responsaveis'].append(resp.strip())

        # Padrões para decisões
        # Ex: "Decisão:", "Se...", "Caso..."
        decisoes = re.findall(
            r'(?:Decisão|Decision|Gateway):\s*([^\n]+)|^(?:Se|Caso|If)\s+([^\n]+)',
            self.content,
            re.MULTILINE | re.IGNORECASE
        )
        for match in decisoes:
            dec = match[0] or match[1]
            if dec.strip():
                keywords['decisoes'].append(dec.strip())

        # Padrões para condições
        # Ex: "Se sim:", "Se aprovado:", "Caso contrário:"
        condicoes = re.findall(
            r'(?:Se|Caso|If)\s+([^:]+):|(?:então|then|otherwise):\s*([^\n]+)',
            self.content,
            re.IGNORECASE
        )
        for match in condicoes:
            cond = match[0] or match[1]
            if cond.strip():
                keywords['condicoes'].append(cond.strip())

        # Padrões para eventos
        # Ex: "Início:", "Fim:", "Finalização:"
        eventos = re.findall(
            r'(?:Início|Start|Começo|Begin|Fim|End|Finalização|Término):\s*([^\n]+)',
            self.content,
            re.IGNORECASE
        )
        for match in eventos:
            if match.strip():
                keywords['eventos'].append(match.strip())

        logger.debug(f"Identified keywords: {[(k, len(v)) for k, v in keywords.items()]}")
        return keywords

    def get_statistics(self) -> Dict[str, int]:
        """
        Retorna estatísticas sobre o conteúdo.

        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'total_chars': len(self.content),
            'total_lines': len(self.content.splitlines()),
            'total_words': len(self.content.split()),
            'num_headers_h1': len(re.findall(r'^#\s+', self.content, re.MULTILINE)),
            'num_headers_h2': len(re.findall(r'^##\s+', self.content, re.MULTILINE)),
            'num_headers_h3': len(re.findall(r'^###\s+', self.content, re.MULTILINE)),
            'num_bullet_points': len(re.findall(r'^\s*[-*]\s+', self.content, re.MULTILINE)),
            'num_numbered_items': len(re.findall(r'^\s*\d+\.\s+', self.content, re.MULTILINE)),
        }
        return stats

    def preprocess_for_llm(self) -> str:
        """
        Pré-processa o markdown para otimizar a extração via LLM.

        - Remove excesso de espaços em branco
        - Normaliza quebras de linha
        - Remove comentários HTML
        - Mantém estrutura importante

        Returns:
            Conteúdo pré-processado
        """
        processed = self.content

        # Remover comentários HTML
        processed = re.sub(r'<!--.*?-->', '', processed, flags=re.DOTALL)

        # Normalizar múltiplas linhas vazias para uma única
        processed = re.sub(r'\n{3,}', '\n\n', processed)

        # Remover espaços em branco no final das linhas
        processed = '\n'.join(line.rstrip() for line in processed.splitlines())

        # Remover espaços múltiplos (mas manter indentação)
        processed = re.sub(r'[ \t]{2,}', ' ', processed)

        logger.debug(f"Preprocessed content: {len(self.content)} -> {len(processed)} chars")
        return processed.strip()

    def parse(self, file_path: str) -> Tuple[str, Dict[str, any]]:
        """
        Pipeline completo de parsing.

        Args:
            file_path: Caminho para o arquivo markdown

        Returns:
            Tupla (conteúdo pré-processado, metadados extraídos)
        """
        # Carregar arquivo
        self.load_file(file_path)

        # Extrair metadados
        metadata = {
            'title': self.extract_title(),
            'sections': self.extract_sections(),
            'lists': self.extract_lists(),
            'keywords': self.identify_keywords(),
            'statistics': self.get_statistics(),
            'file_path': file_path
        }

        # Pré-processar para LLM
        processed_content = self.preprocess_for_llm()

        logger.info(f"Parsing complete: {metadata['title'] or 'Untitled'}")
        return processed_content, metadata


def parse_markdown_file(file_path: str) -> Tuple[str, Dict[str, any]]:
    """
    Função utilitária para fazer parsing de um arquivo markdown.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        Tupla (conteúdo processado, metadados)
    """
    parser = MarkdownParser()
    return parser.parse(file_path)
