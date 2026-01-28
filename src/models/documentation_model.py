"""
Modelos de documentacao padronizada.
Suporta POP (Procedimento Operacional Padrao), IT (Instrucao de Trabalho),
Checklist, Manual e Politica.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class DocumentBase(BaseModel):
    """
    Classe base para todos os documentos padronizados.
    """
    id: str = Field(..., description="Identificador unico interno")
    code: str = Field(..., description="Codigo do documento (ex: POP-001, IT-001)")
    title: str = Field(..., description="Titulo do documento")
    version: str = Field(default="1.0", description="Versao do documento")
    status: Literal['rascunho', 'revisao', 'aprovado', 'obsoleto'] = Field(
        default='rascunho',
        description="Status do documento"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de criacao"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de ultima atualizacao"
    )
    author: str = Field(default="", description="Autor do documento")
    reviewer: Optional[str] = Field(None, description="Revisor")
    approver: Optional[str] = Field(None, description="Aprovador")
    process_id: Optional[str] = Field(None, description="ID do processo relacionado")
    tags: List[str] = Field(
        default_factory=list,
        description="Tags para categorizar o documento"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Valida que o codigo nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("Codigo do documento nao pode ser vazio")
        return v.strip().upper()

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Valida que o titulo nao esta vazio."""
        if not v or not v.strip():
            raise ValueError("Titulo do documento nao pode ser vazio")
        return v.strip()

    def is_approved(self) -> bool:
        """Verifica se o documento esta aprovado."""
        return self.status == 'aprovado'

    def is_draft(self) -> bool:
        """Verifica se o documento e um rascunho."""
        return self.status == 'rascunho'

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================
# Modelos para POP (Procedimento Operacional Padrao)
# ============================================

class Responsibility(BaseModel):
    """
    Responsabilidade em documento POP.
    Define papel e suas responsabilidades.
    """
    role: str = Field(..., description="Cargo/funcao")
    responsibilities: List[str] = Field(
        default_factory=list,
        description="Lista de responsabilidades"
    )


class Definition(BaseModel):
    """
    Definicao/termo no glossario do POP.
    """
    term: str = Field(..., description="Termo a ser definido")
    definition: str = Field(..., description="Definicao do termo")


class MappedStep(BaseModel):
    """
    Passo mapeado no BPMN com numeracao.
    Representa uma atividade no diagrama de processo.
    """
    number: str = Field(..., description="Numeracao (ex: 1, 1.1, 1.1.1)")
    name: str = Field(..., description="Nome da atividade")
    type: Literal['task', 'gateway', 'event', 'annotation'] = Field(
        default='task',
        description="Tipo do elemento BPMN"
    )
    responsible: str = Field(default="", description="Responsavel pela execucao")
    description: str = Field(default="", description="Descricao da atividade")
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
        description="Ferramentas/sistemas"
    )
    criteria: Optional[str] = Field(
        None,
        description="Criterio de decisao (para gateways)"
    )
    it_reference: Optional[str] = Field(
        None,
        description="Referencia a IT (ex: IT-001)"
    )


class ProcessMap(BaseModel):
    """
    Mapeamento de processo para POP.
    Inclui referencia ao diagrama e passos numerados.
    """
    diagram_ref: Optional[str] = Field(
        None,
        description="URL ou referencia ao diagrama (Miro, imagem)"
    )
    miro_board_id: Optional[str] = Field(
        None,
        description="ID do board no Miro"
    )
    steps: List[MappedStep] = Field(
        default_factory=list,
        description="Passos mapeados com numeracao"
    )


class StepDescription(BaseModel):
    """
    Descricao detalhada de passo no POP.
    Segue o modelo 5W1H (What, Why, When, Where, Who, How).
    """
    step_number: str = Field(..., description="Numero do passo referenciado")
    what: str = Field(default="", description="O que fazer")
    how: str = Field(default="", description="Como fazer")
    why: str = Field(default="", description="Por que fazer")
    when: str = Field(default="", description="Quando fazer")
    where: str = Field(default="", description="Onde fazer")
    who: str = Field(default="", description="Quem faz")
    notes: Optional[str] = Field(None, description="Observacoes adicionais")
    it_reference: Optional[str] = Field(
        None,
        description="Referencia a IT para detalhes"
    )


class Record(BaseModel):
    """
    Registro gerado pelo processo.
    """
    name: str = Field(..., description="Nome do registro")
    description: str = Field(default="", description="Descricao")
    retention_period: Optional[str] = Field(
        None,
        description="Periodo de retencao"
    )
    storage_location: Optional[str] = Field(
        None,
        description="Local de armazenamento"
    )


class Appendix(BaseModel):
    """
    Anexo de documento.
    """
    number: str = Field(..., description="Numero do anexo (ex: A, B, 1)")
    title: str = Field(..., description="Titulo do anexo")
    content_type: Literal['formulario', 'tabela', 'diagrama', 'template', 'outro'] = Field(
        default='outro',
        description="Tipo de conteudo"
    )
    content: Optional[str] = Field(None, description="Conteudo do anexo")
    file_ref: Optional[str] = Field(None, description="Referencia a arquivo externo")


class POP(DocumentBase):
    """
    Procedimento Operacional Padrao.
    Documento principal para padronizar processos e subprocessos.
    """
    document_type: Literal['POP'] = Field(default='POP', description="Tipo do documento")
    objective: str = Field(default="", description="Objetivo do procedimento")
    scope: str = Field(default="", description="Escopo de aplicacao")
    responsibilities: List[Responsibility] = Field(
        default_factory=list,
        description="Responsabilidades por cargo"
    )
    definitions: List[Definition] = Field(
        default_factory=list,
        description="Glossario de termos"
    )
    process_map: Optional[ProcessMap] = Field(
        None,
        description="Mapeamento BPMN numerado"
    )
    step_descriptions: List[StepDescription] = Field(
        default_factory=list,
        description="Descricoes detalhadas dos passos"
    )
    records: List[Record] = Field(
        default_factory=list,
        description="Registros gerados"
    )
    references: List[str] = Field(
        default_factory=list,
        description="Referencias (outros POPs, normas, etc)"
    )
    appendices: List[Appendix] = Field(
        default_factory=list,
        description="Anexos"
    )
    related_its: List[str] = Field(
        default_factory=list,
        description="Codigos das ITs relacionadas"
    )
    related_checklists: List[str] = Field(
        default_factory=list,
        description="Codigos dos Checklists relacionados"
    )

    def get_step_description(self, step_number: str) -> Optional[StepDescription]:
        """Busca descricao de passo por numero."""
        for desc in self.step_descriptions:
            if desc.step_number == step_number:
                return desc
        return None

    def get_mapped_step(self, step_number: str) -> Optional[MappedStep]:
        """Busca passo mapeado por numero."""
        if self.process_map:
            for step in self.process_map.steps:
                if step.number == step_number:
                    return step
        return None


# ============================================
# Modelos para IT (Instrucao de Trabalho)
# ============================================

class Material(BaseModel):
    """
    Material/recurso necessario para IT.
    """
    name: str = Field(..., description="Nome do material")
    quantity: Optional[str] = Field(None, description="Quantidade necessaria")
    specification: Optional[str] = Field(None, description="Especificacao tecnica")


class ITStep(BaseModel):
    """
    Passo detalhado de Instrucao de Trabalho.
    Inclui suporte para prints e imagens.
    """
    number: int = Field(..., ge=1, description="Numero do passo")
    action: str = Field(..., description="Acao a ser executada")
    details: str = Field(default="", description="Detalhes de como executar")
    caution: Optional[str] = Field(None, description="Alertas/cuidados")
    image_ref: Optional[str] = Field(None, description="Referencia a imagem/print")
    image_description: Optional[str] = Field(None, description="Descricao da imagem")
    estimated_time: Optional[str] = Field(None, description="Tempo estimado")
    tips: Optional[str] = Field(None, description="Dicas uteis")
    system_path: Optional[str] = Field(
        None,
        description="Caminho no sistema (ex: Menu > Opcao > Submenu)"
    )


class Troubleshooting(BaseModel):
    """
    Resolucao de problemas comuns.
    """
    problem: str = Field(..., description="Descricao do problema")
    possible_causes: List[str] = Field(
        default_factory=list,
        description="Possiveis causas"
    )
    solutions: List[str] = Field(
        default_factory=list,
        description="Solucoes possiveis"
    )


class IT(DocumentBase):
    """
    Instrucao de Trabalho.
    Documento detalhado para padronizar atividades especificas.
    Objetivo: colaborador executa sem apoio.
    """
    document_type: Literal['IT'] = Field(default='IT', description="Tipo do documento")
    activity_id: Optional[str] = Field(None, description="ID da atividade relacionada")
    pop_reference: Optional[str] = Field(
        None,
        description="Codigo do POP relacionado"
    )
    step_in_pop: Optional[str] = Field(
        None,
        description="Numero do passo no POP"
    )
    objective: str = Field(default="", description="Objetivo da instrucao")
    target_audience: str = Field(
        default="",
        description="Publico-alvo (nivel de experiencia)"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Pre-requisitos para execucao"
    )
    safety_requirements: List[str] = Field(
        default_factory=list,
        description="Requisitos de seguranca"
    )
    materials: List[Material] = Field(
        default_factory=list,
        description="Materiais/recursos necessarios"
    )
    steps: List[ITStep] = Field(
        default_factory=list,
        description="Passos detalhados"
    )
    quality_criteria: List[str] = Field(
        default_factory=list,
        description="Criterios de qualidade"
    )
    troubleshooting: List[Troubleshooting] = Field(
        default_factory=list,
        description="Resolucao de problemas"
    )
    related_manuals: List[str] = Field(
        default_factory=list,
        description="Manuais relacionados"
    )
    clickup_task_id: Optional[str] = Field(
        None,
        description="ID da tarefa no ClickUp"
    )

    def get_step(self, step_number: int) -> Optional[ITStep]:
        """Busca passo por numero."""
        for step in self.steps:
            if step.number == step_number:
                return step
        return None


# ============================================
# Modelos para Checklist
# ============================================

class ChecklistItem(BaseModel):
    """
    Item individual do checklist.
    """
    number: int = Field(..., ge=1, description="Numero do item")
    description: str = Field(..., description="Descricao do item a verificar")
    criteria: str = Field(default="", description="Criterio de aceitacao")
    responsible: Optional[str] = Field(None, description="Responsavel pela verificacao")
    mandatory: bool = Field(default=True, description="Se e obrigatorio")
    notes: Optional[str] = Field(None, description="Observacoes")
    related_step: Optional[str] = Field(
        None,
        description="Passo relacionado no POP/IT"
    )


class Checklist(DocumentBase):
    """
    Checklist de verificacao.
    Documento simples para garantir execucao correta.
    Principio: "O simples funciona - e muito!"
    """
    document_type: Literal['CL'] = Field(default='CL', description="Tipo do documento")
    purpose: str = Field(default="", description="Proposito do checklist")
    frequency: Optional[str] = Field(
        None,
        description="Frequencia de uso (diario, semanal, etc)"
    )
    trigger: Optional[str] = Field(
        None,
        description="Gatilho para uso (antes de, apos, etc)"
    )
    items: List[ChecklistItem] = Field(
        default_factory=list,
        description="Itens do checklist"
    )
    sign_off_required: bool = Field(
        default=False,
        description="Requer assinatura de conclusao"
    )
    pop_reference: Optional[str] = Field(
        None,
        description="Codigo do POP relacionado"
    )
    it_reference: Optional[str] = Field(
        None,
        description="Codigo da IT relacionada"
    )

    def get_mandatory_items(self) -> List[ChecklistItem]:
        """Retorna apenas itens obrigatorios."""
        return [item for item in self.items if item.mandatory]

    def get_optional_items(self) -> List[ChecklistItem]:
        """Retorna apenas itens opcionais."""
        return [item for item in self.items if not item.mandatory]


# ============================================
# Modelos para Manual
# ============================================

class ManualSection(BaseModel):
    """
    Secao de um manual.
    """
    number: str = Field(..., description="Numero da secao (ex: 1, 1.1)")
    title: str = Field(..., description="Titulo da secao")
    content: str = Field(default="", description="Conteudo da secao")
    subsections: List['ManualSection'] = Field(
        default_factory=list,
        description="Subsecoes"
    )
    images: List[str] = Field(
        default_factory=list,
        description="Referencias a imagens"
    )


class Manual(DocumentBase):
    """
    Manual de uso de ferramenta/sistema.
    Similar ao manual de uma TV - facilita aprendizado.
    """
    document_type: Literal['MAN'] = Field(default='MAN', description="Tipo do documento")
    tool_name: str = Field(default="", description="Nome da ferramenta/sistema")
    tool_version: Optional[str] = Field(None, description="Versao da ferramenta")
    purpose: str = Field(default="", description="Proposito do manual")
    target_audience: str = Field(default="", description="Publico-alvo")
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Pre-requisitos"
    )
    sections: List[ManualSection] = Field(
        default_factory=list,
        description="Secoes do manual"
    )
    quick_reference: Optional[str] = Field(
        None,
        description="Guia de referencia rapida"
    )
    faq: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Perguntas frequentes (question, answer)"
    )


# ============================================
# Modelos para Politica
# ============================================

class PolicySection(BaseModel):
    """
    Secao de uma politica.
    """
    number: str = Field(..., description="Numero da secao")
    title: str = Field(..., description="Titulo da secao")
    content: str = Field(default="", description="Conteudo")
    guidelines: List[str] = Field(
        default_factory=list,
        description="Diretrizes especificas"
    )


class Policy(DocumentBase):
    """
    Politica organizacional.
    Define diretrizes e regras macro da organizacao.
    """
    document_type: Literal['POL'] = Field(default='POL', description="Tipo do documento")
    purpose: str = Field(default="", description="Proposito da politica")
    scope: str = Field(default="", description="Escopo de aplicacao")
    target_audience: str = Field(default="", description="Publico-alvo")
    principles: List[str] = Field(
        default_factory=list,
        description="Principios norteadores"
    )
    sections: List[PolicySection] = Field(
        default_factory=list,
        description="Secoes da politica"
    )
    compliance_requirements: List[str] = Field(
        default_factory=list,
        description="Requisitos de conformidade"
    )
    exceptions: Optional[str] = Field(
        None,
        description="Casos de excecao"
    )
    related_policies: List[str] = Field(
        default_factory=list,
        description="Politicas relacionadas"
    )
    related_pops: List[str] = Field(
        default_factory=list,
        description="POPs relacionados"
    )


# ============================================
# Container de Documentacao
# ============================================

class DocumentationSet(BaseModel):
    """
    Conjunto de documentacao de um processo.
    Agrupa todos os documentos relacionados.
    """
    process_id: str = Field(..., description="ID do processo")
    process_name: str = Field(..., description="Nome do processo")
    pop: Optional[POP] = Field(None, description="POP do processo")
    its: List[IT] = Field(
        default_factory=list,
        description="ITs das atividades"
    )
    checklists: List[Checklist] = Field(
        default_factory=list,
        description="Checklists"
    )
    manuals: List[Manual] = Field(
        default_factory=list,
        description="Manuais relacionados"
    )
    policies: List[Policy] = Field(
        default_factory=list,
        description="Politicas relacionadas"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de criacao"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de ultima atualizacao"
    )

    def get_it_by_code(self, code: str) -> Optional[IT]:
        """Busca IT por codigo."""
        for it in self.its:
            if it.code == code:
                return it
        return None

    def get_checklist_by_code(self, code: str) -> Optional[Checklist]:
        """Busca checklist por codigo."""
        for cl in self.checklists:
            if cl.code == code:
                return cl
        return None

    def is_complete(self) -> bool:
        """Verifica se a documentacao esta completa."""
        return (
            self.pop is not None and
            self.pop.is_approved() and
            len(self.its) > 0
        )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Permitir referencia circular para ManualSection
ManualSection.model_rebuild()
