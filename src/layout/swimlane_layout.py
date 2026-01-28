"""
Layout de swimlanes (raias por responsável).
Organiza elementos verticalmente por ator/responsável.
"""

from typing import Dict, List
from config.settings import get_settings
from src.models.process_model import Process
from src.models.visual_model import (
    VisualDiagram,
    Swimlane,
    Position,
    Size,
    VISUAL_STYLES
)
from src.utils.logger import get_logger

logger = get_logger()


class SwimlaneLayoutEngine:
    """
    Engine de layout para swimlanes.
    Calcula posições e tamanhos de swimlanes baseado nos atores.
    """

    def __init__(self):
        settings = get_settings()
        self.swimlane_height = settings.SWIMLANE_HEIGHT
        self.swimlane_spacing = 0  # Swimlanes coladas (sem espaço entre elas)
        self.margin_top = 100  # Margem superior
        self.margin_left = 50  # Margem esquerda
        self.label_width = 60  # Largura da barra vertical do label do ator
        self.label_vertical = True  # Label do ator na vertical

    def calculate_swimlanes(
        self,
        diagram: VisualDiagram,
        process: Process
    ) -> List[Swimlane]:
        """
        Calcula swimlanes para o diagrama baseado nos atores do processo.

        Args:
            diagram: Diagrama visual (com elementos já convertidos)
            process: Processo original (para obter atores)

        Returns:
            Lista de Swimlanes configuradas
        """
        logger.info("Calculating swimlane layout...")

        actors = process.actors if process.actors else ["Processo Geral"]
        swimlanes = []

        # Calcular largura total necessária
        # Vamos usar a largura do canvas menos margens
        canvas_width = diagram.canvas_size.width
        swimlane_width = canvas_width - self.margin_left - 50  # 50 = margem direita

        # Criar swimlane para cada ator
        current_y = self.margin_top

        for idx, actor in enumerate(actors):
            # Criar swimlane
            swimlane = Swimlane(
                id=f"swimlane_{idx}",
                actor=actor,
                position=Position(x=self.margin_left, y=current_y),
                size=Size(width=swimlane_width, height=self.swimlane_height),
                color=VISUAL_STYLES['swimlane'],
                elements=[],
                label_vertical=self.label_vertical,
                label_width=self.label_width
            )

            # Atribuir elementos a esta swimlane
            for element in diagram.elements:
                element_actor = element.metadata.get('actor')
                if element_actor == actor:
                    swimlane.elements.append(element.id)

            swimlanes.append(swimlane)
            logger.debug(
                f"Created swimlane for '{actor}': "
                f"y={current_y}, height={self.swimlane_height}, "
                f"elements={len(swimlane.elements)}"
            )

            # Próxima posição Y
            current_y += self.swimlane_height + self.swimlane_spacing

        # Adicionar swimlane para elementos sem ator (eventos, etc)
        elements_without_actor = [
            e for e in diagram.elements
            if not e.metadata.get('actor')
        ]

        if elements_without_actor:
            swimlane = Swimlane(
                id=f"swimlane_shared",
                actor="Eventos",
                position=Position(x=self.margin_left, y=current_y),
                size=Size(width=swimlane_width, height=self.swimlane_height),
                color=VISUAL_STYLES['swimlane'],
                elements=[e.id for e in elements_without_actor],
                label_vertical=self.label_vertical,
                label_width=self.label_width
            )
            swimlanes.append(swimlane)
            logger.debug(
                f"Created shared swimlane for {len(elements_without_actor)} elements without actor"
            )

        logger.info(f"Created {len(swimlanes)} swimlanes")
        return swimlanes

    def get_swimlane_center_y(self, swimlane: Swimlane) -> float:
        """
        Retorna a coordenada Y do centro de uma swimlane.

        Args:
            swimlane: Swimlane

        Returns:
            Coordenada Y do centro
        """
        return swimlane.position.y + swimlane.size.height / 2

    def get_element_lane_bounds(self, swimlane: Swimlane) -> Dict[str, float]:
        """
        Retorna os limites da área utilizável dentro da swimlane.

        Args:
            swimlane: Swimlane

        Returns:
            Dicionário com x_min, x_max, y_min, y_max
        """
        padding = 20  # Padding interno da swimlane

        return {
            'x_min': swimlane.position.x + self.label_width + padding,
            'x_max': swimlane.position.x + swimlane.size.width - padding,
            'y_min': swimlane.position.y + padding,
            'y_max': swimlane.position.y + swimlane.size.height - padding
        }


def apply_swimlane_layout(diagram: VisualDiagram, process: Process) -> VisualDiagram:
    """
    Aplica layout de swimlanes ao diagrama.

    Args:
        diagram: Diagrama visual
        process: Processo original

    Returns:
        Diagrama com swimlanes configuradas
    """
    engine = SwimlaneLayoutEngine()
    swimlanes = engine.calculate_swimlanes(diagram, process)

    # Atualizar diagrama
    diagram.swimlanes = swimlanes

    return diagram
