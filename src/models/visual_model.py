"""
Modelo de elementos visuais para representação no Miro.
Usa formas simples e intuitivas (não BPMN complexo).
"""

from typing import Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field


class Position(BaseModel):
    """Posição de um elemento visual (coordenadas x, y)."""
    x: float = Field(..., description="Coordenada X (horizontal)")
    y: float = Field(..., description="Coordenada Y (vertical)")


class Size(BaseModel):
    """Tamanho de um elemento visual."""
    width: float = Field(..., description="Largura em pixels")
    height: float = Field(..., description="Altura em pixels")


class Color(BaseModel):
    """Cor de um elemento visual."""
    fill: str = Field(..., description="Cor de preenchimento (hex)")
    border: str = Field(..., description="Cor da borda (hex)")
    text: str = Field(default="#1a1a1a", description="Cor do texto (hex)")


class VisualStyle(BaseModel):
    """Estilo visual de um elemento."""
    color: Color
    border_width: int = Field(default=2, description="Espessura da borda")
    font_size: int = Field(default=14, description="Tamanho da fonte")
    font_weight: Literal['normal', 'bold'] = Field(default='normal')
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)


class VisualElement(BaseModel):
    """
    Elemento visual genérico.
    Representa uma forma no Miro (retângulo, círculo, diamante, sticky note).
    """
    id: str = Field(..., description="ID único do elemento visual")
    element_id: str = Field(..., description="ID do ProcessElement original")
    type: Literal['rectangle', 'circle', 'diamond', 'sticky_note', 'text'] = Field(
        ...,
        description="Tipo de forma visual"
    )
    content: str = Field(..., description="Texto exibido no elemento")
    position: Position = Field(..., description="Posição no canvas")
    size: Size = Field(..., description="Tamanho do elemento")
    style: VisualStyle = Field(..., description="Estilo visual")
    layer: int = Field(default=0, description="Camada (Z-index)")
    metadata: Dict = Field(default_factory=dict)

    def get_center(self) -> Position:
        """Retorna o centro do elemento."""
        return Position(
            x=self.position.x + self.size.width / 2,
            y=self.position.y + self.size.height / 2
        )

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Retorna os limites do elemento (x_min, y_min, x_max, y_max)."""
        return (
            self.position.x,
            self.position.y,
            self.position.x + self.size.width,
            self.position.y + self.size.height
        )


class Connector(BaseModel):
    """
    Conector visual entre elementos (seta).
    """
    id: str = Field(..., description="ID único do conector")
    flow_id: Optional[str] = Field(None, description="ID do ProcessFlow original")
    from_element: str = Field(..., description="ID do elemento visual de origem")
    to_element: str = Field(..., description="ID do elemento visual de destino")
    label: Optional[str] = Field(None, description="Texto na seta (para condições)")
    style: Literal['solid', 'dashed'] = Field(default='solid')
    color: str = Field(default="#000000", description="Cor da linha")
    width: int = Field(default=2, description="Espessura da linha")
    arrow_end: bool = Field(default=True, description="Mostrar seta no final")
    metadata: Dict = Field(default_factory=dict)


class Swimlane(BaseModel):
    """
    Swimlane (raia) para agrupar elementos por responsável.
    """
    id: str = Field(..., description="ID único da swimlane")
    actor: str = Field(..., description="Nome do responsável/ator")
    position: Position = Field(..., description="Posição da swimlane")
    size: Size = Field(..., description="Tamanho da swimlane")
    color: Color = Field(..., description="Cores da swimlane")
    elements: List[str] = Field(
        default_factory=list,
        description="IDs dos elementos visuais dentro desta lane"
    )
    label_vertical: bool = Field(
        default=True,
        description="Se True, label do ator fica na vertical à esquerda"
    )
    label_width: int = Field(
        default=60,
        description="Largura da barra do label do ator"
    )


class VisualDiagram(BaseModel):
    """
    Diagrama visual completo.
    Representa um processo como elementos visuais no Miro.
    """
    name: str = Field(..., description="Nome do diagrama")
    description: str = Field(default="", description="Descrição do diagrama")
    elements: List[VisualElement] = Field(
        default_factory=list,
        description="Elementos visuais do diagrama"
    )
    connectors: List[Connector] = Field(
        default_factory=list,
        description="Conectores entre elementos"
    )
    swimlanes: List[Swimlane] = Field(
        default_factory=list,
        description="Swimlanes (raias por responsável)"
    )
    canvas_size: Size = Field(
        default=Size(width=4000, height=3000),
        description="Tamanho do canvas"
    )
    metadata: Dict = Field(default_factory=dict)

    def get_element(self, element_id: str) -> Optional[VisualElement]:
        """Busca um elemento visual pelo ID."""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None

    def get_swimlane_for_actor(self, actor: str) -> Optional[Swimlane]:
        """Busca swimlane de um ator."""
        for lane in self.swimlanes:
            if lane.actor == actor:
                return lane
        return None

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Retorna os limites do diagrama baseado nos elementos.
        Returns: (x_min, y_min, x_max, y_max)
        """
        if not self.elements:
            return (0, 0, 0, 0)

        x_min = min(e.position.x for e in self.elements)
        y_min = min(e.position.y for e in self.elements)
        x_max = max(e.position.x + e.size.width for e in self.elements)
        y_max = max(e.position.y + e.size.height for e in self.elements)

        return (x_min, y_min, x_max, y_max)


# Estilos visuais pré-definidos para cada tipo de elemento
VISUAL_STYLES = {
    'task': VisualStyle(
        color=Color(
            fill="#E3F2FD",      # Azul claro
            border="#1976D2",    # Azul escuro
            text="#1a1a1a"
        ),
        border_width=2,
        font_size=14,
        font_weight='normal'
    ),
    'gateway': VisualStyle(
        color=Color(
            fill="#FFF9C4",      # Amarelo claro
            border="#F57F17",    # Amarelo escuro
            text="#1a1a1a"
        ),
        border_width=2,
        font_size=13,
        font_weight='bold'
    ),
    'event_start': VisualStyle(
        color=Color(
            fill="#C8E6C9",      # Verde claro
            border="#388E3C",    # Verde escuro
            text="#1a1a1a"
        ),
        border_width=3,
        font_size=13,
        font_weight='bold'
    ),
    'event_end': VisualStyle(
        color=Color(
            fill="#FFCDD2",      # Vermelho claro
            border="#D32F2F",    # Vermelho escuro
            text="#1a1a1a"
        ),
        border_width=4,
        font_size=13,
        font_weight='bold'
    ),
    'annotation': VisualStyle(
        color=Color(
            fill="#FFF9C4",      # Amarelo (sticky note)
            border="#FFD54F",    # Amarelo claro
            text="#1a1a1a"
        ),
        border_width=0,
        font_size=12,
        font_weight='normal'
    ),
    'swimlane': Color(
        fill="#F5F5F5",          # Cinza muito claro
        border="#BDBDBD",        # Cinza médio
        text="#424242"           # Cinza escuro
    )
}

# Tamanhos padrão para cada tipo de elemento
ELEMENT_SIZES = {
    'task': Size(width=160, height=80),
    'gateway': Size(width=80, height=80),
    'event_start': Size(width=50, height=50),
    'event_end': Size(width=50, height=50),
    'annotation': Size(width=200, height=100)
}


def get_visual_style(element_type: str, event_type: Optional[str] = None) -> VisualStyle:
    """
    Retorna o estilo visual para um tipo de elemento.

    Args:
        element_type: Tipo do elemento (task, gateway, event, annotation)
        event_type: Subtipo do evento (start, end) se aplicável

    Returns:
        VisualStyle apropriado
    """
    if element_type == 'event' and event_type:
        style_key = f'event_{event_type}'
        if style_key in VISUAL_STYLES:
            return VISUAL_STYLES[style_key].model_copy()

    if element_type in VISUAL_STYLES:
        return VISUAL_STYLES[element_type].model_copy()

    # Fallback: estilo padrão
    return VisualStyle(
        color=Color(fill="#FFFFFF", border="#000000", text="#1a1a1a"),
        border_width=2,
        font_size=14
    )


def get_element_size(element_type: str) -> Size:
    """
    Retorna o tamanho padrão para um tipo de elemento.

    Args:
        element_type: Tipo do elemento

    Returns:
        Size apropriado
    """
    if element_type in ELEMENT_SIZES:
        return ELEMENT_SIZES[element_type].model_copy()

    # Fallback: tamanho padrão
    return Size(width=120, height=60)
