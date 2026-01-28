"""
Layout para Cadeia de Valor no Miro.
Organiza macroprocessos em tres faixas: Primarios, Apoio e Gestao.
"""

from typing import Dict, List, Optional, Tuple

from src.models.hierarchy_model import ValueChain, Macroprocess, OrganizationHierarchy
from src.models.visual_model import (
    VisualDiagram, VisualElement, Connector, Swimlane,
    Position, Size, VisualStyle, ElementColor
)
from src.utils.logger import get_logger

logger = get_logger()


class ValueChainLayout:
    """
    Gerador de layout para Cadeia de Valor.
    Segue o modelo de Porter com macroprocessos primarios,
    de apoio e de gestao.
    """

    # Configuracoes de layout
    FRAME_PADDING = 30
    FRAME_HEADER_HEIGHT = 50
    MACRO_WIDTH = 180
    MACRO_HEIGHT = 80
    MACRO_SPACING_X = 40
    MACRO_SPACING_Y = 30
    START_X = 100
    START_Y = 100

    # Cores por tipo de macroprocesso
    COLORS = {
        'primario': ElementColor(fill="#E3F2FD", border="#1976D2"),    # Azul
        'apoio': ElementColor(fill="#E8F5E9", border="#388E3C"),       # Verde
        'gestao': ElementColor(fill="#FFF3E0", border="#F57C00"),      # Laranja
        'frame_primario': ElementColor(fill="#BBDEFB", border="#1976D2"),
        'frame_apoio': ElementColor(fill="#C8E6C9", border="#388E3C"),
        'frame_gestao': ElementColor(fill="#FFE0B2", border="#F57C00"),
        'header': ElementColor(fill="#FAFAFA", border="#9E9E9E"),
        'title': ElementColor(fill="#37474F", border="#37474F")
    }

    def __init__(
        self,
        macro_width: int = None,
        macro_height: int = None,
        macro_spacing_x: int = None,
        macro_spacing_y: int = None
    ):
        """
        Inicializa o gerador de layout.

        Args:
            macro_width: Largura dos macroprocessos
            macro_height: Altura dos macroprocessos
            macro_spacing_x: Espacamento horizontal
            macro_spacing_y: Espacamento vertical
        """
        self.macro_width = macro_width or self.MACRO_WIDTH
        self.macro_height = macro_height or self.MACRO_HEIGHT
        self.macro_spacing_x = macro_spacing_x or self.MACRO_SPACING_X
        self.macro_spacing_y = macro_spacing_y or self.MACRO_SPACING_Y

    def create_layout(
        self,
        value_chain: ValueChain,
        macroprocesses: Dict[str, Macroprocess],
        **kwargs
    ) -> VisualDiagram:
        """
        Cria layout visual para Cadeia de Valor.

        Args:
            value_chain: Cadeia de Valor
            macroprocesses: Dict de macroprocessos (id -> Macroprocess)
            **kwargs: Argumentos adicionais

        Returns:
            VisualDiagram com layout da Cadeia de Valor
        """
        logger.info(f"Criando layout de Cadeia de Valor: {value_chain.name}")

        elements = []
        connectors = []

        # Separar macroprocessos por tipo
        primarios = [macroprocesses[mid] for mid in value_chain.primary_macroprocesses if mid in macroprocesses]
        apoio = [macroprocesses[mid] for mid in value_chain.support_macroprocesses if mid in macroprocesses]
        gestao = [macroprocesses[mid] for mid in value_chain.management_macroprocesses if mid in macroprocesses]

        # Calcular dimensoes
        max_count = max(len(primarios), len(apoio), len(gestao), 1)
        frame_width = max_count * (self.macro_width + self.macro_spacing_x) + self.FRAME_PADDING * 2
        frame_height = self.macro_height + self.FRAME_HEADER_HEIGHT + self.FRAME_PADDING * 2

        current_y = self.START_Y

        # Titulo da Cadeia de Valor
        title_element = self._create_title(value_chain.name, frame_width)
        elements.append(title_element)
        current_y += 80

        # Frame de Macroprocessos Primarios
        primary_elements, primary_connectors = self._create_frame_with_macros(
            "MACROPROCESSOS PRIMARIOS",
            primarios,
            self.START_X,
            current_y,
            frame_width,
            frame_height,
            'primario'
        )
        elements.extend(primary_elements)
        connectors.extend(primary_connectors)
        current_y += frame_height + self.macro_spacing_y

        # Frame de Macroprocessos de Apoio
        support_elements, support_connectors = self._create_frame_with_macros(
            "MACROPROCESSOS DE APOIO",
            apoio,
            self.START_X,
            current_y,
            frame_width,
            frame_height,
            'apoio'
        )
        elements.extend(support_elements)
        connectors.extend(support_connectors)
        current_y += frame_height + self.macro_spacing_y

        # Frame de Macroprocessos de Gestao
        management_elements, management_connectors = self._create_frame_with_macros(
            "MACROPROCESSOS DE GESTAO",
            gestao,
            self.START_X,
            current_y,
            frame_width,
            frame_height,
            'gestao'
        )
        elements.extend(management_elements)
        connectors.extend(management_connectors)
        current_y += frame_height + self.macro_spacing_y

        # Calcular dimensoes totais
        total_width = frame_width + self.START_X * 2
        total_height = current_y + 50

        diagram = VisualDiagram(
            name=value_chain.name,
            description=value_chain.description,
            elements=elements,
            connectors=connectors,
            swimlanes=[],
            width=total_width,
            height=total_height,
            metadata={
                'type': 'value_chain',
                'organization': value_chain.organization,
                'mission': value_chain.mission,
                'vision': value_chain.vision
            }
        )

        logger.info(f"Layout criado com {len(elements)} elementos e {len(connectors)} conectores")
        return diagram

    def _create_title(self, title: str, width: float) -> VisualElement:
        """Cria elemento de titulo."""
        return VisualElement(
            id="vc_title",
            element_id="title",
            type='rectangle',
            content=f"CADEIA DE VALOR\n{title}",
            position=Position(x=self.START_X, y=self.START_Y),
            size=Size(width=width, height=60),
            style=VisualStyle(
                color=self.COLORS['title'],
                font_size=18,
                border_width=2
            )
        )

    def _create_frame_with_macros(
        self,
        frame_title: str,
        macroprocesses: List[Macroprocess],
        x: float,
        y: float,
        width: float,
        height: float,
        macro_type: str
    ) -> Tuple[List[VisualElement], List[Connector]]:
        """
        Cria frame com macroprocessos.

        Returns:
            Tuple de (elementos, conectores)
        """
        elements = []
        connectors = []

        frame_id = f"frame_{macro_type}"
        frame_color = self.COLORS[f'frame_{macro_type}']
        macro_color = self.COLORS[macro_type]

        # Frame de fundo
        elements.append(VisualElement(
            id=frame_id,
            element_id=frame_id,
            type='rectangle',
            content="",
            position=Position(x=x, y=y),
            size=Size(width=width, height=height),
            style=VisualStyle(
                color=frame_color,
                font_size=12,
                border_width=2
            )
        ))

        # Titulo do frame
        elements.append(VisualElement(
            id=f"{frame_id}_title",
            element_id=f"{frame_id}_title",
            type='rectangle',
            content=frame_title,
            position=Position(x=x + self.FRAME_PADDING, y=y + 10),
            size=Size(width=width - self.FRAME_PADDING * 2, height=self.FRAME_HEADER_HEIGHT - 20),
            style=VisualStyle(
                color=self.COLORS['header'],
                font_size=14,
                border_width=1
            )
        ))

        # Macroprocessos
        macro_y = y + self.FRAME_HEADER_HEIGHT + self.FRAME_PADDING
        prev_macro_id = None

        for idx, macro in enumerate(macroprocesses):
            macro_x = x + self.FRAME_PADDING + idx * (self.macro_width + self.macro_spacing_x)

            macro_element = VisualElement(
                id=macro.id,
                element_id=macro.id,
                type='rectangle',
                content=macro.name,
                position=Position(x=macro_x, y=macro_y),
                size=Size(width=self.macro_width, height=self.macro_height),
                style=VisualStyle(
                    color=macro_color,
                    font_size=12,
                    border_width=2
                ),
                metadata={
                    'macro_id': macro.id,
                    'macro_type': macro.type,
                    'clickable': True,
                    'link_to_board': True
                }
            )
            elements.append(macro_element)

            # Conectar macroprocessos primarios sequencialmente
            if macro_type == 'primario' and prev_macro_id:
                connectors.append(Connector(
                    id=f"conn_{prev_macro_id}_{macro.id}",
                    from_element=prev_macro_id,
                    to_element=macro.id,
                    label="",
                    color="#1976D2",
                    width=2,
                    style="solid",
                    arrow_end=True
                ))

            prev_macro_id = macro.id

        return elements, connectors

    def create_layout_from_hierarchy(
        self,
        hierarchy: OrganizationHierarchy,
        **kwargs
    ) -> VisualDiagram:
        """
        Cria layout a partir de hierarquia organizacional completa.

        Args:
            hierarchy: Hierarquia organizacional
            **kwargs: Argumentos adicionais

        Returns:
            VisualDiagram
        """
        if not hierarchy.value_chain:
            raise ValueError("Hierarquia nao possui Cadeia de Valor definida")

        return self.create_layout(
            hierarchy.value_chain,
            hierarchy.macroprocesses,
            **kwargs
        )


def create_value_chain_diagram(
    value_chain: ValueChain,
    macroprocesses: Dict[str, Macroprocess],
    **kwargs
) -> VisualDiagram:
    """
    Funcao utilitaria para criar diagrama de Cadeia de Valor.

    Args:
        value_chain: Cadeia de Valor
        macroprocesses: Dict de macroprocessos
        **kwargs: Argumentos adicionais

    Returns:
        VisualDiagram
    """
    layout = ValueChainLayout(**kwargs)
    return layout.create_layout(value_chain, macroprocesses)
