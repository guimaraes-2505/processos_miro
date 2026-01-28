"""
Testes para conversores e layout.
"""

import pytest
from src.models.process_model import Process, ProcessElement, ProcessFlow
from src.models.visual_model import VisualDiagram, Position, Size
from src.converters.process_to_visual import convert_process_to_visual
from src.layout.swimlane_layout import apply_swimlane_layout
from src.layout.auto_layout import apply_auto_layout, create_visual_diagram_with_layout


@pytest.fixture
def simple_process():
    """Cria um processo simples para testes."""
    return Process(
        name="Simple Test Process",
        description="A simple process for testing",
        actors=["Actor1", "Actor2"],
        elements=[
            ProcessElement(
                id="start",
                type="event",
                name="Start",
                metadata={"event_type": "start"}
            ),
            ProcessElement(
                id="task1",
                type="task",
                name="Task 1",
                actor="Actor1"
            ),
            ProcessElement(
                id="task2",
                type="task",
                name="Task 2",
                actor="Actor2"
            ),
            ProcessElement(
                id="gateway1",
                type="gateway",
                name="Decision",
                actor="Actor1",
                metadata={"gateway_type": "exclusive"}
            ),
            ProcessElement(
                id="end",
                type="event",
                name="End",
                metadata={"event_type": "end"}
            )
        ],
        flows=[
            ProcessFlow(from_element="start", to_element="task1"),
            ProcessFlow(from_element="task1", to_element="gateway1"),
            ProcessFlow(from_element="gateway1", to_element="task2", condition="Yes"),
            ProcessFlow(from_element="gateway1", to_element="end", condition="No"),
            ProcessFlow(from_element="task2", to_element="end")
        ]
    )


class TestProcessToVisualConverter:
    """Testes para conversão Process -> Visual"""

    def test_convert_simple_process(self, simple_process):
        """Testa conversão básica"""
        diagram = convert_process_to_visual(simple_process)

        assert diagram is not None
        assert diagram.name == simple_process.name
        assert len(diagram.elements) == len(simple_process.elements)
        assert len(diagram.connectors) == len(simple_process.flows)

    def test_element_types_mapped_correctly(self, simple_process):
        """Testa que tipos de elementos são mapeados corretamente"""
        diagram = convert_process_to_visual(simple_process)

        # Verificar tipos visuais
        visual_types = {e.type for e in diagram.elements}

        assert 'rectangle' in visual_types  # Tasks
        assert 'circle' in visual_types  # Events
        assert 'diamond' in visual_types  # Gateway

    def test_connectors_have_labels_for_conditions(self, simple_process):
        """Testa que conectores têm labels quando há condições"""
        diagram = convert_process_to_visual(simple_process)

        # Encontrar conectores com condições
        conditional_connectors = [c for c in diagram.connectors if c.label]

        assert len(conditional_connectors) >= 2  # "Yes" e "No"
        assert any(c.label == "Yes" for c in conditional_connectors)
        assert any(c.label == "No" for c in conditional_connectors)

    def test_metadata_preserved(self, simple_process):
        """Testa que metadados são preservados"""
        diagram = convert_process_to_visual(simple_process)

        # Verificar que actors estão nos metadados
        task_elements = [e for e in diagram.elements if e.type == 'rectangle']

        for task in task_elements:
            assert 'actor' in task.metadata
            assert task.metadata['actor'] in simple_process.actors


class TestSwimlaneLayout:
    """Testes para layout de swimlanes"""

    def test_swimlanes_created_for_actors(self, simple_process):
        """Testa que swimlanes são criadas para cada ator"""
        diagram = convert_process_to_visual(simple_process)
        diagram = apply_swimlane_layout(diagram, simple_process)

        # Deve ter pelo menos uma swimlane por ator
        assert len(diagram.swimlanes) >= len(simple_process.actors)

        # Verificar que cada ator tem uma swimlane
        swimlane_actors = {s.actor for s in diagram.swimlanes}
        for actor in simple_process.actors:
            assert actor in swimlane_actors

    def test_elements_assigned_to_correct_swimlane(self, simple_process):
        """Testa que elementos são atribuídos às swimlanes corretas"""
        diagram = convert_process_to_visual(simple_process)
        diagram = apply_swimlane_layout(diagram, simple_process)

        for swimlane in diagram.swimlanes:
            # Verificar que elementos na swimlane têm o ator correto
            for elem_id in swimlane.elements:
                element = diagram.get_element(elem_id)
                if element and element.metadata.get('actor'):
                    assert element.metadata['actor'] == swimlane.actor

    def test_swimlanes_have_positions(self, simple_process):
        """Testa que swimlanes têm posições válidas"""
        diagram = convert_process_to_visual(simple_process)
        diagram = apply_swimlane_layout(diagram, simple_process)

        for swimlane in diagram.swimlanes:
            assert swimlane.position.x >= 0
            assert swimlane.position.y >= 0
            assert swimlane.size.width > 0
            assert swimlane.size.height > 0

    def test_swimlanes_dont_overlap(self, simple_process):
        """Testa que swimlanes não se sobrepõem verticalmente"""
        diagram = convert_process_to_visual(simple_process)
        diagram = apply_swimlane_layout(diagram, simple_process)

        # Ordenar por Y
        swimlanes = sorted(diagram.swimlanes, key=lambda s: s.position.y)

        for i in range(len(swimlanes) - 1):
            current_bottom = swimlanes[i].position.y + swimlanes[i].size.height
            next_top = swimlanes[i + 1].position.y

            # Next swimlane deve começar após o fim da atual
            assert next_top >= current_bottom


class TestAutoLayout:
    """Testes para layout automático"""

    def test_elements_have_positions_after_layout(self, simple_process):
        """Testa que elementos têm posições após layout"""
        diagram = convert_process_to_visual(simple_process)
        diagram = apply_swimlane_layout(diagram, simple_process)
        diagram = apply_auto_layout(diagram, simple_process)

        for element in diagram.elements:
            assert element.position is not None
            assert element.position.x >= 0
            assert element.position.y >= 0

    def test_elements_flow_left_to_right(self, simple_process):
        """Testa que elementos fluem da esquerda para direita"""
        diagram = convert_process_to_visual(simple_process)
        diagram = apply_swimlane_layout(diagram, simple_process)
        diagram = apply_auto_layout(diagram, simple_process)

        # Encontrar start e end
        start_elem = next(
            e for e in diagram.elements
            if e.metadata.get('original_type') == 'event'
            and 'start' in e.element_id.lower()
        )
        end_elem = next(
            e for e in diagram.elements
            if e.metadata.get('original_type') == 'event'
            and 'end' in e.element_id.lower()
        )

        # End deve estar à direita de Start
        assert end_elem.position.x > start_elem.position.x

    def test_elements_in_swimlanes_have_correct_y(self, simple_process):
        """Testa que elementos estão posicionados dentro de suas swimlanes"""
        diagram = convert_process_to_visual(simple_process)
        diagram = apply_swimlane_layout(diagram, simple_process)
        diagram = apply_auto_layout(diagram, simple_process)

        for swimlane in diagram.swimlanes:
            for elem_id in swimlane.elements:
                element = diagram.get_element(elem_id)
                if element:
                    # Elemento deve estar dentro dos limites Y da swimlane
                    assert element.position.y >= swimlane.position.y
                    assert (
                        element.position.y + element.size.height <=
                        swimlane.position.y + swimlane.size.height
                    )

    def test_canvas_size_adjusted(self, simple_process):
        """Testa que tamanho do canvas é ajustado"""
        diagram = convert_process_to_visual(simple_process)
        diagram = apply_swimlane_layout(diagram, simple_process)

        original_width = diagram.canvas_size.width
        original_height = diagram.canvas_size.height

        diagram = apply_auto_layout(diagram, simple_process)

        # Canvas pode ter sido ajustado
        assert diagram.canvas_size.width >= 0
        assert diagram.canvas_size.height >= 0


class TestCompleteLayoutPipeline:
    """Testes para pipeline completo"""

    def test_create_visual_diagram_with_layout(self, simple_process):
        """Testa pipeline completo de criação de diagrama"""
        diagram = create_visual_diagram_with_layout(simple_process)

        # Verificações gerais
        assert diagram is not None
        assert len(diagram.elements) == len(simple_process.elements)
        assert len(diagram.connectors) == len(simple_process.flows)
        assert len(diagram.swimlanes) > 0

        # Verificar que todos elementos têm posições
        for element in diagram.elements:
            assert element.position.x >= 0
            assert element.position.y >= 0

    def test_no_overlapping_elements(self, simple_process):
        """Testa que elementos não se sobrepõem (verificação básica)"""
        diagram = create_visual_diagram_with_layout(simple_process)

        # Esta é uma verificação simplificada
        # Em um algoritmo mais sofisticado, verificaríamos sobreposição real
        positions = [
            (e.position.x, e.position.y, e.size.width, e.size.height)
            for e in diagram.elements
        ]

        # Ao menos verificar que não há duas posições idênticas
        assert len(positions) == len(set(positions))

    def test_connectors_reference_valid_elements(self, simple_process):
        """Testa que conectores referenciam elementos válidos"""
        diagram = create_visual_diagram_with_layout(simple_process)

        element_ids = {e.id for e in diagram.elements}

        for connector in diagram.connectors:
            assert connector.from_element in element_ids
            assert connector.to_element in element_ids


@pytest.fixture
def complex_process():
    """Cria um processo mais complexo para testes"""
    return Process(
        name="Complex Process",
        actors=["Actor1", "Actor2", "Actor3"],
        elements=[
            ProcessElement(id="start", type="event", name="Start",
                         metadata={"event_type": "start"}),
            ProcessElement(id="t1", type="task", name="Task 1", actor="Actor1"),
            ProcessElement(id="t2", type="task", name="Task 2", actor="Actor2"),
            ProcessElement(id="t3", type="task", name="Task 3", actor="Actor3"),
            ProcessElement(id="g1", type="gateway", name="Gateway 1", actor="Actor1",
                         metadata={"gateway_type": "exclusive"}),
            ProcessElement(id="t4", type="task", name="Task 4", actor="Actor2"),
            ProcessElement(id="t5", type="task", name="Task 5", actor="Actor3"),
            ProcessElement(id="end1", type="event", name="End 1",
                         metadata={"event_type": "end"}),
            ProcessElement(id="end2", type="event", name="End 2",
                         metadata={"event_type": "end"}),
        ],
        flows=[
            ProcessFlow(from_element="start", to_element="t1"),
            ProcessFlow(from_element="t1", to_element="g1"),
            ProcessFlow(from_element="g1", to_element="t2", condition="Path A"),
            ProcessFlow(from_element="g1", to_element="t3", condition="Path B"),
            ProcessFlow(from_element="t2", to_element="t4"),
            ProcessFlow(from_element="t3", to_element="t5"),
            ProcessFlow(from_element="t4", to_element="end1"),
            ProcessFlow(from_element="t5", to_element="end2"),
        ]
    )


def test_complex_process_layout(complex_process):
    """Testa layout de processo mais complexo"""
    diagram = create_visual_diagram_with_layout(complex_process)

    assert len(diagram.elements) == 9
    assert len(diagram.connectors) == 8
    assert len(diagram.swimlanes) >= 3

    # Todos elementos devem ter posições válidas
    for element in diagram.elements:
        assert element.position.x >= 0
        assert element.position.y >= 0
