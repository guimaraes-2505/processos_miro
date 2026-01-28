"""
Cliente para integração com Miro via API REST.
Cria boards e adiciona elementos visuais (shapes, conectores, sticky notes).
"""

import requests
from typing import Dict, List, Optional, Any
from config.settings import get_settings
from src.utils.exceptions import MiroAPIError
from src.utils.logger import get_logger

logger = get_logger()


class MiroClient:
    """
    Cliente para API do Miro.
    Permite criar boards e adicionar elementos visuais.
    """

    BASE_URL = "https://api.miro.com/v2"

    def __init__(self, api_token: Optional[str] = None):
        """
        Inicializa cliente Miro.

        Args:
            api_token: Token de acesso (usa settings se não fornecido)
        """
        settings = get_settings()
        self.api_token = api_token or settings.MIRO_API_TOKEN

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        logger.info("Miro client initialized")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Faz requisição à API do Miro.

        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API (ex: /boards)
            data: Dados JSON para enviar
            params: Parâmetros de query string

        Returns:
            Resposta JSON

        Raises:
            MiroAPIError: Se a requisição falhar
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )

            # Log da requisição
            logger.debug(f"{method} {endpoint} - Status: {response.status_code}")

            # Verificar erros
            if response.status_code >= 400:
                error_msg = f"Miro API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data}"
                except:
                    error_msg += f" - {response.text}"

                logger.error(error_msg)
                raise MiroAPIError(error_msg, status_code=response.status_code)

            # Retornar JSON
            return response.json() if response.text else {}

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise MiroAPIError(f"Request failed: {e}")

    def create_board(
        self,
        name: str,
        description: str = "",
        policy_sharing: str = "private"
    ) -> Dict:
        """
        Cria um novo board no Miro.

        Args:
            name: Nome do board
            description: Descrição do board
            policy_sharing: Política de compartilhamento (private, team, organization)

        Returns:
            Dados do board criado (incluindo 'id')
        """
        logger.info(f"Creating Miro board: {name}")

        data = {
            "name": name,
            "description": description,
            "policy": {
                "sharingPolicy": {
                    "access": policy_sharing,
                    "teamAccess": "edit"
                }
            }
        }

        board = self._request("POST", "/boards", data=data)
        logger.info(f"Board created: {board.get('id')} - {name}")

        return board

    def create_shape(
        self,
        board_id: str,
        x: float,
        y: float,
        width: float,
        height: float,
        content: str,
        shape: str = "rectangle",
        style: Optional[Dict] = None
    ) -> Dict:
        """
        Cria uma shape (forma) no board.

        Args:
            board_id: ID do board
            x: Posição X
            y: Posição Y
            width: Largura
            height: Altura
            content: Texto dentro da shape
            shape: Tipo de shape (rectangle, circle, triangle, etc)
            style: Estilos customizados

        Returns:
            Dados da shape criada
        """
        data = {
            "data": {
                "shape": shape,
                "content": content
            },
            "position": {
                "x": x,
                "y": y,
                "origin": "center"
            },
            "geometry": {
                "width": width,
                "height": height
            }
        }

        # Aplicar estilos se fornecidos
        if style:
            data["style"] = style

        shape_item = self._request("POST", f"/boards/{board_id}/shapes", data=data)
        logger.debug(f"Shape created: {shape_item.get('id')} - {content[:30]}")

        return shape_item

    def create_sticky_note(
        self,
        board_id: str,
        x: float,
        y: float,
        content: str,
        color: str = "yellow"
    ) -> Dict:
        """
        Cria um sticky note no board.

        Args:
            board_id: ID do board
            x: Posição X
            y: Posição Y
            content: Texto do sticky note
            color: Cor (yellow, light_green, light_blue, etc)

        Returns:
            Dados do sticky note criado
        """
        data = {
            "data": {
                "content": content,
                "shape": "square"
            },
            "position": {
                "x": x,
                "y": y,
                "origin": "center"
            },
            "style": {
                "fillColor": color
            }
        }

        sticky = self._request("POST", f"/boards/{board_id}/sticky_notes", data=data)
        logger.debug(f"Sticky note created: {sticky.get('id')}")

        return sticky

    def create_connector(
        self,
        board_id: str,
        start_item_id: str,
        end_item_id: str,
        caption: Optional[str] = None,
        style: Optional[Dict] = None
    ) -> Dict:
        """
        Cria um conector (linha/seta) entre dois elementos.

        Args:
            board_id: ID do board
            start_item_id: ID do elemento inicial
            end_item_id: ID do elemento final
            caption: Texto na linha (opcional)
            style: Estilos customizados

        Returns:
            Dados do conector criado
        """
        data = {
            "startItem": {
                "id": start_item_id
            },
            "endItem": {
                "id": end_item_id
            },
            "shape": "elbowed",  # elbowed para BPMN, ou "straight", "curved"
            "style": style or {
                "strokeColor": "#1a1a1a",
                "strokeWidth": 2,
                "strokeStyle": "normal",
                "endStrokeCap": "stealth",
                "textOrientation": "horizontal"
            }
        }

        if caption:
            data["captions"] = [{
                "content": caption
            }]

        connector = self._request("POST", f"/boards/{board_id}/connectors", data=data)
        logger.debug(f"Connector created: {connector.get('id')}")

        return connector

    def create_text(
        self,
        board_id: str,
        x: float,
        y: float,
        content: str,
        width: Optional[float] = None
    ) -> Dict:
        """
        Cria um elemento de texto no board.

        Args:
            board_id: ID do board
            x: Posição X
            y: Posição Y
            content: Texto
            width: Largura (opcional)

        Returns:
            Dados do texto criado
        """
        data = {
            "data": {
                "content": content
            },
            "position": {
                "x": x,
                "y": y,
                "origin": "center"
            },
            "style": {
                "fontSize": "14",
                "textAlign": "left"
            }
        }

        if width:
            data["geometry"] = {"width": width}

        text_item = self._request("POST", f"/boards/{board_id}/texts", data=data)
        logger.debug(f"Text created: {text_item.get('id')}")

        return text_item

    def get_board(self, board_id: str) -> Dict:
        """
        Obtém informações de um board.

        Args:
            board_id: ID do board

        Returns:
            Dados do board
        """
        return self._request("GET", f"/boards/{board_id}")

    def list_boards(self, limit: int = 10) -> List[Dict]:
        """
        Lista boards do usuário.

        Args:
            limit: Número máximo de boards

        Returns:
            Lista de boards
        """
        params = {"limit": limit}
        response = self._request("GET", "/boards", params=params)
        return response.get("data", [])

    def delete_board(self, board_id: str):
        """
        Deleta um board.

        Args:
            board_id: ID do board
        """
        logger.warning(f"Deleting board: {board_id}")
        self._request("DELETE", f"/boards/{board_id}")
        logger.info(f"Board deleted: {board_id}")

    # ========================================
    # Metodos adicionais para hierarquia
    # ========================================

    def create_frame(
        self,
        board_id: str,
        x: float,
        y: float,
        width: float,
        height: float,
        title: str = "",
        style: Optional[Dict] = None
    ) -> Dict:
        """
        Cria um frame (container) no board.
        Frames agrupam elementos visualmente.

        Args:
            board_id: ID do board
            x: Posicao X
            y: Posicao Y
            width: Largura
            height: Altura
            title: Titulo do frame
            style: Estilos customizados

        Returns:
            Dados do frame criado
        """
        logger.debug(f"Creating frame: {title}")

        data = {
            "data": {
                "title": title,
                "format": "custom",
                "type": "freeform"
            },
            "position": {
                "x": x,
                "y": y,
                "origin": "center"
            },
            "geometry": {
                "width": width,
                "height": height
            }
        }

        if style:
            data["style"] = style

        frame = self._request("POST", f"/boards/{board_id}/frames", data=data)
        logger.debug(f"Frame created: {frame.get('id')} - {title}")

        return frame

    def create_card(
        self,
        board_id: str,
        x: float,
        y: float,
        title: str,
        description: str = "",
        style: Optional[Dict] = None
    ) -> Dict:
        """
        Cria um card no board.
        Cards podem conter titulo, descricao e links.

        Args:
            board_id: ID do board
            x: Posicao X
            y: Posicao Y
            title: Titulo do card
            description: Descricao
            style: Estilos customizados

        Returns:
            Dados do card criado
        """
        logger.debug(f"Creating card: {title}")

        data = {
            "data": {
                "title": title,
                "description": description
            },
            "position": {
                "x": x,
                "y": y,
                "origin": "center"
            }
        }

        if style:
            data["style"] = style

        card = self._request("POST", f"/boards/{board_id}/cards", data=data)
        logger.debug(f"Card created: {card.get('id')} - {title}")

        return card

    def create_app_card(
        self,
        board_id: str,
        x: float,
        y: float,
        title: str,
        description: str = "",
        fields: Optional[List[Dict]] = None,
        style: Optional[Dict] = None
    ) -> Dict:
        """
        Cria um app card no board.
        App cards podem ter campos customizados.

        Args:
            board_id: ID do board
            x: Posicao X
            y: Posicao Y
            title: Titulo do card
            description: Descricao
            fields: Campos customizados [{"value": "...", "iconUrl": "..."}]
            style: Estilos customizados

        Returns:
            Dados do app card criado
        """
        logger.debug(f"Creating app card: {title}")

        data = {
            "data": {
                "title": title,
                "description": description
            },
            "position": {
                "x": x,
                "y": y,
                "origin": "center"
            }
        }

        if fields:
            data["data"]["fields"] = fields

        if style:
            data["style"] = style

        card = self._request("POST", f"/boards/{board_id}/app_cards", data=data)
        logger.debug(f"App card created: {card.get('id')} - {title}")

        return card

    def create_embed(
        self,
        board_id: str,
        x: float,
        y: float,
        url: str,
        mode: str = "inline"
    ) -> Dict:
        """
        Cria um embed (link externo) no board.
        Pode embedar URLs externas como ClickUp, Google Docs, etc.

        Args:
            board_id: ID do board
            x: Posicao X
            y: Posicao Y
            url: URL a embedar
            mode: Modo de exibicao (inline, modal)

        Returns:
            Dados do embed criado
        """
        logger.debug(f"Creating embed: {url}")

        data = {
            "data": {
                "url": url,
                "mode": mode
            },
            "position": {
                "x": x,
                "y": y,
                "origin": "center"
            }
        }

        embed = self._request("POST", f"/boards/{board_id}/embeds", data=data)
        logger.debug(f"Embed created: {embed.get('id')}")

        return embed

    def create_image(
        self,
        board_id: str,
        x: float,
        y: float,
        url: str,
        title: str = "",
        width: Optional[float] = None,
        height: Optional[float] = None
    ) -> Dict:
        """
        Cria uma imagem no board a partir de URL.

        Args:
            board_id: ID do board
            x: Posicao X
            y: Posicao Y
            url: URL da imagem
            title: Titulo da imagem
            width: Largura da imagem em pixels (opcional)
            height: Altura da imagem em pixels (opcional)

        Returns:
            Dados da imagem criada
        """
        logger.debug(f"Creating image: {url}")

        data = {
            "data": {
                "url": url,
                "title": title
            },
            "position": {
                "x": x,
                "y": y,
                "origin": "center"
            }
        }

        if width is not None or height is not None:
            data["geometry"] = {}
            if width is not None:
                data["geometry"]["width"] = width
            if height is not None:
                data["geometry"]["height"] = height

        image = self._request("POST", f"/boards/{board_id}/images", data=data)
        logger.debug(f"Image created: {image.get('id')}")

        return image

    def add_tag(
        self,
        board_id: str,
        item_id: str,
        tag_id: str
    ) -> Dict:
        """
        Adiciona tag a um item.

        Args:
            board_id: ID do board
            item_id: ID do item
            tag_id: ID da tag

        Returns:
            Dados da associacao
        """
        data = {"tagId": tag_id}
        return self._request("POST", f"/boards/{board_id}/items/{item_id}/tags", data=data)

    def create_tag(
        self,
        board_id: str,
        title: str,
        fill_color: str = "#F5F6F8"
    ) -> Dict:
        """
        Cria uma tag no board.

        Args:
            board_id: ID do board
            title: Titulo da tag
            fill_color: Cor de fundo

        Returns:
            Dados da tag criada
        """
        data = {
            "title": title,
            "fillColor": fill_color
        }

        tag = self._request("POST", f"/boards/{board_id}/tags", data=data)
        logger.debug(f"Tag created: {tag.get('id')} - {title}")

        return tag

    def list_items(
        self,
        board_id: str,
        item_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Lista itens de um board.

        Args:
            board_id: ID do board
            item_type: Tipo de item (shape, sticky_note, card, etc)
            limit: Limite de itens

        Returns:
            Lista de itens
        """
        params = {"limit": limit}
        if item_type:
            params["type"] = item_type

        response = self._request("GET", f"/boards/{board_id}/items", params=params)
        return response.get("data", [])

    def get_item(self, board_id: str, item_id: str) -> Dict:
        """
        Obtem um item especifico.

        Args:
            board_id: ID do board
            item_id: ID do item

        Returns:
            Dados do item
        """
        return self._request("GET", f"/boards/{board_id}/items/{item_id}")

    def update_item(
        self,
        board_id: str,
        item_id: str,
        data: Dict
    ) -> Dict:
        """
        Atualiza um item.

        Args:
            board_id: ID do board
            item_id: ID do item
            data: Dados a atualizar

        Returns:
            Dados do item atualizado
        """
        return self._request("PATCH", f"/boards/{board_id}/items/{item_id}", data=data)

    def delete_item(self, board_id: str, item_id: str):
        """
        Deleta um item.

        Args:
            board_id: ID do board
            item_id: ID do item
        """
        self._request("DELETE", f"/boards/{board_id}/items/{item_id}")
        logger.debug(f"Item deleted: {item_id}")

    def get_board_url(self, board_id: str) -> str:
        """
        Retorna URL do board.

        Args:
            board_id: ID do board

        Returns:
            URL completa do board
        """
        return f"https://miro.com/app/board/{board_id}"

    def create_link_to_board(
        self,
        board_id: str,
        x: float,
        y: float,
        target_board_id: str,
        title: str
    ) -> Dict:
        """
        Cria um card com link para outro board.
        Util para navegacao hierarquica entre boards.

        Args:
            board_id: ID do board atual
            x: Posicao X
            y: Posicao Y
            target_board_id: ID do board destino
            title: Titulo do link

        Returns:
            Dados do card criado
        """
        target_url = self.get_board_url(target_board_id)

        # Criar card com link
        card = self.create_card(
            board_id=board_id,
            x=x,
            y=y,
            title=title,
            description=f"Clique para abrir: {target_url}",
            style={
                "fillColor": "#E3F2FD"
            }
        )

        logger.info(f"Link card created: {title} -> {target_board_id}")
        return card

    def create_clickup_embed(
        self,
        board_id: str,
        x: float,
        y: float,
        clickup_url: str,
        title: str = "ClickUp"
    ) -> Dict:
        """
        Cria embed do ClickUp no board.

        Args:
            board_id: ID do board
            x: Posicao X
            y: Posicao Y
            clickup_url: URL do ClickUp (task, list, etc)
            title: Titulo

        Returns:
            Dados do embed/card criado
        """
        # Tentar criar embed
        try:
            return self.create_embed(board_id, x, y, clickup_url)
        except MiroAPIError:
            # Se embed falhar, criar card com link
            logger.warning("Embed failed, creating card instead")
            return self.create_card(
                board_id=board_id,
                x=x,
                y=y,
                title=title,
                description=f"ClickUp: {clickup_url}",
                style={"fillColor": "#7B68EE"}
            )
