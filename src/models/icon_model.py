"""
Modelos de dados para a biblioteca de ícones BPMN.

Este módulo define as estruturas de dados para gerenciar ícones customizados
utilizados na representação visual de elementos BPMN.
"""

from typing import Dict, Optional, Literal
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class IconConfig(BaseModel):
    """
    Configuração de um único ícone.

    Attributes:
        file_path: Caminho relativo ao diretório base de ícones
        size: Tamanho do ícone em pixels (opcional)
        description: Descrição do ícone (opcional)
    """

    file_path: str = Field(..., description="Caminho relativo do arquivo SVG")
    size: Optional[int] = Field(24, description="Tamanho do ícone em pixels")
    description: Optional[str] = Field(None, description="Descrição do ícone")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Valida formato do caminho do arquivo."""
        if not v.endswith(".svg"):
            raise ValueError("Arquivo de ícone deve ser SVG (.svg)")
        return v


class IconLibraryConfig(BaseModel):
    """
    Configurações gerais da biblioteca de ícones.

    Attributes:
        base_path: Caminho base para os ícones
        mode: Modo de renderização (svg, emoji, hybrid)
        icon_size: Tamanho padrão dos ícones
        icon_sizes: Tamanhos específicos por tipo
        icon_position: Posicionamento por tipo
        fallback_strategy: Estratégia de fallback
    """

    base_path: str = Field(default="data/icons", description="Caminho base dos ícones")
    mode: Literal["svg", "emoji", "hybrid"] = Field(
        default="svg", description="Modo de renderização"
    )
    icon_size: int = Field(default=24, description="Tamanho padrão em pixels")
    icon_sizes: Dict[str, int] = Field(
        default_factory=lambda: {"task": 20, "event": 16, "gateway": 18},
        description="Tamanhos específicos por tipo",
    )
    icon_position: Dict[str, str] = Field(
        default_factory=lambda: {
            "task": "left",
            "event": "inside",
            "gateway": "center",
        },
        description="Posicionamento por tipo",
    )
    fallback_strategy: Literal["none", "emoji", "text", "default_icon"] = Field(
        default="none", description="Estratégia de fallback"
    )


class IconLibrary(BaseModel):
    """
    Biblioteca completa de ícones BPMN.

    Esta classe mantém o mapeamento entre tipos BPMN e seus respectivos
    arquivos de ícones SVG.

    Attributes:
        tasks: Mapeamento de tipos de tarefas → caminhos de ícones
        events: Mapeamento de tipos de eventos → caminhos de ícones
        gateways: Mapeamento de tipos de gateways → caminhos de ícones
        config: Configurações gerais da biblioteca
    """

    tasks: Dict[str, str] = Field(
        default_factory=dict, description="Ícones de tarefas"
    )
    events: Dict[str, str] = Field(
        default_factory=dict, description="Ícones de eventos"
    )
    gateways: Dict[str, str] = Field(
        default_factory=dict, description="Ícones de gateways"
    )
    config: IconLibraryConfig = Field(
        default_factory=IconLibraryConfig, description="Configurações"
    )

    def get_icon_path(
        self, element_type: str, bpmn_type: str
    ) -> Optional[Path]:
        """
        Resolve o caminho do arquivo de ícone baseado no tipo BPMN.

        Args:
            element_type: Tipo do elemento ('task', 'event', 'gateway', 'annotation')
            bpmn_type: Tipo BPMN específico (ex: 'user_task', 'start_event')

        Returns:
            Path absoluto do arquivo SVG ou None se não encontrado

        Examples:
            >>> library.get_icon_path('task', 'user_task')
            Path('data/icons/tasks/user-task.svg')
        """
        # Determina o dicionário correto baseado no tipo de elemento
        if element_type == "task" or bpmn_type in self.tasks:
            icon_map = self.tasks
        elif element_type == "event" or bpmn_type in self.events:
            icon_map = self.events
        elif element_type == "gateway" or bpmn_type in self.gateways:
            icon_map = self.gateways
        else:
            return None

        # Busca o caminho do ícone
        relative_path = icon_map.get(bpmn_type)
        if not relative_path:
            # Tenta fallback para tipo genérico
            fallback_type = element_type if element_type != "annotation" else None
            if fallback_type:
                relative_path = icon_map.get(fallback_type)

        if relative_path:
            base = Path(self.config.base_path)
            return base / relative_path

        return None

    def get_icon_size(self, element_type: str) -> int:
        """
        Retorna o tamanho apropriado para o ícone baseado no tipo.

        Args:
            element_type: Tipo do elemento ('task', 'event', 'gateway')

        Returns:
            Tamanho em pixels
        """
        return self.config.icon_sizes.get(element_type, self.config.icon_size)

    def get_icon_position(self, element_type: str) -> str:
        """
        Retorna o posicionamento apropriado para o ícone.

        Args:
            element_type: Tipo do elemento ('task', 'event', 'gateway')

        Returns:
            Posição ('left', 'inside', 'center')
        """
        return self.config.icon_position.get(element_type, "left")

    def has_icon(self, element_type: str, bpmn_type: str) -> bool:
        """
        Verifica se existe um ícone para o tipo especificado.

        Args:
            element_type: Tipo do elemento
            bpmn_type: Tipo BPMN específico

        Returns:
            True se o ícone existe
        """
        icon_path = self.get_icon_path(element_type, bpmn_type)
        return icon_path is not None and icon_path.exists()


class TypeMapping(BaseModel):
    """
    Mapeamento de metadata para tipos BPMN.

    Usado pelo parser para identificar o tipo BPMN correto
    baseado nos valores de metadata dos elementos.
    """

    event_type: Dict[str, str] = Field(
        default_factory=lambda: {
            "start": "start_event",
            "end": "end_event",
            "timer": "timer_event",
            "message": "message_event",
            "error": "error_event",
        }
    )
    gateway_type: Dict[str, str] = Field(
        default_factory=lambda: {
            "exclusive": "exclusive_gateway",
            "inclusive": "inclusive_gateway",
            "parallel": "parallel_gateway",
            "event_based": "event_based_gateway",
        }
    )
    task_type: Dict[str, str] = Field(
        default_factory=lambda: {
            "user": "user_task",
            "manual": "manual_task",
            "service": "service_task",
            "script": "script_task",
            "send": "send_task",
            "receive": "receive_task",
        }
    )

    def resolve_bpmn_type(
        self, element_type: str, metadata: Dict
    ) -> Optional[str]:
        """
        Resolve o tipo BPMN baseado no tipo de elemento e metadata.

        Args:
            element_type: Tipo base do elemento ('task', 'event', 'gateway')
            metadata: Dicionário de metadata do elemento

        Returns:
            Tipo BPMN específico ou None

        Examples:
            >>> mapping = TypeMapping()
            >>> mapping.resolve_bpmn_type('task', {'task_type': 'user'})
            'user_task'
        """
        if element_type == "task":
            task_type = metadata.get("task_type", "user")
            return self.task_type.get(task_type, "user_task")
        elif element_type == "event":
            event_type = metadata.get("event_type", "start")
            return self.event_type.get(event_type, "start_event")
        elif element_type == "gateway":
            gateway_type = metadata.get("gateway_type", "exclusive")
            return self.gateway_type.get(gateway_type, "exclusive_gateway")
        return None
