"""
Modelos de hierarquia de processos BPM.
Suporta Cadeia de Valor, Macroprocessos e SIPOC.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class SIPOCItem(BaseModel):
    """
    Item individual do SIPOC (Supplier, Input, Output ou Customer).
    """
    name: str = Field(..., description="Nome do item")
    description: Optional[str] = Field(None, description="Descricao detalhada")
    type: Optional[Literal['interno', 'externo']] = Field(
        None,
        description="Tipo do item (interno/externo) - usado para Suppliers e Customers"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("Nome do item SIPOC nao pode ser vazio")
        return v.strip()


class SIPOC(BaseModel):
    """
    Modelo SIPOC (Supplier, Input, Process, Output, Customer).
    Ferramenta central para definir e validar processos.
    """
    suppliers: List[SIPOCItem] = Field(
        default_factory=list,
        description="Fornecedores - quem fornece os insumos"
    )
    inputs: List[SIPOCItem] = Field(
        default_factory=list,
        description="Entradas - o que e necessario para iniciar"
    )
    process_steps: List[str] = Field(
        default_factory=list,
        description="Passos principais do processo (resumo)"
    )
    outputs: List[SIPOCItem] = Field(
        default_factory=list,
        description="Saidas - entregas geradas"
    )
    customers: List[SIPOCItem] = Field(
        default_factory=list,
        description="Clientes - quem recebe as entregas"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    def get_internal_suppliers(self) -> List[SIPOCItem]:
        """Retorna fornecedores internos."""
        return [s for s in self.suppliers if s.type == 'interno']

    def get_external_suppliers(self) -> List[SIPOCItem]:
        """Retorna fornecedores externos."""
        return [s for s in self.suppliers if s.type == 'externo']

    def get_internal_customers(self) -> List[SIPOCItem]:
        """Retorna clientes internos."""
        return [c for c in self.customers if c.type == 'interno']

    def get_external_customers(self) -> List[SIPOCItem]:
        """Retorna clientes externos."""
        return [c for c in self.customers if c.type == 'externo']

    def is_complete(self) -> bool:
        """Verifica se o SIPOC esta completo (todos os campos preenchidos)."""
        return (
            len(self.suppliers) > 0 and
            len(self.inputs) > 0 and
            len(self.process_steps) > 0 and
            len(self.outputs) > 0 and
            len(self.customers) > 0
        )


class Macroprocess(BaseModel):
    """
    Macroprocesso - nivel tatico da hierarquia.
    Agrupa processos relacionados com objetivo comum.
    """
    id: str = Field(..., description="Identificador unico (ex: MACRO-PRI-001)")
    name: str = Field(..., description="Nome do macroprocesso")
    description: str = Field(default="", description="Descricao do macroprocesso")
    type: Literal['primario', 'apoio', 'gestao'] = Field(
        ...,
        description="Tipo: primario (core business), apoio (suporte), gestao (controle)"
    )
    objective: str = Field(default="", description="Objetivo principal do macroprocesso")
    owner: Optional[str] = Field(None, description="Dono/responsavel pelo macroprocesso")
    value_chain_id: Optional[str] = Field(
        None,
        description="ID da Cadeia de Valor pai"
    )
    processes: List[str] = Field(
        default_factory=list,
        description="IDs dos processos filhos"
    )
    sipoc: Optional[SIPOC] = Field(None, description="SIPOC do macroprocesso")
    indicators: List[str] = Field(
        default_factory=list,
        description="Indicadores de desempenho"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Valida que o ID nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("ID do macroprocesso nao pode ser vazio")
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("Nome do macroprocesso nao pode ser vazio")
        return v.strip()

    def is_primary(self) -> bool:
        """Verifica se e macroprocesso primario."""
        return self.type == 'primario'

    def is_support(self) -> bool:
        """Verifica se e macroprocesso de apoio."""
        return self.type == 'apoio'

    def is_management(self) -> bool:
        """Verifica se e macroprocesso de gestao."""
        return self.type == 'gestao'

    def get_type_display(self) -> str:
        """Retorna o tipo formatado para exibicao."""
        type_map = {
            'primario': 'Primario',
            'apoio': 'Apoio',
            'gestao': 'Gestao'
        }
        return type_map.get(self.type, self.type)


class ValueChain(BaseModel):
    """
    Cadeia de Valor - nivel estrategico da hierarquia.
    Visao completa de todos os macroprocessos da organizacao.
    """
    id: str = Field(..., description="Identificador unico")
    name: str = Field(..., description="Nome da cadeia de valor")
    description: str = Field(default="", description="Descricao da cadeia de valor")
    organization: Optional[str] = Field(None, description="Nome da organizacao")
    mission: Optional[str] = Field(None, description="Missao da organizacao")
    vision: Optional[str] = Field(None, description="Visao da organizacao")
    values: List[str] = Field(
        default_factory=list,
        description="Valores da organizacao"
    )
    macroprocesses: List[str] = Field(
        default_factory=list,
        description="IDs dos macroprocessos"
    )
    primary_macroprocesses: List[str] = Field(
        default_factory=list,
        description="IDs dos macroprocessos primarios (ordenados)"
    )
    support_macroprocesses: List[str] = Field(
        default_factory=list,
        description="IDs dos macroprocessos de apoio"
    )
    management_macroprocesses: List[str] = Field(
        default_factory=list,
        description="IDs dos macroprocessos de gestao"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Valida que o ID nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("ID da cadeia de valor nao pode ser vazio")
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("Nome da cadeia de valor nao pode ser vazio")
        return v.strip()

    def get_all_macroprocesses(self) -> List[str]:
        """Retorna todos os IDs de macroprocessos."""
        all_ids = set(self.macroprocesses)
        all_ids.update(self.primary_macroprocesses)
        all_ids.update(self.support_macroprocesses)
        all_ids.update(self.management_macroprocesses)
        return list(all_ids)


class ProcessHierarchy(BaseModel):
    """
    Processo com suporte a hierarquia.
    Estende o conceito de processo para incluir relacionamentos hierarquicos.
    """
    id: str = Field(..., description="Identificador unico (ex: PROC-MKT-001)")
    name: str = Field(..., description="Nome do processo")
    description: str = Field(default="", description="Descricao do processo")
    level: Literal['processo', 'subprocesso'] = Field(
        default='processo',
        description="Nivel na hierarquia"
    )
    parent_id: Optional[str] = Field(
        None,
        description="ID do macroprocesso ou processo pai"
    )
    children: List[str] = Field(
        default_factory=list,
        description="IDs de subprocessos filhos"
    )
    owner: Optional[str] = Field(None, description="Dono/responsavel pelo processo")
    sipoc: Optional[SIPOC] = Field(None, description="SIPOC do processo")
    indicators: List[str] = Field(
        default_factory=list,
        description="Indicadores de desempenho"
    )
    documentation: Dict[str, str] = Field(
        default_factory=dict,
        description="Referencias de documentacao (pop_code, etc)"
    )
    miro_board_id: Optional[str] = Field(
        None,
        description="ID do board no Miro"
    )
    clickup_folder_id: Optional[str] = Field(
        None,
        description="ID da pasta no ClickUp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Valida que o ID nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("ID do processo nao pode ser vazio")
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("Nome do processo nao pode ser vazio")
        return v.strip()

    def is_subprocess(self) -> bool:
        """Verifica se e um subprocesso."""
        return self.level == 'subprocesso'

    def has_children(self) -> bool:
        """Verifica se tem subprocessos."""
        return len(self.children) > 0


class Activity(BaseModel):
    """
    Atividade - nivel tatico-operacional.
    Representa uma atividade dentro de um processo.
    """
    id: str = Field(..., description="Identificador unico (ex: PROC-MKT-001_E01)")
    name: str = Field(..., description="Nome da atividade (verbo no infinitivo)")
    description: str = Field(default="", description="Descricao da atividade")
    process_id: str = Field(..., description="ID do processo pai")
    numbering: str = Field(default="", description="Numeracao (ex: 1.1, 1.2)")
    responsible: Optional[str] = Field(None, description="Responsavel pela execucao")
    inputs: List[str] = Field(
        default_factory=list,
        description="Entradas necessarias"
    )
    outputs: List[str] = Field(
        default_factory=list,
        description="Saidas/entregas"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Ferramentas/sistemas utilizados"
    )
    tasks: List['Task'] = Field(
        default_factory=list,
        description="Tarefas que compoem a atividade"
    )
    documentation_ref: Optional[str] = Field(
        None,
        description="Referencia ao documento IT (ex: IT-001)"
    )
    clickup_task_id: Optional[str] = Field(
        None,
        description="ID da tarefa no ClickUp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Valida que o ID nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("ID da atividade nao pode ser vazio")
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("Nome da atividade nao pode ser vazio")
        return v.strip()


class Task(BaseModel):
    """
    Tarefa - nivel operacional detalhado.
    Acao especifica que nao possui entrega explicita.
    """
    id: str = Field(..., description="Identificador unico")
    name: str = Field(..., description="Nome da tarefa")
    description: str = Field(default="", description="Descricao da tarefa")
    activity_id: str = Field(..., description="ID da atividade pai")
    step_number: int = Field(..., ge=1, description="Numero do passo")
    responsible: Optional[str] = Field(None, description="Responsavel")
    estimated_time: Optional[str] = Field(None, description="Tempo estimado")
    instructions: Optional[str] = Field(
        None,
        description="Instrucoes detalhadas (como executar)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Valida que o ID nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("ID da tarefa nao pode ser vazio")
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("Nome da tarefa nao pode ser vazio")
        return v.strip()


class OrganizationHierarchy(BaseModel):
    """
    Hierarquia organizacional completa.
    Container para toda a estrutura de processos.
    """
    value_chain: Optional[ValueChain] = Field(
        None,
        description="Cadeia de Valor da organizacao"
    )
    macroprocesses: Dict[str, Macroprocess] = Field(
        default_factory=dict,
        description="Macroprocessos indexados por ID"
    )
    processes: Dict[str, ProcessHierarchy] = Field(
        default_factory=dict,
        description="Processos indexados por ID"
    )
    activities: Dict[str, Activity] = Field(
        default_factory=dict,
        description="Atividades indexadas por ID"
    )
    tasks: Dict[str, Task] = Field(
        default_factory=dict,
        description="Tarefas indexadas por ID"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de criacao"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de ultima atualizacao"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    def get_macroprocess(self, macro_id: str) -> Optional[Macroprocess]:
        """Busca macroprocesso por ID."""
        return self.macroprocesses.get(macro_id)

    def get_process(self, process_id: str) -> Optional[ProcessHierarchy]:
        """Busca processo por ID."""
        return self.processes.get(process_id)

    def get_activity(self, activity_id: str) -> Optional[Activity]:
        """Busca atividade por ID."""
        return self.activities.get(activity_id)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Busca tarefa por ID."""
        return self.tasks.get(task_id)

    def get_primary_macroprocesses(self) -> List[Macroprocess]:
        """Retorna macroprocessos primarios."""
        return [m for m in self.macroprocesses.values() if m.is_primary()]

    def get_support_macroprocesses(self) -> List[Macroprocess]:
        """Retorna macroprocessos de apoio."""
        return [m for m in self.macroprocesses.values() if m.is_support()]

    def get_management_macroprocesses(self) -> List[Macroprocess]:
        """Retorna macroprocessos de gestao."""
        return [m for m in self.macroprocesses.values() if m.is_management()]

    def get_processes_by_macroprocess(self, macro_id: str) -> List[ProcessHierarchy]:
        """Retorna processos de um macroprocesso."""
        return [p for p in self.processes.values() if p.parent_id == macro_id]

    def get_activities_by_process(self, process_id: str) -> List[Activity]:
        """Retorna atividades de um processo."""
        return [a for a in self.activities.values() if a.process_id == process_id]

    def add_macroprocess(self, macroprocess: Macroprocess):
        """Adiciona macroprocesso a hierarquia."""
        self.macroprocesses[macroprocess.id] = macroprocess
        self.updated_at = datetime.now()

    def add_process(self, process: ProcessHierarchy):
        """Adiciona processo a hierarquia."""
        self.processes[process.id] = process
        self.updated_at = datetime.now()

    def add_activity(self, activity: Activity):
        """Adiciona atividade a hierarquia."""
        self.activities[activity.id] = activity
        self.updated_at = datetime.now()

    def add_task(self, task: Task):
        """Adiciona tarefa a hierarquia."""
        self.tasks[task.id] = task
        self.updated_at = datetime.now()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Permitir referencia circular para Activity.tasks
Activity.model_rebuild()
