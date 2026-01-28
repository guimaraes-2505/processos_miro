"""
Gerador de IT (Instrucao de Trabalho).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.process_model import Process, ProcessElement
from src.models.documentation_model import (
    IT, ITStep, Material, Troubleshooting
)
from src.generators.base_generator import DocumentGenerator
from src.utils.logger import get_logger

logger = get_logger()


class ITGenerator(DocumentGenerator):
    """
    Gerador de Instrucao de Trabalho.
    Cria ITs detalhadas para atividades especificas.
    """

    @property
    def default_template_path(self) -> str:
        return "data/templates/it_template.md"

    def _get_fallback_template(self) -> str:
        return """# {code} - {title}

**Versao:** {version}
**Status:** {status}
**POP Relacionado:** {pop_reference}

## 1. Objetivo
{objective}

## 2. Pre-requisitos
{prerequisites_list}

## 3. Passos Detalhados
{detailed_steps}

## 4. Criterios de Qualidade
{quality_criteria_list}

---
**Elaborado por:** {author}
"""

    def generate(
        self,
        element: ProcessElement,
        process: Process,
        code: Optional[str] = None,
        author: str = "",
        objective: str = "",
        **kwargs
    ) -> IT:
        """
        Gera IT a partir de um elemento de processo.

        Args:
            element: Elemento (atividade) fonte
            process: Processo pai
            code: Codigo da IT (auto-gerado se nao fornecido)
            author: Autor do documento
            objective: Objetivo da instrucao
            **kwargs: Argumentos adicionais

        Returns:
            IT gerada
        """
        logger.info(f"Gerando IT para atividade: {element.name}")

        # Gerar codigo se nao fornecido
        if not code:
            code = element.documentation_ref or self._generate_code("IT", 1)

        # Criar passos detalhados
        steps = self._create_steps(element, kwargs.get('detailed_steps', []))

        # Criar IT
        it = IT(
            id=f"it_{element.id}",
            code=code,
            title=element.name,
            version="1.0",
            status='rascunho',
            author=author,
            process_id=process.process_id,
            activity_id=element.id,
            pop_reference=process.pop_code,
            step_in_pop=element.numbering,
            objective=objective or f"Detalhar a execucao da atividade {element.name}",
            target_audience=kwargs.get('target_audience', "Colaboradores envolvidos na atividade"),
            prerequisites=self._extract_prerequisites(element),
            safety_requirements=kwargs.get('safety_requirements', []),
            materials=self._extract_materials(element),
            steps=steps,
            quality_criteria=self._extract_quality_criteria(element),
            troubleshooting=kwargs.get('troubleshooting', []),
            related_manuals=kwargs.get('related_manuals', []),
            clickup_task_id=element.clickup_task_id
        )

        logger.info(f"IT gerada: {it.code}")
        return it

    def generate_from_process(
        self,
        process: Process,
        author: str = "",
        **kwargs
    ) -> List[IT]:
        """
        Gera ITs para todas as atividades de um processo.

        Args:
            process: Processo fonte
            author: Autor dos documentos
            **kwargs: Argumentos adicionais

        Returns:
            Lista de ITs geradas
        """
        logger.info(f"Gerando ITs para processo: {process.name}")

        its = []
        tasks = process.get_tasks()

        for idx, task in enumerate(tasks, start=1):
            code = self._generate_code("IT", idx)
            it = self.generate(
                element=task,
                process=process,
                code=code,
                author=author,
                **kwargs
            )
            its.append(it)

        logger.info(f"Total de ITs geradas: {len(its)}")
        return its

    def _create_steps(
        self,
        element: ProcessElement,
        detailed_steps: List[Dict[str, Any]]
    ) -> List[ITStep]:
        """Cria passos detalhados para a IT."""
        steps = []

        if detailed_steps:
            # Usar passos fornecidos
            for idx, step_data in enumerate(detailed_steps, start=1):
                step = ITStep(
                    number=idx,
                    action=step_data.get('action', ''),
                    details=step_data.get('details', ''),
                    caution=step_data.get('caution'),
                    image_ref=step_data.get('image_ref'),
                    image_description=step_data.get('image_description'),
                    estimated_time=step_data.get('estimated_time'),
                    tips=step_data.get('tips'),
                    system_path=step_data.get('system_path')
                )
                steps.append(step)
        else:
            # Gerar passos basicos a partir do elemento
            if element.description:
                steps.append(ITStep(
                    number=1,
                    action=element.name,
                    details=element.description
                ))

            # Adicionar passo de verificacao se houver outputs
            if element.outputs:
                steps.append(ITStep(
                    number=len(steps) + 1,
                    action="Verificar resultado",
                    details=f"Confirmar que as seguintes saidas foram geradas: {', '.join(element.outputs)}"
                ))

        return steps

    def _extract_prerequisites(self, element: ProcessElement) -> List[str]:
        """Extrai pre-requisitos do elemento."""
        prerequisites = []

        # Inputs como pre-requisitos
        if element.inputs:
            prerequisites.extend([f"Ter disponivel: {inp}" for inp in element.inputs])

        # Ferramentas como pre-requisitos
        if element.tools:
            prerequisites.extend([f"Acesso a: {tool}" for tool in element.tools])

        if not prerequisites:
            prerequisites.append("Nenhum pre-requisito especifico")

        return prerequisites

    def _extract_materials(self, element: ProcessElement) -> List[Material]:
        """Extrai materiais/recursos do elemento."""
        materials = []

        # Ferramentas como materiais
        for tool in element.tools:
            materials.append(Material(
                name=tool,
                quantity=None,
                specification=None
            ))

        return materials

    def _extract_quality_criteria(self, element: ProcessElement) -> List[str]:
        """Extrai criterios de qualidade do elemento."""
        criteria = []

        # Outputs como criterios de qualidade
        if element.outputs:
            for output in element.outputs:
                criteria.append(f"Verificar se {output} foi gerado corretamente")

        if not criteria:
            criteria.append(f"Atividade {element.name} executada conforme descrito")

        return criteria

    def to_markdown(self, document: IT) -> str:
        """Exporta IT para Markdown."""
        template = self._load_template()

        # Preparar lista de pre-requisitos
        prerequisites_list = "\n".join([f"- [ ] {prereq}" for prereq in document.prerequisites]) if document.prerequisites else "- Nenhum pre-requisito"

        # Preparar lista de requisitos de seguranca
        safety_requirements_list = "\n".join([f"- {req}" for req in document.safety_requirements]) if document.safety_requirements else "- Nenhum requisito de seguranca especifico"

        # Preparar tabela de materiais
        materials_table = ""
        for material in document.materials:
            qty = material.quantity or "-"
            spec = material.specification or "-"
            materials_table += f"| {material.name} | {qty} | {spec} |\n"
        if not materials_table:
            materials_table = "| - | - | - |"

        # Preparar passos detalhados
        detailed_steps = ""
        for step in document.steps:
            detailed_steps += f"""
### Passo {step.number}: {step.action}

{step.details}
"""
            if step.system_path:
                detailed_steps += f"\n**Caminho no sistema:** `{step.system_path}`\n"
            if step.caution:
                detailed_steps += f"\n> **ATENCAO:** {step.caution}\n"
            if step.tips:
                detailed_steps += f"\n**Dica:** {step.tips}\n"
            if step.image_ref:
                detailed_steps += f"\n![{step.image_description or 'Imagem ilustrativa'}]({step.image_ref})\n"
            if step.estimated_time:
                detailed_steps += f"\n*Tempo estimado: {step.estimated_time}*\n"

        # Preparar lista de criterios de qualidade
        quality_criteria_list = "\n".join([f"- [ ] {crit}" for crit in document.quality_criteria]) if document.quality_criteria else "- Nenhum criterio especifico"

        # Preparar secao de troubleshooting
        troubleshooting_section = ""
        for ts in document.troubleshooting:
            causes = "\n".join([f"  - {cause}" for cause in ts.possible_causes])
            solutions = "\n".join([f"  - {sol}" for sol in ts.solutions])
            troubleshooting_section += f"""
### Problema: {ts.problem}

**Possiveis causas:**
{causes}

**Solucoes:**
{solutions}
"""
        if not troubleshooting_section:
            troubleshooting_section = "Nenhum problema comum documentado."

        # Preparar lista de manuais relacionados
        related_manuals_list = "\n".join([f"- {manual}" for manual in document.related_manuals]) if document.related_manuals else "- Nenhum manual relacionado"

        # URLs de integracao
        miro_board_url = document.metadata.get('miro_board_url', '-')
        clickup_task_url = f"https://app.clickup.com/t/{document.clickup_task_id}" if document.clickup_task_id else "-"

        # Contexto para renderizacao
        context = {
            'code': document.code,
            'title': document.title,
            'version': document.version,
            'status': document.status,
            'created_at': self._format_date(document.created_at),
            'updated_at': self._format_date(document.updated_at),
            'pop_reference': document.pop_reference or "-",
            'step_in_pop': document.step_in_pop or "-",
            'activity_id': document.activity_id or "-",
            'target_audience': document.target_audience,
            'objective': document.objective,
            'prerequisites_list': prerequisites_list,
            'safety_requirements_list': safety_requirements_list,
            'materials_table': materials_table,
            'detailed_steps': detailed_steps,
            'quality_criteria_list': quality_criteria_list,
            'troubleshooting_section': troubleshooting_section,
            'related_manuals_list': related_manuals_list,
            'miro_board_url': miro_board_url,
            'clickup_task_url': clickup_task_url,
            'author': document.author or "-",
            'reviewer': document.reviewer or "-",
            'approver': document.approver or "-"
        }

        return self._render_template(template, context)
