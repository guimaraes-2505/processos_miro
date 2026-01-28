"""
Extrator usando Claude Code (modo interativo).
Elimina necessidade de API key do Anthropic.
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional

from src.models.process_model import Process, ProcessExtractionResult
from src.utils.exceptions import LLMExtractionError
from src.utils.logger import get_logger
from rich.console import Console
from rich.panel import Panel

logger = get_logger()
console = Console()


class ClaudeCodeExtractor:
    """
    Extrator interativo usando Claude Code.
    Permite usar Claude.ai ou este ambiente ao invés da API paga.
    """

    def __init__(self):
        self.prompt_file = Path("data/intermediate/extraction_prompt.txt")
        self.response_file = Path("data/intermediate/extraction_response.json")

    def extract_interactive(
        self,
        markdown_content: str,
        metadata: Optional[Dict] = None
    ) -> ProcessExtractionResult:
        """
        Extrai processo usando modo interativo.

        Workflow:
        1. Prepara prompt
        2. Salva em arquivo
        3. Exibe instruções
        4. Aguarda usuário colar resposta
        5. Valida e retorna

        Args:
            markdown_content: Conteúdo markdown pré-processado
            metadata: Metadados opcionais sobre a transcrição

        Returns:
            ProcessExtractionResult com processo extraído

        Raises:
            LLMExtractionError: Se falhar ao extrair ou parsear resposta
        """
        logger.info("Starting interactive extraction with Claude Code...")

        # 1. Preparar prompt (usar template existente)
        from src.parsers.llm_extractor import EXTRACTION_PROMPT_TEMPLATE
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(markdown_content=markdown_content)

        # 2. Salvar prompt
        self.prompt_file.parent.mkdir(parents=True, exist_ok=True)
        self.prompt_file.write_text(prompt, encoding='utf-8')
        logger.info(f"Prompt saved to: {self.prompt_file}")

        # 3. Limpar resposta anterior
        if self.response_file.exists():
            self.response_file.unlink()
            logger.debug("Cleaned previous response file")

        # 4. Exibir instruções
        self._show_instructions()

        # 5. Aguardar resposta
        self._wait_for_response()

        # 6. Ler e validar
        process = self._parse_response()

        # 7. Retornar resultado
        result = ProcessExtractionResult(
            process=process,
            source_file=metadata.get('file_path') if metadata else None,
            llm_model="claude-code-interactive",
            warnings=[]
        )

        logger.info(f"Interactive extraction completed: {process.name}")
        return result

    def _show_instructions(self):
        """Exibe instruções formatadas para o usuário."""
        instructions = f"""
[bold cyan]🤖 EXTRAÇÃO DE PROCESSO - Modo Claude Code Interativo[/bold cyan]

O prompt foi preparado e salvo em:
📄 [yellow]{self.prompt_file}[/yellow]

[bold]OPÇÃO 1 - Usar este ambiente Claude Code:[/bold]
1. Abra o arquivo acima
2. Copie todo o conteúdo
3. Cole aqui em uma nova mensagem (ou use interface web)
4. Copie a resposta JSON

[bold]OPÇÃO 2 - Usar Claude.ai (chat web):[/bold]
1. Abra [link]https://claude.ai[/link]
2. Cole o conteúdo do arquivo [yellow]extraction_prompt.txt[/yellow]
3. Copie a resposta JSON completa

[bold]OPÇÃO 3 - Linha de comando (se tiver Claude CLI):[/bold]
[green]cat {self.prompt_file} | claude > {self.response_file}[/green]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[bold yellow]IMPORTANTE:[/bold yellow]
Depois de obter a resposta JSON, salve-a em:
📄 [yellow]{self.response_file}[/yellow]

[dim]O sistema está aguardando este arquivo aparecer...[/dim]
"""
        console.print(Panel(instructions, border_style="cyan", title="🤖 Modo Interativo"))

    def _wait_for_response(self):
        """Aguarda arquivo de resposta ser criado."""
        console.print("\n[yellow]⏳ Aguardando resposta...[/yellow]")
        console.print(f"   Verificando: [cyan]{self.response_file}[/cyan]")
        console.print("   [dim](Pressione Ctrl+C para cancelar)[/dim]\n")

        try:
            max_wait = 600  # 10 minutos
            elapsed = 0
            check_interval = 2  # segundos

            while not self.response_file.exists():
                time.sleep(check_interval)
                elapsed += check_interval

                if elapsed % 30 == 0:  # A cada 30 segundos
                    console.print(f"   [dim]Aguardando há {elapsed}s...[/dim]")

                if elapsed >= max_wait:
                    raise LLMExtractionError(
                        f"Timeout: resposta não recebida após {max_wait}s"
                    )

            console.print("[green]✓ Resposta recebida![/green]\n")
            logger.info("Response file detected")

        except KeyboardInterrupt:
            console.print("\n[red]✗ Cancelado pelo usuário[/red]")
            logger.warning("Extraction cancelled by user")
            raise LLMExtractionError("Extraction cancelled by user")

    def _parse_response(self) -> Process:
        """Lê e valida resposta JSON."""
        logger.info(f"Parsing response from {self.response_file}")

        try:
            # Ler arquivo
            response_text = self.response_file.read_text(encoding='utf-8').strip()

            if not response_text:
                raise LLMExtractionError("Response file is empty")

            # Parse JSON
            try:
                process_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                logger.error(f"Response preview: {response_text[:200]}...")
                raise LLMExtractionError(
                    f"Resposta não é JSON válido: {e}\n"
                    f"Verifique se copiou apenas o JSON, sem texto adicional."
                )

            # Criar modelo Process
            try:
                process = Process(**process_data)
            except Exception as e:
                logger.error(f"Failed to create Process model: {e}")
                logger.error(f"Data: {process_data}")
                raise LLMExtractionError(
                    f"Erro ao criar modelo de processo: {e}\n"
                    f"Verifique se a estrutura JSON está correta."
                )

            logger.info(f"Process extracted successfully: {process.name}")
            logger.info(f"  - {len(process.elements)} elements")
            logger.info(f"  - {len(process.flows)} flows")
            logger.info(f"  - {len(process.actors)} actors")

            return process

        except LLMExtractionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            raise LLMExtractionError(f"Erro inesperado ao processar resposta: {e}")


def extract_process_interactive(
    markdown_content: str,
    metadata: Optional[Dict] = None
) -> ProcessExtractionResult:
    """
    Função utilitária para extrair processo usando modo interativo.

    Args:
        markdown_content: Conteúdo markdown
        metadata: Metadados opcionais

    Returns:
        ProcessExtractionResult
    """
    extractor = ClaudeCodeExtractor()
    return extractor.extract_interactive(markdown_content, metadata)
