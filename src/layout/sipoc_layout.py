"""
Layout para SIPOC no Miro.
Organiza elementos em 5 colunas: Suppliers, Inputs, Process, Outputs, Customers.
"""

from typing import Dict, List, Optional, Tuple

from src.models.hierarchy_model import SIPOC, SIPOCItem
from src.models.visual_model import (
    VisualDiagram, VisualElement, Connector,
    Position, Size, VisualStyle, ElementColor
)
from src.utils.logger import get_logger

logger = get_logger()


class SIPOCLayout:
    """
    Gerador de layout para diagramas SIPOC.
    """

    # Configuracoes de layout
    COLUMN_WIDTH = 200
    COLUMN_SPACING = 30
    ROW_HEIGHT = 50
    ROW_SPACING = 10
    HEADER_HEIGHT = 60
    START_X = 100
    START_Y = 100
    TITLE_HEIGHT = 50

    # Cores por coluna SIPOC
    COLORS = {
        'suppliers': ElementColor(fill="#E3F2FD", border="#1976D2"),    # Azul
        'inputs': ElementColor(fill="#E8F5E9", border="#388E3C"),       # Verde
        'process': ElementColor(fill="#FFF9C4", border="#FBC02D"),      # Amarelo
        'outputs': ElementColor(fill="#FCE4EC", border="#C2185B"),      # Rosa
        'customers': ElementColor(fill="#F3E5F5", border="#7B1FA2"),    # Roxo
        'header': ElementColor(fill="#37474F", border="#37474F"),       # Cinza escuro
        'title': ElementColor(fill="#263238", border="#263238")         # Cinza mais escuro
    }

    HEADERS = ['SUPPLIERS', 'INPUTS', 'PROCESS', 'OUTPUTS', 'CUSTOMERS']
    COLUMNS = ['suppliers', 'inputs', 'process', 'outputs', 'customers']

    def __init__(
        self,
        column_width: int = None,
        column_spacing: int = None,
        row_height: int = None
    ):
        """
        Inicializa o gerador de layout.

        Args:
            column_width: Largura das colunas
            column_spacing: Espacamento entre colunas
            row_height: Altura das linhas
        """
        self.column_width = column_width or self.COLUMN_WIDTH
        self.column_spacing = column_spacing or self.COLUMN_SPACING
        self.row_height = row_height or self.ROW_HEIGHT

    def create_layout(
        self,
        sipoc: SIPOC,
        title: str = "SIPOC",
        **kwargs
    ) -> VisualDiagram:
        """
        Cria layout visual para SIPOC.

        Args:
            sipoc: SIPOC a renderizar
            title: Titulo do diagrama
            **kwargs: Argumentos adicionais

        Returns:
            VisualDiagram com layout SIPOC
        """
        logger.info(f"Criando layout SIPOC: {title}")

        elements = []
        connectors = []

        # Preparar dados
        data = {
            'suppliers': [s.name for s in sipoc.suppliers],
            'inputs': [i.name for i in sipoc.inputs],
            'process': sipoc.process_steps,
            'outputs': [o.name for o in sipoc.outputs],
            'customers': [c.name for c in sipoc.customers]
        }

        # Calcular numero maximo de linhas
        max_rows = max(len(v) for v in data.values()) if any(data.values()) else 1

        # Calcular dimensoes totais
        total_width = len(self.COLUMNS) * (self.column_width + self.column_spacing) - self.column_spacing
        total_height = (
            self.TITLE_HEIGHT +
            self.HEADER_HEIGHT +
            max_rows * (self.row_height + self.ROW_SPACING) +
            self.START_Y
        )

        current_y = self.START_Y

        # Titulo
        title_element = self._create_title(title, total_width)
        elements.append(title_element)
        current_y += self.TITLE_HEIGHT + 20

        # Headers das colunas
        header_elements = self._create_headers(current_y)
        elements.extend(header_elements)
        current_y += self.HEADER_HEIGHT + 10

        # Celulas de dados
        cell_elements = self._create_cells(data, current_y, max_rows)
        elements.extend(cell_elements)

        # Conectores entre colunas (setas de fluxo)
        flow_connectors = self._create_flow_connectors(current_y)
        connectors.extend(flow_connectors)

        diagram = VisualDiagram(
            name=title,
            description=sipoc.metadata.get('process_name', ''),
            elements=elements,
            connectors=connectors,
            swimlanes=[],
            width=total_width + self.START_X * 2,
            height=total_height + 50,
            metadata={
                'type': 'sipoc',
                'process_id': sipoc.metadata.get('process_id'),
                'process_name': sipoc.metadata.get('process_name')
            }
        )

        logger.info(f"Layout SIPOC criado com {len(elements)} elementos")
        return diagram

    def _create_title(self, title: str, width: float) -> VisualElement:
        """Cria elemento de titulo."""
        return VisualElement(
            id="sipoc_title",
            element_id="title",
            type='rectangle',
            content=title,
            position=Position(x=self.START_X, y=self.START_Y),
            size=Size(width=width, height=self.TITLE_HEIGHT),
            style=VisualStyle(
                color=self.COLORS['title'],
                font_size=18,
                border_width=2
            )
        )

    def _create_headers(self, start_y: float) -> List[VisualElement]:
        """Cria headers das colunas."""
        elements = []

        for idx, (col, header) in enumerate(zip(self.COLUMNS, self.HEADERS)):
            x = self.START_X + idx * (self.column_width + self.column_spacing)

            elements.append(VisualElement(
                id=f"sipoc_header_{col}",
                element_id=f"header_{col}",
                type='rectangle',
                content=header,
                position=Position(x=x, y=start_y),
                size=Size(width=self.column_width, height=self.HEADER_HEIGHT),
                style=VisualStyle(
                    color=self.COLORS['header'],
                    font_size=14,
                    border_width=2
                )
            ))

        return elements

    def _create_cells(
        self,
        data: Dict[str, List[str]],
        start_y: float,
        max_rows: int
    ) -> List[VisualElement]:
        """Cria celulas de dados."""
        elements = []

        for row_idx in range(max_rows):
            y = start_y + row_idx * (self.row_height + self.ROW_SPACING)

            for col_idx, col in enumerate(self.COLUMNS):
                x = self.START_X + col_idx * (self.column_width + self.column_spacing)
                items = data[col]

                content = items[row_idx] if row_idx < len(items) else ""

                if content:
                    elements.append(VisualElement(
                        id=f"sipoc_{col}_{row_idx}",
                        element_id=f"cell_{col}_{row_idx}",
                        type='rectangle',
                        content=content,
                        position=Position(x=x, y=y),
                        size=Size(width=self.column_width, height=self.row_height),
                        style=VisualStyle(
                            color=self.COLORS[col],
                            font_size=11,
                            border_width=1
                        )
                    ))

        return elements

    def _create_flow_connectors(self, start_y: float) -> List[Connector]:
        """Cria conectores de fluxo entre colunas."""
        connectors = []

        # Conectores entre headers (representando fluxo S -> I -> P -> O -> C)
        for idx in range(len(self.COLUMNS) - 1):
            from_col = self.COLUMNS[idx]
            to_col = self.COLUMNS[idx + 1]

            connectors.append(Connector(
                id=f"flow_{from_col}_{to_col}",
                from_element=f"sipoc_header_{from_col}",
                to_element=f"sipoc_header_{to_col}",
                label="",
                color="#757575",
                width=2,
                style="solid",
                arrow_end=True
            ))

        return connectors


class MacroprocessSIPOCLayout(SIPOCLayout):
    """
    Layout SIPOC especializado para macroprocessos.
    Inclui secao adicional para processos relacionados.
    """

    def create_layout_with_processes(
        self,
        sipoc: SIPOC,
        title: str,
        related_processes: List[Dict[str, str]] = None,
        **kwargs
    ) -> VisualDiagram:
        """
        Cria layout SIPOC com lista de processos relacionados.

        Args:
            sipoc: SIPOC a renderizar
            title: Titulo do diagrama
            related_processes: Lista de processos relacionados
            **kwargs: Argumentos adicionais

        Returns:
            VisualDiagram
        """
        # Criar layout base
        diagram = self.create_layout(sipoc, title, **kwargs)

        if not related_processes:
            return diagram

        # Adicionar secao de processos relacionados
        last_element = diagram.elements[-1] if diagram.elements else None
        if last_element:
            start_y = last_element.position.y + last_element.size.height + 50
        else:
            start_y = self.START_Y + 400

        # Header da secao
        total_width = len(self.COLUMNS) * (self.column_width + self.column_spacing) - self.column_spacing

        diagram.elements.append(VisualElement(
            id="related_processes_header",
            element_id="related_header",
            type='rectangle',
            content="PROCESSOS RELACIONADOS",
            position=Position(x=self.START_X, y=start_y),
            size=Size(width=total_width, height=40),
            style=VisualStyle(
                color=self.COLORS['header'],
                font_size=12,
                border_width=1
            )
        ))

        # Cards de processos
        card_width = 200
        card_height = 60
        card_spacing = 20
        cards_per_row = int(total_width / (card_width + card_spacing))

        for idx, proc in enumerate(related_processes):
            row = idx // cards_per_row
            col = idx % cards_per_row

            x = self.START_X + col * (card_width + card_spacing)
            y = start_y + 50 + row * (card_height + card_spacing)

            diagram.elements.append(VisualElement(
                id=f"related_proc_{idx}",
                element_id=proc.get('id', f'proc_{idx}'),
                type='rectangle',
                content=f"{proc.get('code', '')}\n{proc.get('name', '')}",
                position=Position(x=x, y=y),
                size=Size(width=card_width, height=card_height),
                style=VisualStyle(
                    color=ElementColor(fill="#E0E0E0", border="#9E9E9E"),
                    font_size=10,
                    border_width=1
                ),
                metadata={
                    'process_id': proc.get('id'),
                    'clickable': True,
                    'link_to_board': True
                }
            ))

        # Atualizar altura do diagrama
        diagram.height = start_y + 50 + ((len(related_processes) // cards_per_row) + 1) * (card_height + card_spacing) + 50

        return diagram


def create_sipoc_diagram(
    sipoc: SIPOC,
    title: str = "SIPOC",
    **kwargs
) -> VisualDiagram:
    """
    Funcao utilitaria para criar diagrama SIPOC.

    Args:
        sipoc: SIPOC a renderizar
        title: Titulo do diagrama
        **kwargs: Argumentos adicionais

    Returns:
        VisualDiagram
    """
    layout = SIPOCLayout(**kwargs)
    return layout.create_layout(sipoc, title)
