"""
Conversor de Process para VisualDiagram.
Transforma modelo lógico em modelo visual seguindo padrões BPMN.
"""

from typing import Dict, Literal, Optional
from src.models.process_model import Process, ProcessElement, ProcessFlow
from src.models.visual_model import (
    VisualDiagram,
    VisualElement,
    Connector,
    Position,
    Size,
    Color,
    VisualStyle,
    get_visual_style,
    get_element_size
)
from src.utils.logger import get_logger
from src.utils.icon_library import get_icon_resolver, IconResolver
from config.settings import get_settings

logger = get_logger()
settings = get_settings()


# Configurações BPMN para cada tipo de elemento
BPMN_CONFIG = {
    # Eventos (círculos sem texto interno)
    'start_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#C8E6C9", border="#388E3C", text="#1a1a1a"),
            border_width=2,
            font_size=12
        ),
        'show_label_below': True,  # Label abaixo do círculo
        'internal_content': ''     # Sem texto interno
    },
    'end_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#FFCDD2", border="#D32F2F", text="#1a1a1a"),
            border_width=4,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': ''
    },
    'timer_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#FFFFFF", border="#1976D2", text="#1a1a1a"),
            border_width=2,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '⏱'
    },
    'message_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#FFFFFF", border="#1976D2", text="#1a1a1a"),
            border_width=2,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '✉'
    },

    # Link Intermediate Events (para fluxos reversos)
    'link_throw_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#E3F2FD", border="#1976D2", text="#1976D2"),
            border_width=3,
            font_size=18
        ),
        'show_label_below': True,
        'internal_content': '→'  # Seta preenchida = throw
    },
    'link_catch_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#FFFFFF", border="#1976D2", text="#1976D2"),
            border_width=2,
            font_size=18
        ),
        'show_label_below': True,
        'internal_content': '→'  # Seta contorno = catch
    },

    # Gateways (losangos com símbolo interno)
    'exclusive_gateway': {
        'shape': 'diamond',
        'size': Size(width=60, height=60),
        'style': VisualStyle(
            color=Color(fill="#FFF9C4", border="#F57C00", text="#1a1a1a"),
            border_width=2,
            font_size=18,
            font_weight='bold'
        ),
        'internal_content': 'X'  # Símbolo do gateway exclusivo
    },
    'inclusive_gateway': {
        'shape': 'diamond',
        'size': Size(width=60, height=60),
        'style': VisualStyle(
            color=Color(fill="#FFF9C4", border="#F57C00", text="#1a1a1a"),
            border_width=2,
            font_size=18,
            font_weight='bold'
        ),
        'internal_content': 'O'
    },
    'parallel_gateway': {
        'shape': 'diamond',
        'size': Size(width=60, height=60),
        'style': VisualStyle(
            color=Color(fill="#FFF9C4", border="#F57C00", text="#1a1a1a"),
            border_width=2,
            font_size=18,
            font_weight='bold'
        ),
        'internal_content': '+'
    },
    'event_based_gateway': {
        'shape': 'diamond',
        'size': Size(width=60, height=60),
        'style': VisualStyle(
            color=Color(fill="#FFF9C4", border="#F57C00", text="#1a1a1a"),
            border_width=2,
            font_size=18,
            font_weight='bold'
        ),
        'internal_content': '◇'
    },

    # Eventos de início especializados
    'start_timer_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#C8E6C9", border="#388E3C", text="#1a1a1a"),
            border_width=2,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '⏱'
    },
    'start_message_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#C8E6C9", border="#388E3C", text="#1a1a1a"),
            border_width=2,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '✉'
    },
    'start_conditional_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#C8E6C9", border="#388E3C", text="#1a1a1a"),
            border_width=2,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '≡'
    },
    'start_error_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#C8E6C9", border="#388E3C", text="#1a1a1a"),
            border_width=2,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '⚡'
    },
    'start_signal_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#C8E6C9", border="#388E3C", text="#1a1a1a"),
            border_width=2,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '△'
    },
    'start_multiple_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#C8E6C9", border="#388E3C", text="#1a1a1a"),
            border_width=2,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '⬠'
    },

    # Eventos de fim especializados
    'end_message_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#FFCDD2", border="#D32F2F", text="#1a1a1a"),
            border_width=4,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '✉'
    },
    'end_signal_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#FFCDD2", border="#D32F2F", text="#1a1a1a"),
            border_width=4,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '△'
    },
    'end_multiple_event': {
        'shape': 'circle',
        'size': Size(width=50, height=50),
        'style': VisualStyle(
            color=Color(fill="#FFCDD2", border="#D32F2F", text="#1a1a1a"),
            border_width=4,
            font_size=12
        ),
        'show_label_below': True,
        'internal_content': '⬠'
    },

    # Tarefas (retângulos com cantos arredondados)
    'user_task': {
        'shape': 'rectangle',
        'size': Size(width=160, height=80),
        'style': VisualStyle(
            color=Color(fill="#E3F2FD", border="#1976D2", text="#1a1a1a"),
            border_width=2,
            font_size=13
        ),
        'icon': '👤'
    },
    'manual_task': {
        'shape': 'rectangle',
        'size': Size(width=160, height=80),
        'style': VisualStyle(
            color=Color(fill="#E3F2FD", border="#1976D2", text="#1a1a1a"),
            border_width=2,
            font_size=13
        ),
        'icon': '✋'
    },
    'service_task': {
        'shape': 'rectangle',
        'size': Size(width=160, height=80),
        'style': VisualStyle(
            color=Color(fill="#E3F2FD", border="#1976D2", text="#1a1a1a"),
            border_width=2,
            font_size=13
        ),
        'icon': '⚙️'
    },
    'task': {
        'shape': 'rectangle',
        'size': Size(width=160, height=80),
        'style': VisualStyle(
            color=Color(fill="#E3F2FD", border="#1976D2", text="#1a1a1a"),
            border_width=2,
            font_size=13
        )
    }
}


def get_bpmn_element_type(element: ProcessElement) -> str:
    """
    Determina o tipo BPMN específico do elemento.

    Args:
        element: Elemento do processo

    Returns:
        Tipo BPMN específico (start_event, exclusive_gateway, user_task, etc)
    """
    if element.is_event():
        event_type = element.metadata.get('event_type', 'start')
        event_subtype = element.metadata.get('event_subtype')

        # Eventos com subtipo específico (ex: start + timer = start_timer_event)
        if event_subtype:
            composite = f"{event_type}_{event_subtype}_event"
            if composite in BPMN_CONFIG:
                return composite

        # Mapeamento direto
        event_map = {
            'start': 'start_event',
            'end': 'end_event',
            'timer': 'timer_event',
            'message': 'message_event',
            'error': 'start_error_event',
            'signal': 'start_signal_event',
            'conditional': 'start_conditional_event',
            'multiple': 'start_multiple_event',
        }
        return event_map.get(event_type, 'start_event')

    elif element.is_gateway():
        gateway_type = element.metadata.get('gateway_type', 'exclusive')
        gateway_map = {
            'exclusive': 'exclusive_gateway',
            'inclusive': 'inclusive_gateway',
            'parallel': 'parallel_gateway',
            'event_based': 'event_based_gateway',
        }
        return gateway_map.get(gateway_type, 'exclusive_gateway')

    elif element.is_task():
        task_type = element.metadata.get('task_type', 'task')
        task_map = {
            'user': 'user_task',
            'service': 'service_task',
            'task': 'task',
        }
        return task_map.get(task_type, 'task')

    return 'task'


def get_visual_type(element: ProcessElement) -> Literal['rectangle', 'circle', 'diamond', 'sticky_note', 'text']:
    """
    Determina o tipo visual baseado no tipo de elemento.

    Args:
        element: Elemento do processo

    Returns:
        Tipo de forma visual
    """
    if element.is_task():
        return 'rectangle'
    elif element.is_gateway():
        return 'diamond'
    elif element.is_event():
        return 'circle'
    elif element.is_annotation():
        return 'sticky_note'
    else:
        return 'rectangle'


class ProcessToVisualConverter:
    """
    Conversor de Process para VisualDiagram.

    Attributes:
        icon_resolver: Resolver de ícones SVG customizados
        use_svg_icons: Se deve usar ícones SVG ou emojis
    """

    def __init__(self, icon_resolver: Optional[IconResolver] = None):
        self.element_mapping: Dict[str, str] = {}  # process_element_id -> visual_element_id
        self.visual_id_counter = 0

        # Inicializar resolver de ícones
        self.use_svg_icons = settings.is_icons_enabled()
        if self.use_svg_icons:
            try:
                self.icon_resolver = icon_resolver or get_icon_resolver(
                    settings.get_icons_yaml_path()
                )
                logger.info(f"Ícones SVG habilitados: {self.icon_resolver.get_stats()}")
            except Exception as e:
                logger.warning(f"Erro ao carregar ícones SVG: {e}. Usando emojis como fallback.")
                self.use_svg_icons = False
                self.icon_resolver = None
        else:
            self.icon_resolver = None
            logger.debug("Ícones SVG desabilitados. Usando emojis.")

    def _generate_visual_id(self, prefix: str = "visual") -> str:
        """Gera ID único para elemento visual."""
        self.visual_id_counter += 1
        return f"{prefix}_{self.visual_id_counter}"

    def _convert_element(self, element: ProcessElement) -> VisualElement:
        """
        Converte um ProcessElement em VisualElement seguindo padrões BPMN.

        Args:
            element: Elemento do processo

        Returns:
            VisualElement correspondente
        """
        # Determinar tipo BPMN específico e tipo visual
        bpmn_type = get_bpmn_element_type(element)
        visual_type = get_visual_type(element)

        # Gerar ID visual
        visual_id = self._generate_visual_id("elem")
        self.element_mapping[element.id] = visual_id

        # Obter configuração BPMN se disponível
        bpmn_config = BPMN_CONFIG.get(bpmn_type, {})

        # Obter estilo (da config BPMN ou padrão)
        if 'style' in bpmn_config:
            style = bpmn_config['style'].model_copy()
        else:
            event_type = element.metadata.get('event_type') if element.is_event() else None
            style = get_visual_style(element.type, event_type)

        # Obter tamanho (da config BPMN ou padrão)
        if 'size' in bpmn_config:
            size = bpmn_config['size'].model_copy()
        else:
            size = get_element_size(element.type)

        # Determinar conteúdo do elemento
        # Eventos e gateways: símbolo interno, nome fica como label externo
        # Tarefas: nome dentro com ícone opcional
        if bpmn_config.get('show_label_below', False):
            # Eventos: símbolo interno, label será criado separadamente
            content = bpmn_config.get('internal_content', '')
            show_label_below = True
            label_text = element.name
        elif 'internal_content' in bpmn_config and element.is_gateway():
            # Gateways: símbolo X, O ou + interno
            content = bpmn_config['internal_content']
            show_label_below = False
            label_text = None
        else:
            # Tarefas: nome com ícone opcional
            # Tentar usar ícone SVG se disponível, senão fallback para emoji
            icon_svg = None
            icon_emoji = bpmn_config.get('icon', '')

            icon_relative_path = None
            if self.use_svg_icons and self.icon_resolver:
                # Tentar resolver ícone SVG
                icon_svg = self.icon_resolver.get_icon_svg(element.type, bpmn_type)
                if icon_svg:
                    icon_path = self.icon_resolver.get_icon_path(element.type, bpmn_type)
                    if icon_path:
                        icon_relative_path = str(icon_path)
                    logger.debug(f"Ícone SVG encontrado para {bpmn_type}")

            # Determinar conteúdo baseado no modo
            if icon_svg:
                # Modo SVG: apenas o nome, SVG será adicionado depois no Miro
                content = element.name
            elif icon_emoji:
                # Fallback para emoji
                content = f"{icon_emoji} {element.name}"
            else:
                # Sem ícone
                content = element.name

            show_label_below = False
            label_text = None

        # Criar elemento visual (posição será calculada pelo layout engine)
        visual_element = VisualElement(
            id=visual_id,
            element_id=element.id,
            type=visual_type,
            content=content,
            position=Position(x=0, y=0),  # Placeholder
            size=size,
            style=style,
            metadata={
                'original_type': element.type,
                'bpmn_type': bpmn_type,
                'actor': element.actor,
                'description': element.description,
                'show_label_below': show_label_below,
                'label_text': label_text,
                'icon': bpmn_config.get('icon'),  # Emoji fallback
                'icon_svg': icon_svg if 'icon_svg' in locals() and icon_svg else None,
                'icon_relative_path': icon_relative_path if 'icon_relative_path' in locals() and icon_relative_path else None,
                'icon_size': self.icon_resolver.get_icon_size(element.type) if self.icon_resolver else 24,
                'icon_position': self.icon_resolver.get_icon_position(element.type) if self.icon_resolver else 'left'
            }
        )

        logger.debug(f"Converted element {element.id} -> {visual_id} ({bpmn_type})")
        return visual_element

    def _create_link_event(
        self,
        bpmn_type: str,
        link_label: str,
        actor: str
    ) -> VisualElement:
        """
        Cria um Link Intermediate Event (Throw ou Catch).

        Args:
            bpmn_type: 'link_throw_event' ou 'link_catch_event'
            link_label: Letra/nome do link (ex: 'A')
            actor: Ator/swimlane onde o evento será posicionado

        Returns:
            VisualElement do link event
        """
        config = BPMN_CONFIG[bpmn_type]
        visual_id = self._generate_visual_id("elem")

        element = VisualElement(
            id=visual_id,
            element_id=f"{bpmn_type}_{link_label}",
            type='circle',
            content=config['internal_content'],
            position=Position(x=0, y=0),
            size=config['size'].model_copy(),
            style=config['style'].model_copy(),
            metadata={
                'original_type': 'event',
                'bpmn_type': bpmn_type,
                'actor': actor,
                'description': f'Link {link_label}',
                'show_label_below': True,
                'label_text': link_label,
                'link_label': link_label
            }
        )

        logger.debug(f"Created {bpmn_type}: {visual_id} (link={link_label}, actor={actor})")
        return element

    def _convert_flow(self, flow: ProcessFlow) -> Connector:
        """
        Converte um ProcessFlow em Connector.

        Args:
            flow: Fluxo do processo

        Returns:
            Connector correspondente
        """
        # Obter IDs visuais dos elementos
        from_visual_id = self.element_mapping.get(flow.from_element)
        to_visual_id = self.element_mapping.get(flow.to_element)

        if not from_visual_id or not to_visual_id:
            logger.warning(
                f"Flow references unmapped elements: {flow.from_element} -> {flow.to_element}"
            )
            # Usar IDs originais como fallback
            from_visual_id = from_visual_id or flow.from_element
            to_visual_id = to_visual_id or flow.to_element

        # Gerar ID do conector
        connector_id = self._generate_visual_id("conn")

        # Determinar se é linha tracejada (para fluxos condicionais)
        style = 'solid'
        if flow.condition:
            style = 'solid'  # Mantém sólido, apenas adiciona label

        connector = Connector(
            id=connector_id,
            flow_id=f"{flow.from_element}->{flow.to_element}",
            from_element=from_visual_id,
            to_element=to_visual_id,
            label=flow.condition,
            style=style,
            color="#424242",
            width=2,
            arrow_end=True
        )

        logger.debug(
            f"Converted flow {flow.from_element}->{flow.to_element} -> {connector_id}"
        )
        return connector

    def convert(self, process: Process) -> VisualDiagram:
        """
        Converte um Process completo em VisualDiagram.

        Args:
            process: Processo a converter

        Returns:
            VisualDiagram correspondente
        """
        logger.info(f"Converting process to visual diagram: {process.name}")

        # Reset estado
        self.element_mapping = {}
        self.visual_id_counter = 0

        # Converter elementos
        visual_elements = []
        for element in process.elements:
            visual_element = self._convert_element(element)
            visual_elements.append(visual_element)

        logger.info(f"Converted {len(visual_elements)} elements")

        # Detectar fluxos reversos (backward flows)
        element_order = {elem.id: idx for idx, elem in enumerate(process.elements)}
        element_actor_map = {elem.id: elem.actor for elem in process.elements}

        forward_flows = []
        backward_flows = []

        for flow in process.flows:
            from_idx = element_order.get(flow.from_element, 0)
            to_idx = element_order.get(flow.to_element, 0)
            if to_idx < from_idx:
                backward_flows.append(flow)
            else:
                forward_flows.append(flow)

        if backward_flows:
            logger.info(
                f"Detected {len(backward_flows)} backward flow(s) - "
                f"replacing with Link Throw/Catch events"
            )

        # Converter fluxos normais (forward)
        connectors = []
        for flow in forward_flows:
            connector = self._convert_flow(flow)
            connectors.append(connector)

        # Criar Link Events para fluxos reversos
        link_label_counter = ord('A')
        for flow in backward_flows:
            link_label = chr(link_label_counter)
            link_label_counter += 1

            from_actor = element_actor_map.get(flow.from_element, '')
            to_actor = element_actor_map.get(flow.to_element, '')

            # Criar Link Throw (na swimlane de origem)
            throw_event = self._create_link_event(
                'link_throw_event', link_label, from_actor
            )
            visual_elements.append(throw_event)

            # Criar Link Catch (na swimlane de destino)
            catch_event = self._create_link_event(
                'link_catch_event', link_label, to_actor
            )
            visual_elements.append(catch_event)

            # Conector: origem → Link Throw (com label da condição)
            from_visual_id = self.element_mapping.get(flow.from_element)
            to_visual_id = self.element_mapping.get(flow.to_element)

            connectors.append(Connector(
                id=self._generate_visual_id("conn"),
                flow_id=f"{flow.from_element}->link_throw_{link_label}",
                from_element=from_visual_id,
                to_element=throw_event.id,
                label=flow.condition,
                style='solid',
                color="#424242",
                width=2,
                arrow_end=True
            ))

            # Conector: Link Catch → destino (sem label)
            connectors.append(Connector(
                id=self._generate_visual_id("conn"),
                flow_id=f"link_catch_{link_label}->{flow.to_element}",
                from_element=catch_event.id,
                to_element=to_visual_id,
                label=None,
                style='solid',
                color="#424242",
                width=2,
                arrow_end=True
            ))

            logger.info(
                f"  Link {link_label}: {flow.from_element} ⊕→ ...→⊕ {flow.to_element}"
                f" [{flow.condition or 'sem condição'}]"
            )

        logger.info(f"Converted {len(connectors)} flows (including link events)")

        # Criar diagrama visual
        diagram = VisualDiagram(
            name=process.name,
            description=process.description,
            elements=visual_elements,
            connectors=connectors,
            swimlanes=[],  # Será preenchido pelo layout engine
            metadata={
                'actors': process.actors,
                'source_process': {
                    'total_elements': len(process.elements),
                    'total_flows': len(process.flows),
                    'total_actors': len(process.actors)
                }
            }
        )

        logger.info(f"Visual diagram created: {diagram.name}")
        return diagram


def convert_process_to_visual(process: Process) -> VisualDiagram:
    """
    Função utilitária para converter Process em VisualDiagram.

    Args:
        process: Processo a converter

    Returns:
        VisualDiagram correspondente
    """
    converter = ProcessToVisualConverter()
    return converter.convert(process)
