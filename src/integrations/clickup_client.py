"""
Cliente para integracao com ClickUp via API REST.
Cria espacos, pastas, listas e tarefas com checklists e descricoes.
"""

import requests
from typing import Dict, List, Optional, Any
from config.settings import get_settings
from src.utils.exceptions import ClickUpAPIError
from src.utils.logger import get_logger

logger = get_logger()


class ClickUpClient:
    """
    Cliente para API do ClickUp.
    Permite criar estrutura organizacional e tarefas.
    """

    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(
        self,
        api_token: Optional[str] = None,
        team_id: Optional[str] = None
    ):
        """
        Inicializa cliente ClickUp.

        Args:
            api_token: Token de acesso (usa settings se nao fornecido)
            team_id: ID do time/workspace
        """
        settings = get_settings()
        self.api_token = api_token or settings.CLICKUP_API_TOKEN
        self.team_id = team_id or settings.CLICKUP_TEAM_ID

        if not self.api_token:
            logger.warning("ClickUp API token not configured")

        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }

        logger.info("ClickUp client initialized")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Faz requisicao a API do ClickUp.

        Args:
            method: Metodo HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API
            data: Dados JSON para enviar
            params: Parametros de query string

        Returns:
            Resposta JSON

        Raises:
            ClickUpAPIError: Se a requisicao falhar
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

            logger.debug(f"{method} {endpoint} - Status: {response.status_code}")

            if response.status_code >= 400:
                error_msg = f"ClickUp API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data}"
                except:
                    error_msg += f" - {response.text}"

                logger.error(error_msg)
                raise ClickUpAPIError(error_msg, status_code=response.status_code)

            return response.json() if response.text else {}

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise ClickUpAPIError(f"Request failed: {e}")

    # ========================================
    # Estrutura Organizacional
    # ========================================

    def get_teams(self) -> List[Dict]:
        """
        Lista times/workspaces do usuario.

        Returns:
            Lista de times
        """
        response = self._request("GET", "/team")
        return response.get("teams", [])

    def get_spaces(self, team_id: Optional[str] = None) -> List[Dict]:
        """
        Lista espacos de um time.

        Args:
            team_id: ID do time (usa padrao se nao fornecido)

        Returns:
            Lista de espacos
        """
        team = team_id or self.team_id
        response = self._request("GET", f"/team/{team}/space")
        return response.get("spaces", [])

    def create_space(
        self,
        name: str,
        team_id: Optional[str] = None,
        multiple_assignees: bool = True,
        features: Optional[Dict] = None
    ) -> Dict:
        """
        Cria um espaco no time.

        Args:
            name: Nome do espaco
            team_id: ID do time
            multiple_assignees: Permitir multiplos responsaveis
            features: Features habilitadas

        Returns:
            Dados do espaco criado
        """
        team = team_id or self.team_id
        logger.info(f"Creating space: {name}")

        data = {
            "name": name,
            "multiple_assignees": multiple_assignees,
            "features": features or {
                "due_dates": {"enabled": True, "start_date": True, "remap_due_dates": True},
                "time_tracking": {"enabled": True},
                "tags": {"enabled": True},
                "checklists": {"enabled": True},
                "custom_fields": {"enabled": True},
                "dependency_warning": {"enabled": True}
            }
        }

        space = self._request("POST", f"/team/{team}/space", data=data)
        logger.info(f"Space created: {space.get('id')} - {name}")

        return space

    def get_space(self, space_id: str) -> Dict:
        """
        Obtem dados de um espaco.

        Args:
            space_id: ID do espaco

        Returns:
            Dados do espaco
        """
        return self._request("GET", f"/space/{space_id}")

    def get_folders(self, space_id: str) -> List[Dict]:
        """
        Lista pastas de um espaco.

        Args:
            space_id: ID do espaco

        Returns:
            Lista de pastas
        """
        response = self._request("GET", f"/space/{space_id}/folder")
        return response.get("folders", [])

    def create_folder(
        self,
        space_id: str,
        name: str
    ) -> Dict:
        """
        Cria uma pasta no espaco.

        Args:
            space_id: ID do espaco
            name: Nome da pasta

        Returns:
            Dados da pasta criada
        """
        logger.info(f"Creating folder: {name}")

        data = {"name": name}
        folder = self._request("POST", f"/space/{space_id}/folder", data=data)
        logger.info(f"Folder created: {folder.get('id')} - {name}")

        return folder

    def get_folder(self, folder_id: str) -> Dict:
        """
        Obtem dados de uma pasta.

        Args:
            folder_id: ID da pasta

        Returns:
            Dados da pasta
        """
        return self._request("GET", f"/folder/{folder_id}")

    def get_lists(self, folder_id: str) -> List[Dict]:
        """
        Lista listas de uma pasta.

        Args:
            folder_id: ID da pasta

        Returns:
            Lista de listas
        """
        response = self._request("GET", f"/folder/{folder_id}/list")
        return response.get("lists", [])

    def create_list(
        self,
        folder_id: str,
        name: str,
        content: str = "",
        status: Optional[str] = None
    ) -> Dict:
        """
        Cria uma lista na pasta.

        Args:
            folder_id: ID da pasta
            name: Nome da lista
            content: Descricao da lista
            status: Status inicial

        Returns:
            Dados da lista criada
        """
        logger.info(f"Creating list: {name}")

        data = {
            "name": name,
            "content": content
        }

        if status:
            data["status"] = status

        list_item = self._request("POST", f"/folder/{folder_id}/list", data=data)
        logger.info(f"List created: {list_item.get('id')} - {name}")

        return list_item

    def create_folderless_list(
        self,
        space_id: str,
        name: str,
        content: str = ""
    ) -> Dict:
        """
        Cria uma lista diretamente no espaco (sem pasta).

        Args:
            space_id: ID do espaco
            name: Nome da lista
            content: Descricao da lista

        Returns:
            Dados da lista criada
        """
        logger.info(f"Creating folderless list: {name}")

        data = {
            "name": name,
            "content": content
        }

        list_item = self._request("POST", f"/space/{space_id}/list", data=data)
        logger.info(f"List created: {list_item.get('id')} - {name}")

        return list_item

    # ========================================
    # Tarefas
    # ========================================

    def get_tasks(
        self,
        list_id: str,
        include_closed: bool = False
    ) -> List[Dict]:
        """
        Lista tarefas de uma lista.

        Args:
            list_id: ID da lista
            include_closed: Incluir tarefas fechadas

        Returns:
            Lista de tarefas
        """
        params = {"include_closed": str(include_closed).lower()}
        response = self._request("GET", f"/list/{list_id}/task", params=params)
        return response.get("tasks", [])

    def create_task(
        self,
        list_id: str,
        name: str,
        description: str = "",
        assignees: Optional[List[int]] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        due_date: Optional[int] = None,
        start_date: Optional[int] = None,
        custom_fields: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict:
        """
        Cria uma tarefa na lista.

        Args:
            list_id: ID da lista
            name: Nome da tarefa
            description: Descricao (suporta Markdown)
            assignees: IDs dos responsaveis
            tags: Tags da tarefa
            status: Status inicial
            priority: Prioridade (1=Urgent, 2=High, 3=Normal, 4=Low)
            due_date: Data de vencimento (timestamp ms)
            start_date: Data de inicio (timestamp ms)
            custom_fields: Campos customizados
            **kwargs: Outros parametros

        Returns:
            Dados da tarefa criada
        """
        logger.info(f"Creating task: {name}")

        data = {
            "name": name,
            "description": description,
            "markdown_description": description
        }

        if assignees:
            data["assignees"] = assignees
        if tags:
            data["tags"] = tags
        if status:
            data["status"] = status
        if priority:
            data["priority"] = priority
        if due_date:
            data["due_date"] = due_date
        if start_date:
            data["start_date"] = start_date
        if custom_fields:
            data["custom_fields"] = custom_fields

        # Adicionar campos extras
        data.update(kwargs)

        task = self._request("POST", f"/list/{list_id}/task", data=data)
        logger.info(f"Task created: {task.get('id')} - {name}")

        return task

    def get_task(self, task_id: str) -> Dict:
        """
        Obtem dados de uma tarefa.

        Args:
            task_id: ID da tarefa

        Returns:
            Dados da tarefa
        """
        return self._request("GET", f"/task/{task_id}")

    def update_task(
        self,
        task_id: str,
        **kwargs
    ) -> Dict:
        """
        Atualiza uma tarefa.

        Args:
            task_id: ID da tarefa
            **kwargs: Campos a atualizar

        Returns:
            Dados da tarefa atualizada
        """
        return self._request("PUT", f"/task/{task_id}", data=kwargs)

    def delete_task(self, task_id: str):
        """
        Deleta uma tarefa.

        Args:
            task_id: ID da tarefa
        """
        self._request("DELETE", f"/task/{task_id}")
        logger.debug(f"Task deleted: {task_id}")

    def create_subtask(
        self,
        parent_task_id: str,
        list_id: str,
        name: str,
        description: str = "",
        **kwargs
    ) -> Dict:
        """
        Cria uma subtarefa.

        Args:
            parent_task_id: ID da tarefa pai
            list_id: ID da lista
            name: Nome da subtarefa
            description: Descricao
            **kwargs: Outros parametros

        Returns:
            Dados da subtarefa criada
        """
        logger.info(f"Creating subtask: {name}")

        data = {
            "name": name,
            "description": description,
            "parent": parent_task_id
        }
        data.update(kwargs)

        task = self._request("POST", f"/list/{list_id}/task", data=data)
        logger.info(f"Subtask created: {task.get('id')} - {name}")

        return task

    # ========================================
    # Checklists
    # ========================================

    def create_checklist(
        self,
        task_id: str,
        name: str
    ) -> Dict:
        """
        Cria um checklist em uma tarefa.

        Args:
            task_id: ID da tarefa
            name: Nome do checklist

        Returns:
            Dados do checklist criado
        """
        logger.info(f"Creating checklist: {name}")

        data = {"name": name}
        checklist = self._request("POST", f"/task/{task_id}/checklist", data=data)
        logger.debug(f"Checklist created: {checklist.get('checklist', {}).get('id')}")

        return checklist

    def create_checklist_item(
        self,
        checklist_id: str,
        name: str,
        assignee: Optional[int] = None
    ) -> Dict:
        """
        Cria um item no checklist.

        Args:
            checklist_id: ID do checklist
            name: Nome do item
            assignee: ID do responsavel

        Returns:
            Dados do item criado
        """
        data = {"name": name}
        if assignee:
            data["assignee"] = assignee

        return self._request("POST", f"/checklist/{checklist_id}/checklist_item", data=data)

    def add_checklist_with_items(
        self,
        task_id: str,
        checklist_name: str,
        items: List[str]
    ) -> Dict:
        """
        Cria checklist com todos os itens de uma vez.

        Args:
            task_id: ID da tarefa
            checklist_name: Nome do checklist
            items: Lista de itens

        Returns:
            Dados do checklist com itens
        """
        # Criar checklist
        checklist_response = self.create_checklist(task_id, checklist_name)
        checklist_id = checklist_response.get("checklist", {}).get("id")

        if not checklist_id:
            raise ClickUpAPIError("Failed to create checklist")

        # Adicionar itens
        for item in items:
            self.create_checklist_item(checklist_id, item)

        logger.info(f"Checklist created with {len(items)} items")
        return checklist_response

    # ========================================
    # Custom Fields
    # ========================================

    def get_custom_fields(self, list_id: str) -> List[Dict]:
        """
        Lista campos customizados de uma lista.

        Args:
            list_id: ID da lista

        Returns:
            Lista de campos customizados
        """
        response = self._request("GET", f"/list/{list_id}/field")
        return response.get("fields", [])

    def set_custom_field_value(
        self,
        task_id: str,
        field_id: str,
        value: Any
    ) -> Dict:
        """
        Define valor de campo customizado.

        Args:
            task_id: ID da tarefa
            field_id: ID do campo
            value: Valor a definir

        Returns:
            Resposta da API
        """
        data = {"value": value}
        return self._request("POST", f"/task/{task_id}/field/{field_id}", data=data)

    # ========================================
    # Dependencies
    # ========================================

    def add_dependency(
        self,
        task_id: str,
        depends_on: str
    ) -> Dict:
        """
        Adiciona dependencia entre tarefas.

        Args:
            task_id: ID da tarefa
            depends_on: ID da tarefa da qual depende

        Returns:
            Resposta da API
        """
        data = {
            "depends_on": depends_on
        }
        return self._request("POST", f"/task/{task_id}/dependency", data=data)

    # ========================================
    # Comments
    # ========================================

    def add_comment(
        self,
        task_id: str,
        comment_text: str,
        assignee: Optional[int] = None,
        notify_all: bool = False
    ) -> Dict:
        """
        Adiciona comentario a uma tarefa.

        Args:
            task_id: ID da tarefa
            comment_text: Texto do comentario
            assignee: ID do responsavel a mencionar
            notify_all: Notificar todos

        Returns:
            Dados do comentario criado
        """
        data = {
            "comment_text": comment_text,
            "notify_all": notify_all
        }

        if assignee:
            data["assignee"] = assignee

        return self._request("POST", f"/task/{task_id}/comment", data=data)

    # ========================================
    # Links e URLs
    # ========================================

    def add_task_link(
        self,
        task_id: str,
        links_to: str
    ) -> Dict:
        """
        Cria link entre tarefas.

        Args:
            task_id: ID da tarefa
            links_to: ID da tarefa a linkar

        Returns:
            Resposta da API
        """
        data = {"links_to": links_to}
        return self._request("POST", f"/task/{task_id}/link/{links_to}", data=data)

    def get_task_url(self, task_id: str) -> str:
        """
        Retorna URL da tarefa.

        Args:
            task_id: ID da tarefa

        Returns:
            URL completa da tarefa
        """
        return f"https://app.clickup.com/t/{task_id}"

    def get_list_url(self, list_id: str) -> str:
        """
        Retorna URL da lista.

        Args:
            list_id: ID da lista

        Returns:
            URL completa da lista
        """
        return f"https://app.clickup.com/list/{list_id}"

    # ========================================
    # Metodos auxiliares
    # ========================================

    def create_task_with_checklist(
        self,
        list_id: str,
        name: str,
        description: str,
        checklist_items: List[str],
        checklist_name: str = "Verificacao",
        **kwargs
    ) -> Dict:
        """
        Cria tarefa com checklist em uma operacao.

        Args:
            list_id: ID da lista
            name: Nome da tarefa
            description: Descricao
            checklist_items: Itens do checklist
            checklist_name: Nome do checklist
            **kwargs: Outros parametros da tarefa

        Returns:
            Dados da tarefa criada
        """
        # Criar tarefa
        task = self.create_task(list_id, name, description, **kwargs)
        task_id = task.get("id")

        # Adicionar checklist
        if task_id and checklist_items:
            self.add_checklist_with_items(task_id, checklist_name, checklist_items)

        return task

    def create_process_structure(
        self,
        space_id: str,
        process_name: str,
        activities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Cria estrutura completa para um processo.
        Folder -> List -> Tasks com checklists.

        Args:
            space_id: ID do espaco
            process_name: Nome do processo
            activities: Lista de atividades [{"name": ..., "description": ..., "checklist": [...]}]

        Returns:
            Dict com IDs criados
        """
        result = {
            "folder_id": None,
            "list_id": None,
            "task_ids": []
        }

        # Criar pasta
        folder = self.create_folder(space_id, process_name)
        result["folder_id"] = folder.get("id")

        # Criar lista de atividades
        activities_list = self.create_list(result["folder_id"], "Atividades")
        result["list_id"] = activities_list.get("id")

        # Criar tarefas
        for activity in activities:
            task = self.create_task_with_checklist(
                list_id=result["list_id"],
                name=activity.get("name", ""),
                description=activity.get("description", ""),
                checklist_items=activity.get("checklist", []),
                checklist_name=activity.get("checklist_name", "Verificacao")
            )
            result["task_ids"].append(task.get("id"))

        logger.info(f"Process structure created: {process_name}")
        return result
