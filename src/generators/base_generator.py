"""
Classe base abstrata para geradores de documentacao.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.models.process_model import Process, ProcessElement
from src.models.documentation_model import DocumentBase
from src.utils.logger import get_logger

logger = get_logger()


class DocumentGenerator(ABC):
    """
    Classe base abstrata para geradores de documentacao.
    Define interface comum para todos os geradores.
    """

    def __init__(self, template_path: Optional[str] = None):
        """
        Inicializa o gerador.

        Args:
            template_path: Caminho para template customizado (opcional)
        """
        self.template_path = template_path
        self._template_content: Optional[str] = None

    @property
    def default_template_path(self) -> str:
        """Retorna caminho do template padrao. Deve ser implementado."""
        raise NotImplementedError("Subclass must define default_template_path")

    def _load_template(self) -> str:
        """
        Carrega o template do arquivo.

        Returns:
            Conteudo do template
        """
        if self._template_content is not None:
            return self._template_content

        path = self.template_path or self.default_template_path
        template_file = Path(path)

        if not template_file.exists():
            logger.warning(f"Template nao encontrado: {path}")
            return self._get_fallback_template()

        self._template_content = template_file.read_text(encoding='utf-8')
        return self._template_content

    def _get_fallback_template(self) -> str:
        """
        Retorna template fallback quando arquivo nao existe.
        Deve ser implementado pelas subclasses.
        """
        return "# {title}\n\n{content}"

    @abstractmethod
    def generate(self, process: Process, **kwargs) -> DocumentBase:
        """
        Gera documento a partir de um processo.

        Args:
            process: Processo fonte
            **kwargs: Argumentos adicionais

        Returns:
            Documento gerado
        """
        pass

    @abstractmethod
    def to_markdown(self, document: DocumentBase) -> str:
        """
        Exporta documento para Markdown.

        Args:
            document: Documento a exportar

        Returns:
            Conteudo em Markdown
        """
        pass

    def to_html(self, document: DocumentBase) -> str:
        """
        Exporta documento para HTML.
        Implementacao padrao converte Markdown para HTML basico.

        Args:
            document: Documento a exportar

        Returns:
            Conteudo em HTML
        """
        markdown_content = self.to_markdown(document)
        # Conversao basica - pode ser melhorada com biblioteca markdown
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{document.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background-color: #f4f4f4; padding: 2px 5px; }}
    </style>
</head>
<body>
<pre>{markdown_content}</pre>
</body>
</html>"""
        return html

    def save_to_file(
        self,
        document: DocumentBase,
        output_path: str,
        format: str = 'markdown'
    ) -> str:
        """
        Salva documento em arquivo.

        Args:
            document: Documento a salvar
            output_path: Caminho de saida
            format: Formato (markdown, html)

        Returns:
            Caminho do arquivo salvo
        """
        if format == 'markdown':
            content = self.to_markdown(document)
            extension = '.md'
        elif format == 'html':
            content = self.to_html(document)
            extension = '.html'
        else:
            raise ValueError(f"Formato nao suportado: {format}")

        output_file = Path(output_path)
        if output_file.suffix != extension:
            output_file = output_file.with_suffix(extension)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding='utf-8')

        logger.info(f"Documento salvo: {output_file}")
        return str(output_file)

    def _number_elements(self, process: Process) -> Dict[str, str]:
        """
        Gera numeracao hierarquica para elementos do processo.

        Args:
            process: Processo a numerar

        Returns:
            Dict mapeando element_id -> numeracao
        """
        numbering_map: Dict[str, str] = {}

        if not process.actors:
            # Sem swimlanes, numerar sequencialmente
            counter = 1
            for element in process.elements:
                if element.is_task():
                    numbering_map[element.id] = str(counter)
                    counter += 1
        else:
            # Com swimlanes, numerar por ator
            for actor_idx, actor in enumerate(process.actors, start=1):
                actor_elements = process.get_elements_by_actor(actor)
                task_counter = 1
                for element in actor_elements:
                    if element.is_task():
                        numbering_map[element.id] = f"{actor_idx}.{task_counter}"
                        task_counter += 1

        return numbering_map

    def _extract_responsibilities(self, process: Process) -> List[Dict[str, Any]]:
        """
        Extrai responsabilidades dos atores do processo.

        Args:
            process: Processo fonte

        Returns:
            Lista de responsabilidades por ator
        """
        responsibilities = []

        for actor in process.actors:
            actor_elements = process.get_elements_by_actor(actor)
            tasks = [e.name for e in actor_elements if e.is_task()]

            responsibilities.append({
                'role': actor,
                'responsibilities': tasks
            })

        return responsibilities

    def _format_date(self, dt: datetime) -> str:
        """Formata data para exibicao."""
        return dt.strftime("%d/%m/%Y")

    def _format_datetime(self, dt: datetime) -> str:
        """Formata data e hora para exibicao."""
        return dt.strftime("%d/%m/%Y %H:%M")

    def _generate_code(self, prefix: str, sequence: int) -> str:
        """
        Gera codigo de documento.

        Args:
            prefix: Prefixo (POP, IT, CL)
            sequence: Numero sequencial

        Returns:
            Codigo formatado (ex: POP-001)
        """
        return f"{prefix}-{sequence:03d}"

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Renderiza template com contexto.
        Substitui placeholders {key} por valores do contexto.

        Args:
            template: Template string
            context: Dicionario de valores

        Returns:
            Template renderizado
        """
        result = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value) if value else "")
        return result
