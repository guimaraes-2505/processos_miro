"""
Gerador de SIPOC (Supplier, Input, Process, Output, Customer).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.models.process_model import Process
from src.models.hierarchy_model import SIPOC, SIPOCItem, Macroprocess
from src.models.visual_model import VisualDiagram, VisualElement, Position, Size, VisualStyle, ElementColor
from src.generators.base_generator import DocumentGenerator
from src.utils.logger import get_logger

logger = get_logger()


class SIPOCGenerator(DocumentGenerator):
    """
    Gerador de diagramas e documentos SIPOC.
    """

    @property
    def default_template_path(self) -> str:
        return "data/templates/sipoc_template.md"

    def _get_fallback_template(self) -> str:
        return """# SIPOC - {process_name}

**Codigo:** {process_id}

## SIPOC

| Suppliers | Inputs | Process | Outputs | Customers |
|-----------|--------|---------|---------|-----------|
{sipoc_table}

---
**Elaborado por:** {author}
"""

    def generate(self, process: Process, **kwargs) -> SIPOC:
        """
        Gera SIPOC a partir de um processo.

        Args:
            process: Processo fonte
            **kwargs: Argumentos adicionais

        Returns:
            SIPOC gerado
        """
        logger.info(f"Gerando SIPOC para processo: {process.name}")

        # Extrair suppliers
        suppliers = self._extract_suppliers(process)

        # Extrair inputs
        inputs = self._extract_inputs(process)

        # Extrair process steps
        process_steps = self._extract_process_steps(process)

        # Extrair outputs
        outputs = self._extract_outputs(process)

        # Extrair customers
        customers = self._extract_customers(process)

        sipoc = SIPOC(
            suppliers=suppliers,
            inputs=inputs,
            process_steps=process_steps,
            outputs=outputs,
            customers=customers,
            metadata={
                'process_id': process.process_id,
                'process_name': process.name,
                'generated_at': datetime.now().isoformat()
            }
        )

        logger.info(f"SIPOC gerado: S={len(suppliers)}, I={len(inputs)}, P={len(process_steps)}, O={len(outputs)}, C={len(customers)}")
        return sipoc

    def generate_from_macroprocess(self, macroprocess: Macroprocess, **kwargs) -> SIPOC:
        """
        Gera SIPOC a partir de um macroprocesso.

        Args:
            macroprocess: Macroprocesso fonte
            **kwargs: Argumentos adicionais

        Returns:
            SIPOC gerado
        """
        logger.info(f"Gerando SIPOC para macroprocesso: {macroprocess.name}")

        # Se ja tem SIPOC, retornar
        if macroprocess.sipoc:
            return macroprocess.sipoc

        # Criar SIPOC basico
        sipoc = SIPOC(
            suppliers=[],
            inputs=[],
            process_steps=[f"Processo: {pid}" for pid in macroprocess.processes],
            outputs=[],
            customers=[],
            metadata={
                'macroprocess_id': macroprocess.id,
                'macroprocess_name': macroprocess.name,
                'macroprocess_type': macroprocess.type
            }
        )

        return sipoc

    def _extract_suppliers(self, process: Process) -> List[SIPOCItem]:
        """Extrai fornecedores do processo."""
        suppliers = []
        seen = set()

        # Usar suppliers do processo
        for supplier in process.suppliers:
            if supplier not in seen:
                suppliers.append(SIPOCItem(
                    name=supplier,
                    description=None,
                    type='interno'  # Default, pode ser ajustado
                ))
                seen.add(supplier)

        # Extrair de elementos (atores anteriores no fluxo)
        for element in process.elements:
            if element.is_start_event():
                # Fornecedor e quem dispara o inicio
                trigger = element.metadata.get('trigger')
                if trigger and trigger not in seen:
                    suppliers.append(SIPOCItem(
                        name=trigger,
                        description="Dispara o processo",
                        type='externo' if 'cliente' in trigger.lower() else 'interno'
                    ))
                    seen.add(trigger)

        return suppliers

    def _extract_inputs(self, process: Process) -> List[SIPOCItem]:
        """Extrai entradas do processo."""
        inputs = []
        seen = set()

        # Usar inputs do processo
        for inp in process.inputs:
            if inp not in seen:
                inputs.append(SIPOCItem(
                    name=inp,
                    description=None,
                    type=None
                ))
                seen.add(inp)

        # Extrair de elementos
        for element in process.elements:
            for inp in element.inputs:
                if inp not in seen:
                    inputs.append(SIPOCItem(
                        name=inp,
                        description=f"Entrada para {element.name}",
                        type=None
                    ))
                    seen.add(inp)

        return inputs

    def _extract_process_steps(self, process: Process) -> List[str]:
        """Extrai passos principais do processo."""
        steps = []

        for element in process.elements:
            if element.is_task():
                step = element.name
                if element.numbering:
                    step = f"{element.numbering}. {element.name}"
                steps.append(step)

        return steps

    def _extract_outputs(self, process: Process) -> List[SIPOCItem]:
        """Extrai saidas do processo."""
        outputs = []
        seen = set()

        # Usar outputs do processo
        for out in process.outputs:
            if out not in seen:
                outputs.append(SIPOCItem(
                    name=out,
                    description=None,
                    type=None
                ))
                seen.add(out)

        # Extrair de elementos
        for element in process.elements:
            for out in element.outputs:
                if out not in seen:
                    outputs.append(SIPOCItem(
                        name=out,
                        description=f"Saida de {element.name}",
                        type=None
                    ))
                    seen.add(out)

        return outputs

    def _extract_customers(self, process: Process) -> List[SIPOCItem]:
        """Extrai clientes do processo."""
        customers = []
        seen = set()

        # Usar customers do processo
        for customer in process.customers:
            if customer not in seen:
                customers.append(SIPOCItem(
                    name=customer,
                    description=None,
                    type='interno'  # Default
                ))
                seen.add(customer)

        # Extrair de elementos de fim
        for element in process.elements:
            if element.is_end_event():
                recipient = element.metadata.get('recipient')
                if recipient and recipient not in seen:
                    customers.append(SIPOCItem(
                        name=recipient,
                        description="Recebe o resultado do processo",
                        type='externo' if 'cliente' in recipient.lower() else 'interno'
                    ))
                    seen.add(recipient)

        return customers

    def to_visual_diagram(
        self,
        sipoc: SIPOC,
        name: str = "SIPOC",
        **kwargs
    ) -> VisualDiagram:
        """
        Converte SIPOC para diagrama visual (para Miro).

        Args:
            sipoc: SIPOC fonte
            name: Nome do diagrama
            **kwargs: Argumentos adicionais

        Returns:
            VisualDiagram para renderizacao
        """
        logger.info(f"Convertendo SIPOC para diagrama visual: {name}")

        elements = []
        element_id = 0

        # Configuracoes de layout
        column_width = 200
        column_spacing = 50
        row_height = 40
        header_height = 50
        start_x = 100
        start_y = 100

        # Cores por coluna
        colors = {
            'suppliers': ElementColor(fill="#E3F2FD", border="#1976D2"),    # Azul
            'inputs': ElementColor(fill="#E8F5E9", border="#388E3C"),       # Verde
            'process': ElementColor(fill="#FFF9C4", border="#FBC02D"),      # Amarelo
            'outputs': ElementColor(fill="#FCE4EC", border="#C2185B"),      # Rosa
            'customers': ElementColor(fill="#F3E5F5", border="#7B1FA2")     # Roxo
        }

        columns = ['suppliers', 'inputs', 'process', 'outputs', 'customers']
        headers = ['SUPPLIERS', 'INPUTS', 'PROCESS', 'OUTPUTS', 'CUSTOMERS']

        # Criar headers
        for idx, (col, header) in enumerate(zip(columns, headers)):
            x = start_x + idx * (column_width + column_spacing)
            element_id += 1

            elements.append(VisualElement(
                id=f"sipoc_header_{col}",
                element_id=f"header_{element_id}",
                type='rectangle',
                content=header,
                position=Position(x=x, y=start_y),
                size=Size(width=column_width, height=header_height),
                style=VisualStyle(
                    color=colors[col],
                    font_size=14,
                    border_width=2
                )
            ))

        # Determinar numero maximo de linhas
        max_rows = max(
            len(sipoc.suppliers),
            len(sipoc.inputs),
            len(sipoc.process_steps),
            len(sipoc.outputs),
            len(sipoc.customers)
        )

        # Criar celulas
        data = {
            'suppliers': [s.name for s in sipoc.suppliers],
            'inputs': [i.name for i in sipoc.inputs],
            'process': sipoc.process_steps,
            'outputs': [o.name for o in sipoc.outputs],
            'customers': [c.name for c in sipoc.customers]
        }

        for row_idx in range(max_rows):
            y = start_y + header_height + 10 + row_idx * (row_height + 10)

            for col_idx, col in enumerate(columns):
                x = start_x + col_idx * (column_width + column_spacing)
                items = data[col]

                content = items[row_idx] if row_idx < len(items) else ""

                if content:
                    element_id += 1
                    elements.append(VisualElement(
                        id=f"sipoc_{col}_{row_idx}",
                        element_id=f"cell_{element_id}",
                        type='rectangle',
                        content=content,
                        position=Position(x=x, y=y),
                        size=Size(width=column_width, height=row_height),
                        style=VisualStyle(
                            color=ElementColor(
                                fill=colors[col].fill,
                                border=colors[col].border
                            ),
                            font_size=12,
                            border_width=1
                        )
                    ))

        # Calcular dimensoes do diagrama
        total_width = len(columns) * (column_width + column_spacing) + start_x
        total_height = start_y + header_height + max_rows * (row_height + 10) + 50

        diagram = VisualDiagram(
            name=name,
            description=sipoc.metadata.get('process_name', ''),
            elements=elements,
            connectors=[],
            swimlanes=[],
            width=total_width,
            height=total_height
        )

        logger.info(f"Diagrama SIPOC criado com {len(elements)} elementos")
        return diagram

    def to_markdown(self, sipoc: SIPOC, **kwargs) -> str:
        """
        Exporta SIPOC para Markdown.

        Args:
            sipoc: SIPOC a exportar
            **kwargs: Argumentos adicionais

        Returns:
            Conteudo em Markdown
        """
        template = self._load_template()

        # Preparar tabela SIPOC
        max_rows = max(
            len(sipoc.suppliers),
            len(sipoc.inputs),
            len(sipoc.process_steps),
            len(sipoc.outputs),
            len(sipoc.customers)
        )

        sipoc_table = ""
        for i in range(max_rows):
            s = sipoc.suppliers[i].name if i < len(sipoc.suppliers) else ""
            inp = sipoc.inputs[i].name if i < len(sipoc.inputs) else ""
            p = sipoc.process_steps[i] if i < len(sipoc.process_steps) else ""
            o = sipoc.outputs[i].name if i < len(sipoc.outputs) else ""
            c = sipoc.customers[i].name if i < len(sipoc.customers) else ""
            sipoc_table += f"| {s} | {inp} | {p} | {o} | {c} |\n"

        if not sipoc_table:
            sipoc_table = "| - | - | - | - | - |"

        # Preparar tabelas detalhadas
        suppliers_table = ""
        for s in sipoc.suppliers:
            supplier_type = s.type or "-"
            desc = s.description or "-"
            suppliers_table += f"| {s.name} | {supplier_type} | {desc} |\n"

        inputs_table = ""
        for i in sipoc.inputs:
            desc = i.description or "-"
            inputs_table += f"| {i.name} | - | {desc} |\n"

        process_steps_table = ""
        for idx, step in enumerate(sipoc.process_steps, start=1):
            process_steps_table += f"| {idx} | {step} | - |\n"

        outputs_table = ""
        for o in sipoc.outputs:
            desc = o.description or "-"
            outputs_table += f"| {o.name} | - | {desc} |\n"

        customers_table = ""
        for c in sipoc.customers:
            customer_type = c.type or "-"
            desc = c.description or "-"
            customers_table += f"| {c.name} | {customer_type} | {desc} |\n"

        # Contexto
        context = {
            'process_name': sipoc.metadata.get('process_name', 'Processo'),
            'process_id': sipoc.metadata.get('process_id', '-'),
            'macroprocess_name': sipoc.metadata.get('macroprocess_name', '-'),
            'description': sipoc.metadata.get('description', ''),
            'created_at': datetime.now().strftime("%d/%m/%Y"),
            'sipoc_diagram': '',  # Sera preenchido se necessario
            'sipoc_table': sipoc_table,
            'suppliers_table': suppliers_table or "| - | - | - |",
            'inputs_table': inputs_table or "| - | - | - |",
            'process_steps_table': process_steps_table or "| - | - | - |",
            'outputs_table': outputs_table or "| - | - | - |",
            'customers_table': customers_table or "| - | - | - |",
            'related_processes_table': "| - | - | - |",
            'miro_board_url': sipoc.metadata.get('miro_board_url', '-'),
            'pop_reference': sipoc.metadata.get('pop_reference', '-'),
            'author': kwargs.get('author', '-')
        }

        return self._render_template(template, context)

    def to_markdown_table(self, sipoc: SIPOC) -> str:
        """
        Exporta SIPOC como tabela Markdown simples.

        Args:
            sipoc: SIPOC a exportar

        Returns:
            Tabela em Markdown
        """
        max_rows = max(
            len(sipoc.suppliers),
            len(sipoc.inputs),
            len(sipoc.process_steps),
            len(sipoc.outputs),
            len(sipoc.customers),
            1
        )

        table = "| Suppliers | Inputs | Process | Outputs | Customers |\n"
        table += "|-----------|--------|---------|---------|----------|\n"

        for i in range(max_rows):
            s = sipoc.suppliers[i].name if i < len(sipoc.suppliers) else ""
            inp = sipoc.inputs[i].name if i < len(sipoc.inputs) else ""
            p = sipoc.process_steps[i] if i < len(sipoc.process_steps) else ""
            o = sipoc.outputs[i].name if i < len(sipoc.outputs) else ""
            c = sipoc.customers[i].name if i < len(sipoc.customers) else ""
            table += f"| {s} | {inp} | {p} | {o} | {c} |\n"

        return table
