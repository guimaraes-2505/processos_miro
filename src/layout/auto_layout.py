"""
Layout automático de elementos no diagrama.
Posiciona elementos em grid horizontal (left-to-right) dentro de swimlanes.
"""

from collections import defaultdict, deque
from typing import Dict, List

from config.settings import get_settings
from src.models.process_model import Process
from src.models.visual_model import VisualDiagram, VisualElement, Position, Swimlane
from src.utils.logger import get_logger

logger = get_logger()


class AutoLayoutEngine:
    """
    Engine de layout automático.
    Usa algoritmo de ranking por níveis (layered graph drawing).
    """

    def __init__(self):
        settings = get_settings()
        self.element_spacing_x = settings.ELEMENT_SPACING_X
        self.element_spacing_y = settings.ELEMENT_SPACING_Y
        self.start_x = 250  # Posição X inicial (após label da swimlane)

    def _build_graph(self, diagram: VisualDiagram) -> Dict[str, List[str]]:
        """
        Constrói grafo de adjacência a partir dos conectores.

        Args:
            diagram: Diagrama visual

        Returns:
            Dicionário: element_id -> [connected_element_ids]
        """
        graph = defaultdict(list)

        for connector in diagram.connectors:
            graph[connector.from_element].append(connector.to_element)

        return dict(graph)

    def _topological_sort(self, graph: Dict[str, List[str]], elements: List[VisualElement]) -> List[List[str]]:
        """
        Ordena elementos em níveis (ranks) usando BFS.
        Elementos no mesmo nível podem ser posicionados na mesma coluna.

        Args:
            graph: Grafo de adjacência
            elements: Lista de elementos visuais

        Returns:
            Lista de níveis, onde cada nível é uma lista de element_ids
        """
        # Calcular grau de entrada de cada nó
        in_degree = {elem.id: 0 for elem in elements}

        for from_id, to_ids in graph.items():
            for to_id in to_ids:
                if to_id in in_degree:
                    in_degree[to_id] += 1

        # Encontrar nós raiz (grau de entrada 0)
        roots = [elem_id for elem_id, degree in in_degree.items() if degree == 0]

        if not roots:
            logger.warning("No root nodes found, using first element as root")
            roots = [elements[0].id] if elements else []

        # BFS para criar níveis
        levels = []
        visited = set()
        queue = deque([(node, 0) for node in roots])  # (node_id, level)
        max_level = 0

        # Mapear nós para seus níveis
        node_levels: Dict[str, int] = {}

        while queue:
            node_id, level = queue.popleft()

            if node_id in visited:
                continue

            visited.add(node_id)
            node_levels[node_id] = level
            max_level = max(max_level, level)

            # Adicionar próximos nós
            if node_id in graph:
                for next_node in graph[node_id]:
                    if next_node not in visited:
                        queue.append((next_node, level + 1))

        # Organizar em níveis
        levels = [[] for _ in range(max_level + 1)]
        for node_id, level in node_levels.items():
            levels[level].append(node_id)

        # Adicionar nós não visitados (órfãos) ao último nível
        orphans = [elem.id for elem in elements if elem.id not in visited]
        if orphans:
            logger.warning(f"Found {len(orphans)} orphan elements, adding to last level")
            levels.append(orphans)

        logger.debug(f"Created {len(levels)} levels: {[len(lvl) for lvl in levels]}")
        return levels

    def _assign_positions(
        self,
        diagram: VisualDiagram,
        levels: List[List[str]],
        swimlane_map: Dict[str, Swimlane]
    ):
        """
        Atribui posições (x, y) aos elementos baseado nos níveis e swimlanes.
        Quando múltiplos elementos compartilham o mesmo nível e swimlane,
        distribui verticalmente dentro da swimlane.

        Args:
            diagram: Diagrama visual
            levels: Níveis de elementos
            swimlane_map: Mapeamento element_id -> swimlane
        """
        # Calcular posição X para cada nível
        current_x = self.start_x

        for level_idx, level_nodes in enumerate(levels):
            # Encontrar largura máxima neste nível
            max_width = 0
            for node_id in level_nodes:
                element = diagram.get_element(node_id)
                if element:
                    max_width = max(max_width, element.size.width)

            # Agrupar elementos por swimlane neste nível
            lane_groups: Dict[str, List[str]] = defaultdict(list)
            for node_id in level_nodes:
                swimlane = swimlane_map.get(node_id)
                lane_key = swimlane.id if swimlane else '_none_'
                lane_groups[lane_key].append(node_id)

            # Posicionar elementos de cada grupo
            for lane_key, group_nodes in lane_groups.items():
                if len(group_nodes) == 1:
                    # Elemento único na swimlane - centralizar
                    node_id = group_nodes[0]
                    element = diagram.get_element(node_id)
                    if not element:
                        continue

                    swimlane = swimlane_map.get(node_id)
                    if swimlane:
                        center_y = swimlane.position.y + swimlane.size.height / 2
                        element_y = center_y - element.size.height / 2
                    else:
                        element_y = 100

                    element_x = current_x + (max_width - element.size.width) / 2
                    element.position = Position(x=element_x, y=element_y)

                    logger.debug(
                        f"Positioned {node_id} at level {level_idx}: "
                        f"x={element_x:.0f}, y={element_y:.0f}"
                    )
                else:
                    # Múltiplos elementos na mesma swimlane - distribuir verticalmente
                    elements_data = []
                    for node_id in group_nodes:
                        element = diagram.get_element(node_id)
                        if element:
                            elements_data.append((node_id, element))

                    swimlane = swimlane_map.get(group_nodes[0])
                    spacing = 30  # Espaçamento base entre elementos (aumentado de 15 para 30)

                    # Calcular altura total considerando labels externos
                    total_height = 0
                    for _, element in elements_data:
                        elem_height = element.size.height
                        # Adicionar espaço extra se elemento tem label abaixo (Link Events, etc)
                        if element.metadata.get('show_label_below'):
                            elem_height += 40  # 20px (offset do label) + 20px (altura aprox do texto)
                        total_height += elem_height

                    total_height += spacing * (len(elements_data) - 1)

                    if swimlane:
                        center_y = swimlane.position.y + swimlane.size.height / 2
                        start_y = center_y - total_height / 2
                    else:
                        start_y = 100

                    curr_y = start_y
                    for node_id, element in elements_data:
                        element_x = current_x + (max_width - element.size.width) / 2
                        element.position = Position(x=element_x, y=curr_y)

                        # Calcular incremento considerando label externo
                        increment = element.size.height
                        if element.metadata.get('show_label_below'):
                            increment += 40  # Espaço para o label abaixo
                        curr_y += increment + spacing

                        logger.debug(
                            f"Positioned {node_id} at level {level_idx} (stacked): "
                            f"x={element_x:.0f}, y={element.position.y:.0f}"
                        )

            # Próxima coluna
            current_x += max_width + self.element_spacing_x

    def calculate_layout(self, diagram: VisualDiagram, process: Process) -> VisualDiagram:
        """
        Calcula layout completo do diagrama.

        Args:
            diagram: Diagrama visual (com swimlanes já configuradas)
            process: Processo original

        Returns:
            Diagrama com elementos posicionados
        """
        logger.info("Calculating auto layout...")

        if not diagram.elements:
            logger.warning("No elements to layout")
            return diagram

        # Construir grafo
        graph = self._build_graph(diagram)

        # Ordenar em níveis
        levels = self._topological_sort(graph, diagram.elements)

        # Criar mapeamento elemento -> swimlane
        swimlane_map: Dict[str, Swimlane] = {}
        for swimlane in diagram.swimlanes:
            for elem_id in swimlane.elements:
                swimlane_map[elem_id] = swimlane

        # Atribuir posições
        self._assign_positions(diagram, levels, swimlane_map)

        # Ajustar canvas size baseado nos elementos
        self._adjust_canvas_size(diagram)

        logger.info(f"Layout calculated for {len(diagram.elements)} elements")
        return diagram

    def _adjust_canvas_size(self, diagram: VisualDiagram):
        """
        Ajusta o tamanho do canvas baseado nos elementos posicionados.

        Args:
            diagram: Diagrama visual
        """
        if not diagram.elements:
            return

        # Calcular bounds
        x_min, y_min, x_max, y_max = diagram.get_bounds()

        # Adicionar margem
        margin = 100
        required_width = x_max + margin
        required_height = y_max + margin

        # Atualizar canvas size se necessário
        diagram.canvas_size.width = max(diagram.canvas_size.width, required_width)
        diagram.canvas_size.height = max(diagram.canvas_size.height, required_height)

        logger.debug(
            f"Canvas size adjusted to: {diagram.canvas_size.width}x{diagram.canvas_size.height}"
        )


def apply_auto_layout(diagram: VisualDiagram, process: Process) -> VisualDiagram:
    """
    Aplica layout automático ao diagrama.

    Args:
        diagram: Diagrama visual (deve ter swimlanes configuradas)
        process: Processo original

    Returns:
        Diagrama com elementos posicionados
    """
    engine = AutoLayoutEngine()
    return engine.calculate_layout(diagram, process)


def create_visual_diagram_with_layout(process: Process) -> VisualDiagram:
    """
    Pipeline completo: converte processo para visual e aplica layout.

    Args:
        process: Processo a visualizar

    Returns:
        VisualDiagram completamente posicionado
    """
    from src.converters.process_to_visual import convert_process_to_visual
    from src.layout.swimlane_layout import apply_swimlane_layout

    logger.info(f"Creating visual diagram with layout for: {process.name}")

    # 1. Converter para visual
    diagram = convert_process_to_visual(process)

    # 2. Aplicar swimlanes
    diagram = apply_swimlane_layout(diagram, process)

    # 3. Aplicar auto layout
    diagram = apply_auto_layout(diagram, process)

    logger.info("Visual diagram with layout created successfully")
    return diagram
