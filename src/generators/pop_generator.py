"""
Gerador de POP (Procedimento Operacional Padrao).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.models.process_model import Process, ProcessElement
from src.models.documentation_model import (
    POP, ProcessMap, MappedStep, StepDescription,
    Responsibility, Definition, Record, Appendix
)
from src.generators.base_generator import DocumentGenerator
from src.utils.logger import get_logger

logger = get_logger()


class POPGenerator(DocumentGenerator):
    """
    Gerador de Procedimento Operacional Padrao.
    Cria POPs a partir de processos mapeados.
    """

    @property
    def default_template_path(self) -> str:
        return "data/templates/pop_template.md"

    def _get_fallback_template(self) -> str:
        return """# {code} - {title}

**Versao:** {version}
**Status:** {status}

## 1. Objetivo
{objective}

## 2. Escopo
{scope}

## 3. Responsabilidades
{responsibilities_table}

## 4. Mapeamento do Processo
{process_steps_table}

## 5. Descricao das Etapas
{step_descriptions}

---
**Elaborado por:** {author}
"""

    def generate(
        self,
        process: Process,
        code: Optional[str] = None,
        author: str = "",
        objective: str = "",
        scope: str = "",
        **kwargs
    ) -> POP:
        """
        Gera POP a partir de um processo.

        Args:
            process: Processo fonte
            code: Codigo do POP (auto-gerado se nao fornecido)
            author: Autor do documento
            objective: Objetivo do procedimento
            scope: Escopo de aplicacao
            **kwargs: Argumentos adicionais

        Returns:
            POP gerado
        """
        logger.info(f"Gerando POP para processo: {process.name}")

        # Gerar codigo se nao fornecido
        if not code:
            code = process.pop_code or self._generate_code("POP", 1)

        # Gerar numeracao dos elementos
        numbering_map = self._number_elements(process)

        # Criar mapa de processo
        process_map = self._create_process_map(process, numbering_map)

        # Extrair responsabilidades
        responsibilities = self._create_responsibilities(process)

        # Gerar descricoes dos passos
        step_descriptions = self._create_step_descriptions(process, numbering_map)

        # Criar POP
        pop = POP(
            id=f"pop_{process.process_id or process.name.lower().replace(' ', '_')}",
            code=code,
            title=process.name,
            version="1.0",
            status='rascunho',
            author=author,
            process_id=process.process_id,
            objective=objective or f"Padronizar a execucao do processo {process.name}",
            scope=scope or f"Este procedimento aplica-se a todos os colaboradores envolvidos no processo {process.name}",
            responsibilities=responsibilities,
            definitions=[],
            process_map=process_map,
            step_descriptions=step_descriptions,
            records=[],
            references=[],
            appendices=[],
            related_its=[],
            related_checklists=[]
        )

        # Adicionar referencia ao Miro se existir
        if process.miro_board_id:
            pop.process_map.miro_board_id = process.miro_board_id
            pop.process_map.diagram_ref = process.miro_board_url

        logger.info(f"POP gerado: {pop.code}")
        return pop

    def _create_process_map(
        self,
        process: Process,
        numbering_map: Dict[str, str]
    ) -> ProcessMap:
        """Cria mapa de processo com passos numerados."""
        steps = []

        for element in process.elements:
            if element.is_task() or element.is_gateway():
                step = MappedStep(
                    number=numbering_map.get(element.id, ""),
                    name=element.name,
                    type=element.type,
                    responsible=element.actor or "",
                    description=element.description or "",
                    inputs=element.inputs,
                    outputs=element.outputs,
                    tools=element.tools,
                    criteria=element.metadata.get('criteria') if element.is_gateway() else None,
                    it_reference=element.documentation_ref
                )
                steps.append(step)

        return ProcessMap(
            diagram_ref=process.miro_board_url,
            miro_board_id=process.miro_board_id,
            steps=steps
        )

    def _create_responsibilities(self, process: Process) -> List[Responsibility]:
        """Cria lista de responsabilidades por cargo."""
        responsibilities = []

        for actor in process.actors:
            actor_elements = process.get_elements_by_actor(actor)
            tasks = [e.name for e in actor_elements if e.is_task()]

            if tasks:
                responsibilities.append(Responsibility(
                    role=actor,
                    responsibilities=tasks
                ))

        return responsibilities

    def _create_step_descriptions(
        self,
        process: Process,
        numbering_map: Dict[str, str]
    ) -> List[StepDescription]:
        """Cria descricoes detalhadas dos passos."""
        descriptions = []

        for element in process.elements:
            if element.is_task():
                step_number = numbering_map.get(element.id, "")

                description = StepDescription(
                    step_number=step_number,
                    what=element.name,
                    how=element.description or f"Executar a atividade {element.name}",
                    why=element.metadata.get('why', f"Garantir a correta execucao de {element.name}"),
                    when=element.metadata.get('when', "Conforme fluxo do processo"),
                    where=element.metadata.get('where', "No ambiente de trabalho"),
                    who=element.actor or "Responsavel designado",
                    notes=element.metadata.get('notes'),
                    it_reference=element.documentation_ref
                )
                descriptions.append(description)

        return descriptions

    def to_markdown(self, document: POP) -> str:
        """Exporta POP para Markdown."""
        template = self._load_template()

        # Preparar tabela de responsabilidades
        responsibilities_table = ""
        for resp in document.responsibilities:
            tasks = ", ".join(resp.responsibilities)
            responsibilities_table += f"| {resp.role} | {tasks} |\n"

        # Preparar tabela de definicoes
        definitions_table = ""
        for defn in document.definitions:
            definitions_table += f"| {defn.term} | {defn.definition} |\n"

        # Preparar tabela de passos do processo
        process_steps_table = ""
        if document.process_map:
            for step in document.process_map.steps:
                inputs = ", ".join(step.inputs) if step.inputs else "-"
                outputs = ", ".join(step.outputs) if step.outputs else "-"
                tools = ", ".join(step.tools) if step.tools else "-"
                process_steps_table += f"| {step.number} | {step.name} | {step.type} | {step.responsible} | {inputs} | {outputs} | {tools} |\n"

        # Preparar descricoes dos passos
        step_descriptions = ""
        for desc in document.step_descriptions:
            step_descriptions += f"""
### Passo {desc.step_number}: {desc.what}

**O que:** {desc.what}
**Como:** {desc.how}
**Por que:** {desc.why}
**Quando:** {desc.when}
**Onde:** {desc.where}
**Quem:** {desc.who}
"""
            if desc.it_reference:
                step_descriptions += f"**IT Relacionada:** {desc.it_reference}\n"
            if desc.notes:
                step_descriptions += f"**Observacoes:** {desc.notes}\n"

        # Preparar tabela de registros
        records_table = ""
        for record in document.records:
            records_table += f"| {record.name} | {record.description} | {record.retention_period or '-'} | {record.storage_location or '-'} |\n"

        # Preparar lista de referencias
        references_list = "\n".join([f"- {ref}" for ref in document.references]) if document.references else "- Nenhuma referencia"

        # Preparar lista de anexos
        appendices_list = ""
        for appendix in document.appendices:
            appendices_list += f"### Anexo {appendix.number}: {appendix.title}\n"
            appendices_list += f"**Tipo:** {appendix.content_type}\n"
            if appendix.content:
                appendices_list += f"{appendix.content}\n"
            if appendix.file_ref:
                appendices_list += f"**Arquivo:** {appendix.file_ref}\n"

        # Preparar listas de documentos relacionados
        related_its_list = "\n".join([f"- {it}" for it in document.related_its]) if document.related_its else "- Nenhuma IT relacionada"
        related_checklists_list = "\n".join([f"- {cl}" for cl in document.related_checklists]) if document.related_checklists else "- Nenhum checklist relacionado"

        # Preparar imagem do diagrama
        diagram_image = ""
        if document.process_map and document.process_map.diagram_ref:
            diagram_image = f"![Diagrama do Processo]({document.process_map.diagram_ref})"

        # Preparar URL do Miro
        miro_board_url = ""
        if document.process_map and document.process_map.miro_board_id:
            miro_board_url = f"https://miro.com/app/board/{document.process_map.miro_board_id}"

        # Contexto para renderizacao
        context = {
            'code': document.code,
            'title': document.title,
            'version': document.version,
            'status': document.status,
            'created_at': self._format_date(document.created_at),
            'updated_at': self._format_date(document.updated_at),
            'objective': document.objective,
            'scope': document.scope,
            'responsibilities_table': responsibilities_table or "| - | - |",
            'definitions_table': definitions_table or "| - | - |",
            'diagram_image': diagram_image,
            'miro_board_url': miro_board_url,
            'process_steps_table': process_steps_table or "| - | - | - | - | - | - | - |",
            'step_descriptions': step_descriptions,
            'records_table': records_table or "| - | - | - | - |",
            'references_list': references_list,
            'appendices_list': appendices_list or "Nenhum anexo",
            'related_its_list': related_its_list,
            'related_checklists_list': related_checklists_list,
            'author': document.author or "-",
            'reviewer': document.reviewer or "-",
            'approver': document.approver or "-"
        }

        return self._render_template(template, context)
