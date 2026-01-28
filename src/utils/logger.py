"""
Sistema de logging configurado com Loguru.
Fornece logging estruturado para console e arquivo.
"""

import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logger(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    log_to_console: bool = True,
    log_to_file: bool = True,
) -> logger:
    """
    Configura o logger do sistema.

    Args:
        log_file: Caminho para o arquivo de log (padrão: data/output/process_mapper.log)
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Se deve fazer log no console
        log_to_file: Se deve fazer log em arquivo

    Returns:
        Logger configurado
    """
    # Remove handlers padrão
    logger.remove()

    # Console output (colorido e formatado)
    if log_to_console:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )

    # File output (detalhado com todas as informações)
    if log_to_file:
        if log_file is None:
            log_file = "data/output/process_mapper.log"

        # Garantir que o diretório existe
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",  # Arquivo sempre em DEBUG para auditoria completa
            rotation="10 MB",  # Rotacionar quando atingir 10MB
            retention="30 days",  # Manter logs por 30 dias
            compression="zip",  # Comprimir logs antigos
            enqueue=True,  # Thread-safe
            backtrace=True,  # Incluir traceback completo em erros
            diagnose=True,  # Informações de diagnóstico em exceções
        )

    return logger


def get_logger():
    """
    Retorna a instância do logger.
    Útil para importar em outros módulos.

    Usage:
        from utils.logger import get_logger
        logger = get_logger()
        logger.info("Mensagem")
    """
    return logger


# Configuração padrão ao importar o módulo
# Pode ser reconfigurado posteriormente chamando setup_logger()
_default_logger = setup_logger()


# Exportar logger configurado
__all__ = ['setup_logger', 'get_logger', 'logger']
