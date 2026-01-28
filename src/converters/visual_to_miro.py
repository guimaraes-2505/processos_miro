"""
Conversor de VisualDiagram para Miro.
Cria elementos no Miro usando o MiroClient.

Ícones SVG são renderizados via URL pública (GitHub raw).
Configure ICON_BASE_URL em config/settings.py.
Fallback para emoji quando URL não disponível.
"""

from typing import Dict, Optional
from src.models.visual_model import VisualDiagram, VisualElement, Connector, Swimlane
from src.integrations.miro_client import MiroClient
from src.utils.logger import get_logger
from config.settings import get_settings

logger = get_logger()


class VisualToMiroConverter:
    """
    Converte VisualDiagram para board do Miro.
    """

    def __init__(self, miro_client: MiroClient):
        """
        Inicializa o conversor.

        Args:
            miro_client: Cliente Miro configurado
        """
        self.miro_client = miro_client
        self.element_id_map: Dict[str, str] = {}  # visual_id -> miro_item_id
        self._settings = get_settings()

    def _get_miro_shape_type(self, visual_type: str) -> str:
        """
        Mapeia tipo visual para tipo de shape do Miro.

        Args:
            visual_type: Tipo visual (rectangle, circle, diamond)

        Returns:
            Tipo de shape do Miro
        """
        mapping = {
            'rectangle': 'rectangle',
            'circle': 'circle',
            'diamond': 'rhombus',  # Miro usa 'rhombus' para diamante
            'sticky_note': 'sticky_note',
            'text': 'text'
        }
        return mapping.get(visual_type, 'rectangle')

    def _convert_color_to_miro(self, hex_color: str) -> str:
        """
        Converte cor hex para formato do Miro.

        Args:
            hex_color: Cor em hexadecimal (#RRGGBB)

        Returns:
            Cor no formato aceito pelo Miro
        """
        # Miro aceita cores hex diretamente
        return hex_color

    def _create_swimlane_background(
        self,
        board_id: str,
        swimlane: Swimlane
    ) -> Dict:
        """
        Cria fundo visual para swimlane com label vertical à esquerda.

        Args:
            board_id: ID do board
            swimlane: Swimlane a desenhar

        Returns:
            Item do Miro criado
        """
        logger.debug(f"Creating swimlane background: {swimlane.actor}")

        # Largura do label (barra vertical à esquerda)
        label_width = getattr(swimlane, 'label_width', 60)

        # Criar retângulo de fundo principal (área de conteúdo)
        content_style = {
            "fillColor": self._convert_color_to_miro(swimlane.color.fill),
            "borderColor": self._convert_color_to_miro(swimlane.color.border),
            "borderWidth": "1",
            "fillOpacity": "0.2"  # Bem transparente
        }

        background = self.miro_client.create_shape(
            board_id=board_id,
            x=swimlane.position.x + label_width + (swimlane.size.width - label_width) / 2,
            y=swimlane.position.y + swimlane.size.height / 2,
            width=swimlane.size.width - label_width,
            height=swimlane.size.height,
            content="",
            shape="rectangle",
            style=content_style
        )

        # Criar barra vertical com nome do ator
        label_style = {
            "fillColor": "#E0E0E0",  # Cinza claro
            "borderColor": self._convert_color_to_miro(swimlane.color.border),
            "borderWidth": "1",
            "fontSize": "14",
            "textAlign": "center",
            "textAlignVertical": "middle"
        }

        # Nome do ator (abreviado se muito longo para caber verticalmente)
        actor_name = swimlane.actor
        if len(actor_name) > 15:
            actor_name = actor_name[:12] + "..."

        self.miro_client.create_shape(
            board_id=board_id,
            x=swimlane.position.x + label_width / 2,
            y=swimlane.position.y + swimlane.size.height / 2,
            width=label_width,
            height=swimlane.size.height,
            content=actor_name,
            shape="rectangle",
            style=label_style
        )

        logger.debug(f"Swimlane created with vertical label: {background.get('id')}")
        return background

    def _create_visual_element(
        self,
        board_id: str,
        element: VisualElement
    ) -> Dict:
        """
        Cria elemento visual no Miro seguindo padrões BPMN.

        Args:
            board_id: ID do board
            element: Elemento visual

        Returns:
            Item do Miro criado
        """
        content_preview = element.content[:30] if element.content else "(empty)"
        logger.debug(f"Creating element: {content_preview}")

        # Se for sticky note, usar método específico
        if element.type == 'sticky_note':
            color_map = {
                "#FFF9C4": "yellow",
                "#C8E6C9": "light_green",
                "#FFCDD2": "light_pink",
                "#E3F2FD": "light_blue"
            }
            fill_color = element.style.color.fill
            sticky_color = color_map.get(fill_color, "yellow")

            item = self.miro_client.create_sticky_note(
                board_id=board_id,
                x=element.position.x + element.size.width / 2,
                y=element.position.y + element.size.height / 2,
                content=element.content,
                color=sticky_color
            )
        else:
            # Criar shape normal
            shape_type = self._get_miro_shape_type(element.type)

            style = {
                "fillColor": self._convert_color_to_miro(element.style.color.fill),
                "borderColor": self._convert_color_to_miro(element.style.color.border),
                "borderWidth": str(element.style.border_width),
                "fontSize": str(element.style.font_size),
                "textAlign": "center",
                "textAlignVertical": "middle"
            }

            # Preparar content (com ou sem ícone)
            content = element.content
            icon_svg = element.metadata.get('icon_svg')

            # Usar emoji como prefixo se não temos URL para ícone SVG
            fallback_icon = element.metadata.get('icon')
            icon_url = None

            if icon_svg:
                # Tentar construir URL pública para o ícone
                icon_relative_path = element.metadata.get('icon_relative_path')
                if icon_relative_path:
                    icon_url = self._settings.get_icon_url(icon_relative_path)

                if not icon_url and fallback_icon:
                    content = f"{fallback_icon} {content}"
                    logger.debug(f"Usando emoji fallback: {fallback_icon}")
            elif fallback_icon:
                content = f"{fallback_icon} {content}"

            item = self.miro_client.create_shape(
                board_id=board_id,
                x=element.position.x + element.size.width / 2,
                y=element.position.y + element.size.height / 2,
                width=element.size.width,
                height=element.size.height,
                content=content,
                shape=shape_type,
                style=style
            )

            # Se temos URL do ícone, criar imagem sobreposta ao shape
            if icon_url:
                try:
                    icon_size = element.metadata.get('icon_size', 20)
                    icon_position = element.metadata.get('icon_position', 'left')

                    # Calcular posição do ícone baseado no posicionamento configurado
                    icon_x = element.position.x + element.size.width / 2
                    icon_y = element.position.y + element.size.height / 2
                    if icon_position == 'left':
                        icon_x = element.position.x + icon_size / 2 + 8
                        icon_y = element.position.y + icon_size / 2 + 8
                    elif icon_position == 'center' or icon_position == 'inside':
                        icon_x = element.position.x + element.size.width / 2
                        icon_y = element.position.y + element.size.height / 2

                    self.miro_client.create_image(
                        board_id=board_id,
                        x=icon_x,
                        y=icon_y,
                        url=icon_url,
                        width=float(icon_size),
                        height=float(icon_size)
                    )
                    logger.debug(f"Ícone SVG renderizado via URL para {element.id}")
                except Exception as e:
                    logger.warning(f"Falha ao criar ícone SVG para {element.id}: {e}")

        # Mapear ID
        self.element_id_map[element.id] = item['id']

        # Criar label externo para eventos (abaixo do círculo)
        if element.metadata.get('show_label_below'):
            label_text = element.metadata.get('label_text', '')
            if label_text:
                self.miro_client.create_text(
                    board_id=board_id,
                    x=element.position.x + element.size.width / 2,
                    y=element.position.y + element.size.height + 20,
                    content=label_text,
                    width=120
                )
                logger.debug(f"Created label below element: {label_text}")

        logger.debug(f"Element created: {item['id']}")
        return item

    def _create_connector(
        self,
        board_id: str,
        connector: Connector
    ) -> Dict:
        """
        Cria conector no Miro.

        Args:
            board_id: ID do board
            connector: Conector a criar

        Returns:
            Conector do Miro criado
        """
        # Obter IDs dos elementos no Miro
        start_id = self.element_id_map.get(connector.from_element)
        end_id = self.element_id_map.get(connector.to_element)

        if not start_id or not end_id:
            logger.warning(
                f"Connector references unmapped elements: "
                f"{connector.from_element} -> {connector.to_element}"
            )
            # Tentar usar IDs originais
            start_id = start_id or connector.from_element
            end_id = end_id or connector.to_element

        logger.debug(f"Creating connector: {start_id} -> {end_id}")

        # Mapear estilo: Miro usa "normal" ao invés de "solid"
        stroke_style_map = {"solid": "normal", "dashed": "dashed"}
        miro_stroke_style = stroke_style_map.get(connector.style, "normal")

        style = {
            "strokeColor": connector.color,
            "strokeWidth": connector.width,  # Miro espera número, não string
            "strokeStyle": miro_stroke_style,
            "endStrokeCap": "stealth" if connector.arrow_end else "none",
            "textOrientation": "horizontal"  # Texto sempre horizontal, não alinhado à linha
        }

        item = self.miro_client.create_connector(
            board_id=board_id,
            start_item_id=start_id,
            end_item_id=end_id,
            caption=connector.label,
            style=style
        )

        logger.debug(f"Connector created: {item.get('id')}")
        return item

    def convert_and_create(
        self,
        diagram: VisualDiagram,
        board_name: Optional[str] = None
    ) -> str:
        """
        Converte VisualDiagram completo e cria board no Miro.

        Args:
            diagram: Diagrama visual
            board_name: Nome do board (usa diagram.name se não fornecido)

        Returns:
            ID do board criado
        """
        board_name = board_name or diagram.name

        logger.info(f"Creating Miro board: {board_name}")

        # 1. Criar board
        board = self.miro_client.create_board(
            name=board_name,
            description=diagram.description
        )
        board_id = board['id']

        logger.info(f"Board created: {board_id}")

        # 2. Criar swimlanes (fundos)
        logger.info(f"Creating {len(diagram.swimlanes)} swimlanes...")
        for swimlane in diagram.swimlanes:
            self._create_swimlane_background(board_id, swimlane)

        # 3. Criar elementos
        logger.info(f"Creating {len(diagram.elements)} elements...")
        for element in diagram.elements:
            self._create_visual_element(board_id, element)

        # 4. Criar conectores
        logger.info(f"Creating {len(diagram.connectors)} connectors...")
        connectors_created = 0
        connectors_failed = 0
        for connector in diagram.connectors:
            try:
                self._create_connector(board_id, connector)
                connectors_created += 1
            except Exception as e:
                connectors_failed += 1
                logger.error(
                    f"Failed to create connector "
                    f"{connector.from_element} -> {connector.to_element}: {e}"
                )
                # Continuar mesmo se um conector falhar
        logger.info(
            f"Connectors: {connectors_created} created, {connectors_failed} failed"
        )

        logger.info(f"✓ Miro board created successfully: {board_id}")
        logger.info(f"  URL: https://miro.com/app/board/{board_id}")

        return board_id


def create_miro_board_from_diagram(
    diagram: VisualDiagram,
    miro_client: Optional[MiroClient] = None,
    board_name: Optional[str] = None
) -> str:
    """
    Função utilitária para criar board no Miro a partir de VisualDiagram.

    Args:
        diagram: Diagrama visual
        miro_client: Cliente Miro (cria um novo se não fornecido)
        board_name: Nome do board (opcional)

    Returns:
        ID do board criado
    """
    if miro_client is None:
        miro_client = MiroClient()

    converter = VisualToMiroConverter(miro_client)
    return converter.convert_and_create(diagram, board_name)
