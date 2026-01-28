"""
Gerador de Checklist.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.process_model import Process, ProcessElement
from src.models.documentation_model import (
    Checklist, ChecklistItem, POP
)
from src.generators.base_generator import DocumentGenerator
from src.utils.logger import get_logger

logger = get_logger()


class ChecklistGenerator(DocumentGenerator):
    """
    Gerador de Checklists.
    Principio: "O simples funciona - e muito!"
    """

    @property
    def default_template_path(self) -> str:
        return "data/templates/checklist_template.md"

    def _get_fallback_template(self) -> str:
        return """# {code} - {title}

**Versao:** {version}
**Proposito:** {purpose}

## Checklist

{checklist_items_table}

---
**Elaborado por:** {author}
"""

    def generate(
        self,
        process: Process,
        code: Optional[str] = None,
        author: str = "",
        purpose: str = "",
        frequency: Optional[str] = None,
        trigger: Optional[str] = None,
        **kwargs
    ) -> Checklist:
        """
        Gera Checklist a partir de um processo.
        Baseado nos outputs das atividades.

        Args:
            process: Processo fonte
            code: Codigo do checklist (auto-gerado se nao fornecido)
            author: Autor do documento
            purpose: Proposito do checklist
            frequency: Frequencia de uso
            trigger: Gatilho para uso
            **kwargs: Argumentos adicionais

        Returns:
            Checklist gerado
        """
        logger.info(f"Gerando Checklist para processo: {process.name}")

        # Gerar codigo se nao fornecido
        if not code:
            code = self._generate_code("CL", 1)

        # Criar itens do checklist baseado nos outputs
        items = self._create_items_from_process(process)

        # Criar Checklist
        checklist = Checklist(
            id=f"cl_{process.process_id or process.name.lower().replace(' ', '_')}",
            code=code,
            title=f"Checklist - {process.name}",
            version="1.0",
            status='rascunho',
            author=author,
            process_id=process.process_id,
            purpose=purpose or f"Garantir a execucao correta do processo {process.name}",
            frequency=frequency,
            trigger=trigger,
            items=items,
            sign_off_required=kwargs.get('sign_off_required', False),
            pop_reference=process.pop_code,
            it_reference=None
        )

        logger.info(f"Checklist gerado: {checklist.code} com {len(items)} itens")
        return checklist

    def generate_from_pop(
        self,
        pop: POP,
        author: str = "",
        **kwargs
    ) -> Checklist:
        """
        Gera Checklist a partir de um POP.
        Baseado nos passos e outputs do POP.

        Args:
            pop: POP fonte
            author: Autor do documento
            **kwargs: Argumentos adicionais

        Returns:
            Checklist gerado
        """
        logger.info(f"Gerando Checklist a partir do POP: {pop.code}")

        code = self._generate_code("CL", 1)

        # Criar itens baseados nos passos do POP
        items = self._create_items_from_pop(pop)

        checklist = Checklist(
            id=f"cl_{pop.code.lower()}",
            code=code,
            title=f"Checklist - {pop.title}",
            version="1.0",
            status='rascunho',
            author=author,
            process_id=pop.process_id,
            purpose=f"Verificar execucao do processo conforme {pop.code}",
            frequency=kwargs.get('frequency'),
            trigger=kwargs.get('trigger'),
            items=items,
            sign_off_required=kwargs.get('sign_off_required', True),
            pop_reference=pop.code,
            it_reference=None
        )

        logger.info(f"Checklist gerado: {checklist.code}")
        return checklist

    def generate_for_activity(
        self,
        element: ProcessElement,
        process: Process,
        code: Optional[str] = None,
        author: str = "",
        **kwargs
    ) -> Checklist:
        """
        Gera Checklist para uma atividade especifica.

        Args:
            element: Elemento (atividade) fonte
            process: Processo pai
            code: Codigo do checklist
            author: Autor do documento
            **kwargs: Argumentos adicionais

        Returns:
            Checklist gerado
        """
        logger.info(f"Gerando Checklist para atividade: {element.name}")

        if not code:
            code = self._generate_code("CL", 1)

        items = self._create_items_from_element(element)

        checklist = Checklist(
            id=f"cl_{element.id}",
            code=code,
            title=f"Checklist - {element.name}",
            version="1.0",
            status='rascunho',
            author=author,
            process_id=process.process_id,
            purpose=f"Verificar execucao da atividade {element.name}",
            frequency=kwargs.get('frequency'),
            trigger=kwargs.get('trigger', f"Apos executar {element.name}"),
            items=items,
            sign_off_required=kwargs.get('sign_off_required', False),
            pop_reference=process.pop_code,
            it_reference=element.documentation_ref
        )

        return checklist

    def _create_items_from_process(self, process: Process) -> List[ChecklistItem]:
        """Cria itens de checklist baseado no processo."""
        items = []
        item_number = 1

        # Criar itens baseados nos outputs de cada tarefa
        for element in process.elements:
            if element.is_task():
                # Adicionar item para a atividade
                items.append(ChecklistItem(
                    number=item_number,
                    description=f"{element.name} executado",
                    criteria=f"Atividade {element.name} concluida conforme procedimento",
                    responsible=element.actor,
                    mandatory=True,
                    notes=None,
                    related_step=element.numbering
                ))
                item_number += 1

                # Adicionar itens para cada output
                for output in element.outputs:
                    items.append(ChecklistItem(
                        number=item_number,
                        description=f"{output} gerado",
                        criteria=f"Verificar se {output} foi produzido corretamente",
                        responsible=element.actor,
                        mandatory=True,
                        notes=None,
                        related_step=element.numbering
                    ))
                    item_number += 1

        # Adicionar item de verificacao final se houver outputs do processo
        if process.outputs:
            items.append(ChecklistItem(
                number=item_number,
                description="Todas as entregas do processo verificadas",
                criteria=f"Entregas: {', '.join(process.outputs)}",
                responsible=process.owner,
                mandatory=True,
                notes="Verificacao final do processo",
                related_step=None
            ))

        return items

    def _create_items_from_pop(self, pop: POP) -> List[ChecklistItem]:
        """Cria itens de checklist baseado no POP."""
        items = []
        item_number = 1

        if pop.process_map:
            for step in pop.process_map.steps:
                if step.type == 'task':
                    # Item para a tarefa
                    items.append(ChecklistItem(
                        number=item_number,
                        description=f"{step.name} executado",
                        criteria=f"Conforme passo {step.number} do {pop.code}",
                        responsible=step.responsible,
                        mandatory=True,
                        notes=None,
                        related_step=step.number
                    ))
                    item_number += 1

                    # Itens para outputs
                    for output in step.outputs:
                        items.append(ChecklistItem(
                            number=item_number,
                            description=f"{output} verificado",
                            criteria=f"Output do passo {step.number}",
                            responsible=step.responsible,
                            mandatory=True,
                            notes=None,
                            related_step=step.number
                        ))
                        item_number += 1

        return items

    def _create_items_from_element(self, element: ProcessElement) -> List[ChecklistItem]:
        """Cria itens de checklist baseado em um elemento."""
        items = []
        item_number = 1

        # Item principal
        items.append(ChecklistItem(
            number=item_number,
            description=f"{element.name} iniciado",
            criteria="Atividade iniciada corretamente",
            responsible=element.actor,
            mandatory=True,
            notes=None,
            related_step=element.numbering
        ))
        item_number += 1

        # Itens para inputs verificados
        for inp in element.inputs:
            items.append(ChecklistItem(
                number=item_number,
                description=f"Entrada verificada: {inp}",
                criteria=f"Confirmar disponibilidade de {inp}",
                responsible=element.actor,
                mandatory=True,
                notes=None,
                related_step=element.numbering
            ))
            item_number += 1

        # Itens para outputs gerados
        for output in element.outputs:
            items.append(ChecklistItem(
                number=item_number,
                description=f"Saida gerada: {output}",
                criteria=f"Verificar qualidade de {output}",
                responsible=element.actor,
                mandatory=True,
                notes=None,
                related_step=element.numbering
            ))
            item_number += 1

        # Item de conclusao
        items.append(ChecklistItem(
            number=item_number,
            description=f"{element.name} concluido",
            criteria="Atividade finalizada com sucesso",
            responsible=element.actor,
            mandatory=True,
            notes=None,
            related_step=element.numbering
        ))

        return items

    def to_markdown(self, document: Checklist) -> str:
        """Exporta Checklist para Markdown."""
        template = self._load_template()

        # Preparar tabela de itens
        checklist_items_table = ""
        for item in document.items:
            mandatory = "Sim" if item.mandatory else "Nao"
            responsible = item.responsible or "-"
            notes = item.notes or ""
            checklist_items_table += f"| {item.number} | {item.description} | {item.criteria} | {responsible} | {mandatory} | [ ] |\n"

        if not checklist_items_table:
            checklist_items_table = "| - | - | - | - | - | - |"

        # Preparar secao de observacoes
        notes_section = ""
        for item in document.items:
            if item.notes:
                notes_section += f"- **Item {item.number}:** {item.notes}\n"
        if not notes_section:
            notes_section = "Nenhuma observacao adicional."

        # Preparar secao de assinatura
        sign_off_section = ""
        if document.sign_off_required:
            sign_off_section = "**Assinatura obrigatoria ao final da execucao.**"

        # Contexto para renderizacao
        context = {
            'code': document.code,
            'title': document.title,
            'version': document.version,
            'status': document.status,
            'created_at': self._format_date(document.created_at),
            'updated_at': self._format_date(document.updated_at),
            'purpose': document.purpose,
            'frequency': document.frequency or "Conforme necessidade",
            'trigger': document.trigger or "Conforme procedimento",
            'pop_reference': document.pop_reference or "-",
            'it_reference': document.it_reference or "-",
            'checklist_items_table': checklist_items_table,
            'notes_section': notes_section,
            'sign_off_section': sign_off_section,
            'author': document.author or "-"
        }

        return self._render_template(template, context)
