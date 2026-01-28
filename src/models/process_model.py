"""
Modelo intermediário de processo.
Formato neutro entre parsing e visualização (Miro/ClickUp).
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ProcessElement(BaseModel):
    """
    Elemento individual de um processo (tarefa, decisão, evento, anotação).
    """
    id: str = Field(..., description="Identificador único do elemento")
    type: Literal['task', 'gateway', 'event', 'annotation'] = Field(
        ...,
        description="Tipo do elemento"
    )
    name: str = Field(..., description="Nome/título do elemento")
    description: Optional[str] = Field(None, description="Descrição detalhada")
    actor: Optional[str] = Field(None, description="Responsável pela execução (para swimlane)")

    # Campos hierárquicos (novos)
    hierarchy_level: Optional[Literal['processo', 'subprocesso', 'atividade', 'tarefa']] = Field(
        None,
        description="Nível na hierarquia BPM"
    )
    parent_id: Optional[str] = Field(
        None,
        description="ID do elemento pai na hierarquia"
    )
    numbering: Optional[str] = Field(
        None,
        description="Numeração hierárquica (ex: 1.2.3)"
    )

    # Campos de documentação (novos)
    documentation_ref: Optional[str] = Field(
        None,
        description="Referência ao documento (ex: POP-001, IT-001)"
    )
    inputs: List[str] = Field(
        default_factory=list,
        description="Entradas necessárias para a atividade"
    )
    outputs: List[str] = Field(
        default_factory=list,
        description="Saídas/entregas da atividade"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Ferramentas/sistemas utilizados"
    )

    # Campos de integração (novos)
    miro_item_id: Optional[str] = Field(
        None,
        description="ID do elemento no Miro"
    )
    clickup_task_id: Optional[str] = Field(
        None,
        description="ID da tarefa no ClickUp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais específicos do tipo"
    )

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Valida que o ID não está vazio."""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome não está vazio."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    def is_task(self) -> bool:
        """Verifica se é uma tarefa."""
        return self.type == 'task'

    def is_gateway(self) -> bool:
        """Verifica se é uma decisão."""
        return self.type == 'gateway'

    def is_event(self) -> bool:
        """Verifica se é um evento."""
        return self.type == 'event'

    def is_start_event(self) -> bool:
        """Verifica se é um evento de início."""
        return self.type == 'event' and self.metadata.get('event_type') == 'start'

    def is_end_event(self) -> bool:
        """Verifica se é um evento de fim."""
        return self.type == 'event' and self.metadata.get('event_type') == 'end'

    def is_annotation(self) -> bool:
        """Verifica se é uma anotação."""
        return self.type == 'annotation'


class ProcessFlow(BaseModel):
    """
    Fluxo/conexão entre elementos do processo.
    """
    from_element: str = Field(..., description="ID do elemento de origem")
    to_element: str = Field(..., description="ID do elemento de destino")
    condition: Optional[str] = Field(None, description="Condição para seguir este fluxo (para gateways)")

    @field_validator('from_element', 'to_element')
    @classmethod
    def validate_element_ids(cls, v: str) -> str:
        """Valida que os IDs não estão vazios."""
        if not v or not v.strip():
            raise ValueError("Element ID cannot be empty")
        return v.strip()


class Process(BaseModel):
    """
    Modelo completo de um processo de negócio.
    """
    name: str = Field(..., description="Nome do processo")
    description: str = Field(default="", description="Descrição do processo")
    elements: List[ProcessElement] = Field(
        default_factory=list,
        description="Lista de elementos do processo"
    )
    flows: List[ProcessFlow] = Field(
        default_factory=list,
        description="Lista de fluxos entre elementos"
    )
    actors: List[str] = Field(
        default_factory=list,
        description="Lista de atores/responsáveis (para swimlanes)"
    )

    # Campos de identificação (novos)
    process_id: Optional[str] = Field(
        None,
        description="Código do processo (ex: PROC-MKT-001)"
    )
    level: Literal['processo', 'subprocesso'] = Field(
        default='processo',
        description="Nível na hierarquia"
    )

    # Campos hierárquicos (novos)
    macroprocess_id: Optional[str] = Field(
        None,
        description="ID do macroprocesso pai"
    )
    parent_process_id: Optional[str] = Field(
        None,
        description="ID do processo pai (para subprocessos)"
    )
    owner: Optional[str] = Field(
        None,
        description="Dono/responsável pelo processo"
    )

    # Campos de documentação (novos)
    pop_code: Optional[str] = Field(
        None,
        description="Código do POP relacionado (ex: POP-001)"
    )
    documentation_refs: Dict[str, str] = Field(
        default_factory=dict,
        description="Referências de documentação (tipo: código)"
    )

    # Campos de integração (novos)
    miro_board_id: Optional[str] = Field(
        None,
        description="ID do board no Miro"
    )
    miro_board_url: Optional[str] = Field(
        None,
        description="URL do board no Miro"
    )
    clickup_folder_id: Optional[str] = Field(
        None,
        description="ID da pasta no ClickUp"
    )
    clickup_list_id: Optional[str] = Field(
        None,
        description="ID da lista no ClickUp"
    )

    # Campos SIPOC (novos)
    suppliers: List[str] = Field(
        default_factory=list,
        description="Fornecedores (SIPOC)"
    )
    inputs: List[str] = Field(
        default_factory=list,
        description="Entradas (SIPOC)"
    )
    outputs: List[str] = Field(
        default_factory=list,
        description="Saídas (SIPOC)"
    )
    customers: List[str] = Field(
        default_factory=list,
        description="Clientes (SIPOC)"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais do processo"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome não está vazio."""
        if not v or not v.strip():
            raise ValueError("Process name cannot be empty")
        return v.strip()

    def get_element(self, element_id: str) -> Optional[ProcessElement]:
        """
        Busca um elemento pelo ID.

        Args:
            element_id: ID do elemento

        Returns:
            ProcessElement ou None se não encontrado
        """
        for element in self.elements:
            if element.id == element_id:
                return element
        return None

    def get_start_events(self) -> List[ProcessElement]:
        """Retorna todos os eventos de início."""
        return [e for e in self.elements if e.is_start_event()]

    def get_end_events(self) -> List[ProcessElement]:
        """Retorna todos os eventos de fim."""
        return [e for e in self.elements if e.is_end_event()]

    def get_tasks(self) -> List[ProcessElement]:
        """Retorna todas as tarefas."""
        return [e for e in self.elements if e.is_task()]

    def get_gateways(self) -> List[ProcessElement]:
        """Retorna todas as decisões."""
        return [e for e in self.elements if e.is_gateway()]

    def get_outgoing_flows(self, element_id: str) -> List[ProcessFlow]:
        """
        Retorna todos os fluxos que saem de um elemento.

        Args:
            element_id: ID do elemento

        Returns:
            Lista de fluxos de saída
        """
        return [f for f in self.flows if f.from_element == element_id]

    def get_incoming_flows(self, element_id: str) -> List[ProcessFlow]:
        """
        Retorna todos os fluxos que chegam em um elemento.

        Args:
            element_id: ID do elemento

        Returns:
            Lista de fluxos de entrada
        """
        return [f for f in self.flows if f.to_element == element_id]

    def get_elements_by_actor(self, actor: str) -> List[ProcessElement]:
        """
        Retorna todos os elementos de um ator específico.

        Args:
            actor: Nome do ator

        Returns:
            Lista de elementos
        """
        return [e for e in self.elements if e.actor == actor]

    def is_subprocess(self) -> bool:
        """Verifica se é um subprocesso."""
        return self.level == 'subprocesso'

    def has_miro_integration(self) -> bool:
        """Verifica se tem integração com Miro."""
        return self.miro_board_id is not None

    def has_clickup_integration(self) -> bool:
        """Verifica se tem integração com ClickUp."""
        return self.clickup_folder_id is not None or self.clickup_list_id is not None

    def get_numbered_elements(self) -> List[ProcessElement]:
        """Retorna elementos com numeração hierárquica."""
        return [e for e in self.elements if e.numbering is not None]

    def get_elements_by_hierarchy_level(
        self,
        level: Literal['processo', 'subprocesso', 'atividade', 'tarefa']
    ) -> List[ProcessElement]:
        """
        Retorna elementos de um nível hierárquico específico.

        Args:
            level: Nível desejado

        Returns:
            Lista de elementos
        """
        return [e for e in self.elements if e.hierarchy_level == level]

    def get_sipoc_summary(self) -> Dict[str, List[str]]:
        """
        Retorna resumo SIPOC do processo.

        Returns:
            Dict com suppliers, inputs, process (nomes das tarefas), outputs, customers
        """
        return {
            'suppliers': self.suppliers,
            'inputs': self.inputs,
            'process': [e.name for e in self.get_tasks()],
            'outputs': self.outputs,
            'customers': self.customers
        }

    def assign_numbering(self):
        """
        Atribui numeração hierárquica aos elementos baseado na ordem e swimlane.
        Elementos são numerados por swimlane: 1.1, 1.2 (swimlane 1), 2.1, 2.2 (swimlane 2).
        """
        if not self.actors:
            # Sem swimlanes, numerar sequencialmente
            counter = 1
            for element in self.elements:
                if element.is_task():
                    element.numbering = str(counter)
                    counter += 1
            return

        # Com swimlanes, numerar por ator
        for actor_idx, actor in enumerate(self.actors, start=1):
            actor_elements = self.get_elements_by_actor(actor)
            task_counter = 1
            for element in actor_elements:
                if element.is_task():
                    element.numbering = f"{actor_idx}.{task_counter}"
                    task_counter += 1


class ProcessExtractionResult(BaseModel):
    """
    Resultado da extração de processo de uma transcrição.
    Inclui o processo e metadados sobre a extração.
    """
    process: Process = Field(..., description="Processo extraído")
    source_file: Optional[str] = Field(None, description="Arquivo fonte da transcrição")
    extraction_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp da extração"
    )
    llm_model: Optional[str] = Field(None, description="Modelo LLM usado na extração")
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Score de confiança da extração (0-1)"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Avisos durante a extração"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProcessIntegrationMetadata(BaseModel):
    """
    Metadados de integração entre Miro e ClickUp.
    Mantém referências cruzadas para sincronização.
    """
    process_id: str = Field(..., description="ID do processo")
    process_name: str = Field(..., description="Nome do processo")

    # Referências Miro
    miro_board_id: Optional[str] = Field(None, description="ID do board no Miro")
    miro_board_url: Optional[str] = Field(None, description="URL do board no Miro")
    miro_element_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapeamento element_id -> miro_item_id"
    )

    # Referências ClickUp
    clickup_space_id: Optional[str] = Field(None, description="ID do space no ClickUp")
    clickup_folder_id: Optional[str] = Field(None, description="ID da folder no ClickUp")
    clickup_list_id: Optional[str] = Field(None, description="ID da list no ClickUp")
    clickup_task_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapeamento element_id -> clickup_task_id"
    )

    # Documentação
    pop_code: Optional[str] = Field(None, description="Código do POP")
    it_codes: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapeamento element_id -> it_code"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de criação"
    )
    last_synced_at: Optional[datetime] = Field(
        None,
        description="Última sincronização"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    def get_miro_item_id(self, element_id: str) -> Optional[str]:
        """Busca ID do item no Miro."""
        return self.miro_element_ids.get(element_id)

    def get_clickup_task_id(self, element_id: str) -> Optional[str]:
        """Busca ID da tarefa no ClickUp."""
        return self.clickup_task_ids.get(element_id)

    def add_miro_mapping(self, element_id: str, miro_item_id: str):
        """Adiciona mapeamento de elemento para Miro."""
        self.miro_element_ids[element_id] = miro_item_id

    def add_clickup_mapping(self, element_id: str, task_id: str):
        """Adiciona mapeamento de elemento para ClickUp."""
        self.clickup_task_ids[element_id] = task_id

    def mark_synced(self):
        """Marca como sincronizado agora."""
        self.last_synced_at = datetime.now()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
