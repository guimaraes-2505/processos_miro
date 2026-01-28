"""
Hierarquia de exceções customizadas para o sistema de mapeamento de processos.
"""

from typing import List, Optional


class ProcessMapperError(Exception):
    """Exceção base para todos os erros do sistema."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ParsingError(ProcessMapperError):
    """Erro ao fazer parsing do arquivo markdown."""

    def __init__(self, message: str, file_path: Optional[str] = None, line_number: Optional[int] = None):
        details = {}
        if file_path:
            details['file'] = file_path
        if line_number:
            details['line'] = line_number
        super().__init__(message, details)


class LLMExtractionError(ProcessMapperError):
    """Erro na extração de elementos via LLM."""

    def __init__(self, message: str, raw_response: Optional[str] = None, model: Optional[str] = None):
        details = {}
        if model:
            details['model'] = model
        super().__init__(message, details)
        self.raw_response = raw_response


class ValidationError(ProcessMapperError):
    """Erro de validação de processo."""

    def __init__(self, errors: List[str], process_name: Optional[str] = None):
        self.validation_errors = errors
        error_list = "\n  - ".join(errors)
        message = f"Validation failed with {len(errors)} error(s):\n  - {error_list}"
        details = {}
        if process_name:
            details['process'] = process_name
        super().__init__(message, details)


class BPMNConversionError(ProcessMapperError):
    """Erro ao converter para BPMN."""

    def __init__(self, message: str, element_id: Optional[str] = None):
        details = {}
        if element_id:
            details['element'] = element_id
        super().__init__(message, details)


class LayoutError(ProcessMapperError):
    """Erro no cálculo de layout."""

    def __init__(self, message: str, layout_type: Optional[str] = None):
        details = {}
        if layout_type:
            details['layout'] = layout_type
        super().__init__(message, details)


class MCPConnectionError(ProcessMapperError):
    """Erro de conexão com servidor MCP."""

    def __init__(self, message: str, server_name: Optional[str] = None):
        details = {}
        if server_name:
            details['server'] = server_name
        super().__init__(message, details)


class MiroAPIError(ProcessMapperError):
    """Erro na API do Miro."""

    def __init__(self, message: str, status_code: Optional[int] = None, board_id: Optional[str] = None):
        details = {}
        if status_code:
            details['status_code'] = status_code
        if board_id:
            details['board_id'] = board_id
        super().__init__(message, details)
        self.status_code = status_code


class ClickUpAPIError(ProcessMapperError):
    """Erro na API do ClickUp."""

    def __init__(self, message: str, status_code: Optional[int] = None, task_id: Optional[str] = None):
        details = {}
        if status_code:
            details['status_code'] = status_code
        if task_id:
            details['task_id'] = task_id
        super().__init__(message, details)
        self.status_code = status_code


class FileNotFoundError(ProcessMapperError):
    """Erro quando arquivo não é encontrado."""

    def __init__(self, file_path: str):
        super().__init__(f"File not found: {file_path}", {'file': file_path})


class InvalidFileFormatError(ProcessMapperError):
    """Erro quando formato de arquivo é inválido."""

    def __init__(self, file_path: str, expected_format: str):
        super().__init__(
            f"Invalid file format. Expected {expected_format}",
            {'file': file_path, 'expected': expected_format}
        )


class ConfigurationError(ProcessMapperError):
    """Erro de configuração do sistema."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        super().__init__(message, details)
