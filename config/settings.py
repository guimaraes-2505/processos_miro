"""
Configurações centralizadas do sistema.
Carrega variáveis de ambiente usando Pydantic Settings.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações do sistema de mapeamento de processos.
    Carrega valores do arquivo .env ou variáveis de ambiente.
    """

    # ========== API Keys ==========
    # Claude API (OPCIONAL - só necessário se EXTRACTION_MODE=api)
    ANTHROPIC_API_KEY: Optional[str] = Field(
        None,
        description="API key do Claude (opcional - use EXTRACTION_MODE=claude-code se não tiver)"
    )

    # Miro (OBRIGATÓRIO)
    MIRO_API_TOKEN: str = Field(
        ...,
        description="Token de acesso da API do Miro"
    )

    # ClickUp (OPCIONAL - para Fase 6)
    CLICKUP_API_TOKEN: Optional[str] = Field(
        None,
        description="Token de acesso da API do ClickUp (opcional)"
    )

    CLICKUP_TEAM_ID: Optional[str] = Field(
        None,
        description="ID do time/workspace no ClickUp (opcional)"
    )

    CLICKUP_SPACE_ID: Optional[str] = Field(
        None,
        description="ID do espaço no ClickUp (opcional)"
    )

    CLICKUP_DEFAULT_FOLDER_ID: Optional[str] = Field(
        None,
        description="ID da pasta padrao no ClickUp (opcional)"
    )

    CLICKUP_SYNC_ENABLED: bool = Field(
        default=False,
        description="Habilitar sincronizacao automatica com ClickUp"
    )

    CLICKUP_IT_CUSTOM_FIELD_ID: Optional[str] = Field(
        None,
        description="ID do campo customizado para codigo IT no ClickUp"
    )

    CLICKUP_MIRO_LINK_FIELD_ID: Optional[str] = Field(
        None,
        description="ID do campo customizado para link do Miro no ClickUp"
    )

    CLICKUP_POP_REFERENCE_FIELD_ID: Optional[str] = Field(
        None,
        description="ID do campo customizado para referencia POP no ClickUp"
    )

    # ========== MCP Configuration ==========
    MCP_MIRO_CONFIG: str = Field(
        default="config/mcp_miro.json",
        description="Caminho para configuração do servidor MCP do Miro"
    )

    MCP_CLICKUP_CONFIG: str = Field(
        default="config/mcp_clickup.json",
        description="Caminho para configuração do servidor MCP do ClickUp"
    )

    # ========== LLM Settings ==========
    LLM_MODEL: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Modelo Claude a ser usado"
    )

    LLM_MAX_TOKENS: int = Field(
        default=8000,
        ge=1000,
        le=200000,
        description="Máximo de tokens na resposta do LLM"
    )

    LLM_TEMPERATURE: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Temperatura do LLM (0 = determinístico, 1 = criativo)"
    )

    # ========== Extraction Mode ==========
    EXTRACTION_MODE: str = Field(
        default="claude-code",
        description="Modo de extração: claude-code (grátis, interativo) | api (pago, automático) | manual (arquivo)"
    )

    @field_validator('EXTRACTION_MODE')
    @classmethod
    def validate_extraction_mode(cls, v: str) -> str:
        """Valida o modo de extração."""
        valid_modes = ['claude-code', 'api', 'manual']
        v_lower = v.lower()
        if v_lower not in valid_modes:
            raise ValueError(f"EXTRACTION_MODE must be one of {valid_modes}")
        return v_lower

    # ========== Layout Settings ==========
    SWIMLANE_HEIGHT: int = Field(
        default=200,
        ge=100,
        description="Altura de cada swimlane em pixels"
    )

    SWIMLANE_SPACING: int = Field(
        default=50,
        ge=10,
        description="Espaçamento entre swimlanes em pixels"
    )

    ELEMENT_SPACING_X: int = Field(
        default=150,
        ge=50,
        description="Espaçamento horizontal entre elementos em pixels"
    )

    ELEMENT_SPACING_Y: int = Field(
        default=100,
        ge=50,
        description="Espaçamento vertical entre elementos em pixels"
    )

    # ========== Miro Board Settings ==========
    MIRO_BOARD_WIDTH: int = Field(
        default=4000,
        ge=1000,
        description="Largura do board Miro em pixels"
    )

    MIRO_BOARD_HEIGHT: int = Field(
        default=3000,
        ge=1000,
        description="Altura do board Miro em pixels"
    )

    # ========== File Paths ==========
    INPUT_DIR: str = Field(
        default="data/input",
        description="Diretório para arquivos de entrada"
    )

    INTERMEDIATE_DIR: str = Field(
        default="data/intermediate",
        description="Diretório para arquivos intermediários (JSONs)"
    )

    OUTPUT_DIR: str = Field(
        default="data/output",
        description="Diretório para arquivos de saída (logs, etc)"
    )

    # ========== Logging ==========
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    LOG_TO_FILE: bool = Field(
        default=True,
        description="Se deve salvar logs em arquivo"
    )

    LOG_TO_CONSOLE: bool = Field(
        default=True,
        description="Se deve exibir logs no console"
    )

    # ========== Processing Options ==========
    MAX_FILE_SIZE_MB: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Tamanho máximo de arquivo de entrada em MB"
    )

    ENABLE_CACHE: bool = Field(
        default=True,
        description="Habilitar cache de resultados LLM"
    )

    # ========== Icon Settings ==========
    ICONS_ENABLED: bool = Field(
        default=True,
        description="Habilitar uso de ícones SVG customizados"
    )

    ICONS_YAML_PATH: str = Field(
        default="data/icons/icons.yaml",
        description="Caminho para o arquivo de configuração de ícones"
    )

    ICONS_MODE: str = Field(
        default="svg",
        description="Modo de renderização de ícones: svg | emoji | hybrid"
    )

    ICONS_DEFAULT_SIZE: int = Field(
        default=24,
        ge=12,
        le=64,
        description="Tamanho padrão dos ícones em pixels"
    )

    ICONS_FALLBACK_STRATEGY: str = Field(
        default="emoji",
        description="Estratégia de fallback quando ícone não encontrado: none | emoji | text"
    )

    ICON_BASE_URL: Optional[str] = Field(
        None,
        description="URL base para ícones SVG públicos (ex: https://raw.githubusercontent.com/user/repo/main/data/icons)"
    )

    @field_validator('ICONS_MODE')
    @classmethod
    def validate_icons_mode(cls, v: str) -> str:
        """Valida o modo de renderização de ícones."""
        valid_modes = ['svg', 'emoji', 'hybrid']
        v_lower = v.lower()
        if v_lower not in valid_modes:
            raise ValueError(f"ICONS_MODE must be one of {valid_modes}")
        return v_lower

    # Model configuration
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'  # Ignora variáveis extras no .env
    )

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valida o nível de log."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper

    def get_input_path(self) -> Path:
        """Retorna Path para diretório de entrada."""
        return Path(self.INPUT_DIR)

    def get_intermediate_path(self) -> Path:
        """Retorna Path para diretório intermediário."""
        return Path(self.INTERMEDIATE_DIR)

    def get_output_path(self) -> Path:
        """Retorna Path para diretório de saída."""
        return Path(self.OUTPUT_DIR)

    def ensure_directories(self):
        """Cria os diretórios necessários se não existirem."""
        self.get_input_path().mkdir(parents=True, exist_ok=True)
        self.get_intermediate_path().mkdir(parents=True, exist_ok=True)
        self.get_output_path().mkdir(parents=True, exist_ok=True)

    def get_log_file_path(self) -> Path:
        """Retorna caminho completo para o arquivo de log."""
        return self.get_output_path() / "process_mapper.log"

    def get_icons_yaml_path(self) -> Path:
        """Retorna Path para o arquivo de configuração de ícones."""
        return Path(self.ICONS_YAML_PATH)

    def is_icons_enabled(self) -> bool:
        """Verifica se ícones SVG estão habilitados."""
        return self.ICONS_ENABLED and self.get_icons_yaml_path().exists()

    def get_icon_url(self, relative_path: str) -> Optional[str]:
        """
        Retorna URL pública para um ícone SVG.

        Args:
            relative_path: Caminho relativo do ícone (ex: 'tasks/user-task.svg')

        Returns:
            URL pública completa ou None se ICON_BASE_URL não configurado
        """
        if not self.ICON_BASE_URL:
            return None
        base = self.ICON_BASE_URL.rstrip('/')
        return f"{base}/{relative_path}"


# Singleton: instância global de configurações
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Retorna a instância global de configurações.
    Cria uma nova se não existir.

    Returns:
        Instância de Settings

    Usage:
        from config.settings import get_settings
        settings = get_settings()
        print(settings.LLM_MODEL)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings


def reload_settings() -> Settings:
    """
    Força o reload das configurações.
    Útil para testes ou quando o .env é alterado.

    Returns:
        Nova instância de Settings
    """
    global _settings
    _settings = Settings()
    _settings.ensure_directories()
    return _settings
