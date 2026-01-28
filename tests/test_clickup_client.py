"""
Testes para o cliente ClickUp.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.integrations.clickup_client import ClickUpClient


class TestClickUpClientInit:
    """Testes de inicializacao do cliente."""

    def test_init_with_token(self):
        """Testa inicializacao com token."""
        client = ClickUpClient(api_token="test_token")
        assert client.api_token == "test_token"
        assert client.base_url == "https://api.clickup.com/api/v2"

    def test_init_without_token(self):
        """Testa inicializacao sem token (deve usar settings)."""
        with patch('src.integrations.clickup_client.get_settings') as mock_settings:
            mock_settings.return_value.CLICKUP_API_TOKEN = "settings_token"
            client = ClickUpClient()
            assert client.api_token == "settings_token"

    def test_headers(self):
        """Testa headers de autenticacao."""
        client = ClickUpClient(api_token="my_token")
        headers = client._headers()
        assert headers['Authorization'] == "my_token"
        assert headers['Content-Type'] == "application/json"


class TestClickUpClientTeams:
    """Testes de operacoes com times."""

    @patch('requests.get')
    def test_get_teams(self, mock_get):
        """Testa obtencao de times."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'teams': [
                {'id': 'team_1', 'name': 'Team 1'},
                {'id': 'team_2', 'name': 'Team 2'}
            ]
        }
        mock_get.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.get_teams()

        assert len(result['teams']) == 2
        assert result['teams'][0]['id'] == 'team_1'


class TestClickUpClientSpaces:
    """Testes de operacoes com spaces."""

    @patch('requests.get')
    def test_get_spaces(self, mock_get):
        """Testa obtencao de spaces."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'spaces': [
                {'id': 'space_1', 'name': 'Space 1'}
            ]
        }
        mock_get.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.get_spaces("team_123")

        assert len(result['spaces']) == 1
        mock_get.assert_called_once()

    @patch('requests.post')
    def test_create_space(self, mock_post):
        """Testa criacao de space."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'new_space',
            'name': 'Novo Space'
        }
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.create_space("team_123", "Novo Space")

        assert result['id'] == 'new_space'
        assert result['name'] == 'Novo Space'


class TestClickUpClientFolders:
    """Testes de operacoes com folders."""

    @patch('requests.get')
    def test_get_folders(self, mock_get):
        """Testa obtencao de folders."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'folders': [
                {'id': 'folder_1', 'name': 'Folder 1'}
            ]
        }
        mock_get.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.get_folders("space_123")

        assert len(result['folders']) == 1

    @patch('requests.post')
    def test_create_folder(self, mock_post):
        """Testa criacao de folder."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'new_folder',
            'name': 'Processo XYZ'
        }
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.create_folder("space_123", "Processo XYZ")

        assert result['id'] == 'new_folder'


class TestClickUpClientLists:
    """Testes de operacoes com lists."""

    @patch('requests.get')
    def test_get_lists(self, mock_get):
        """Testa obtencao de lists."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'lists': [
                {'id': 'list_1', 'name': 'List 1'}
            ]
        }
        mock_get.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.get_lists("folder_123")

        assert len(result['lists']) == 1

    @patch('requests.post')
    def test_create_list(self, mock_post):
        """Testa criacao de list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'new_list',
            'name': 'Atividades'
        }
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.create_list("folder_123", "Atividades")

        assert result['id'] == 'new_list'


class TestClickUpClientTasks:
    """Testes de operacoes com tasks."""

    @patch('requests.post')
    def test_create_task(self, mock_post):
        """Testa criacao de tarefa."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'task_123',
            'name': 'Atividade 1.1',
            'description': 'Descricao da atividade'
        }
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.create_task(
            list_id="list_123",
            name="Atividade 1.1",
            description="Descricao da atividade"
        )

        assert result['id'] == 'task_123'
        assert result['name'] == 'Atividade 1.1'

    @patch('requests.post')
    def test_create_task_with_all_params(self, mock_post):
        """Testa criacao de tarefa com todos os parametros."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'task_456',
            'name': 'Tarefa Completa',
            'priority': 2
        }
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.create_task(
            list_id="list_123",
            name="Tarefa Completa",
            description="Descricao",
            priority=2,
            due_date=1704067200000,
            tags=["processo", "atividade"]
        )

        assert result['id'] == 'task_456'

    @patch('requests.get')
    def test_get_task(self, mock_get):
        """Testa obtencao de tarefa."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'task_123',
            'name': 'Minha Tarefa'
        }
        mock_get.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.get_task("task_123")

        assert result['id'] == 'task_123'

    @patch('requests.put')
    def test_update_task(self, mock_put):
        """Testa atualizacao de tarefa."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'task_123',
            'name': 'Nome Atualizado'
        }
        mock_put.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.update_task("task_123", name="Nome Atualizado")

        assert result['name'] == 'Nome Atualizado'


class TestClickUpClientSubtasks:
    """Testes de operacoes com subtasks."""

    @patch('requests.post')
    def test_create_subtask(self, mock_post):
        """Testa criacao de subtarefa."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'subtask_1',
            'name': 'Subtarefa 1',
            'parent': 'task_123'
        }
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.create_subtask(
            parent_task_id="task_123",
            list_id="list_123",
            name="Subtarefa 1"
        )

        assert result['id'] == 'subtask_1'
        assert result['parent'] == 'task_123'


class TestClickUpClientChecklists:
    """Testes de operacoes com checklists."""

    @patch('requests.post')
    def test_create_checklist(self, mock_post):
        """Testa criacao de checklist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'checklist': {
                'id': 'checklist_1',
                'name': 'Verificacoes'
            }
        }
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.create_checklist("task_123", "Verificacoes")

        assert result['checklist']['id'] == 'checklist_1'

    @patch('requests.post')
    def test_add_checklist_item(self, mock_post):
        """Testa adicao de item ao checklist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'checklist': {
                'id': 'checklist_1',
                'items': [{'name': 'Item 1'}]
            }
        }
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.add_checklist_item("checklist_1", "Item 1")

        assert 'checklist' in result

    @patch('requests.post')
    def test_add_checklist_with_items(self, mock_post):
        """Testa criacao de checklist com items."""
        # Mock para criar checklist
        mock_response_checklist = Mock()
        mock_response_checklist.status_code = 200
        mock_response_checklist.json.return_value = {
            'checklist': {
                'id': 'checklist_1',
                'name': 'Checklist Completo'
            }
        }

        # Mock para adicionar items
        mock_response_item = Mock()
        mock_response_item.status_code = 200
        mock_response_item.json.return_value = {'checklist': {'id': 'checklist_1'}}

        mock_post.side_effect = [mock_response_checklist, mock_response_item, mock_response_item]

        client = ClickUpClient(api_token="test")
        result = client.add_checklist_with_items(
            task_id="task_123",
            checklist_name="Checklist Completo",
            items=["Item 1", "Item 2"]
        )

        assert result['checklist']['id'] == 'checklist_1'
        assert mock_post.call_count == 3  # 1 criacao + 2 items


class TestClickUpClientComments:
    """Testes de operacoes com comentarios."""

    @patch('requests.post')
    def test_add_comment(self, mock_post):
        """Testa adicao de comentario."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'comment_1',
            'comment_text': 'Meu comentario'
        }
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.add_comment("task_123", "Meu comentario")

        assert result['id'] == 'comment_1'

    @patch('requests.get')
    def test_get_comments(self, mock_get):
        """Testa obtencao de comentarios."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'comments': [
                {'id': 'c1', 'comment_text': 'Comentario 1'},
                {'id': 'c2', 'comment_text': 'Comentario 2'}
            ]
        }
        mock_get.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.get_comments("task_123")

        assert len(result['comments']) == 2


class TestClickUpClientDependencies:
    """Testes de operacoes com dependencias."""

    @patch('requests.post')
    def test_add_dependency(self, mock_post):
        """Testa adicao de dependencia."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        client = ClickUpClient(api_token="test")
        result = client.add_dependency(
            task_id="task_2",
            depends_on_task_id="task_1"
        )

        assert result == {}


class TestClickUpClientProcessStructure:
    """Testes de criacao de estrutura de processo."""

    @patch.object(ClickUpClient, 'create_folder')
    @patch.object(ClickUpClient, 'create_list')
    @patch.object(ClickUpClient, 'create_task')
    @patch.object(ClickUpClient, 'add_checklist_with_items')
    def test_create_process_structure(
        self, mock_checklist, mock_task, mock_list, mock_folder
    ):
        """Testa criacao de estrutura completa de processo."""
        mock_folder.return_value = {'id': 'folder_1'}
        mock_list.return_value = {'id': 'list_1'}
        mock_task.return_value = {'id': 'task_1', 'name': 'Atividade 1'}
        mock_checklist.return_value = {'checklist': {'id': 'cl_1'}}

        client = ClickUpClient(api_token="test")

        activities = [
            {
                'name': 'Analisar Pedido',
                'numbering': '1.1',
                'actor': 'Analista',
                'description': 'Analisa o pedido recebido',
                'checklist_items': ['Verificar dados', 'Validar informacoes']
            }
        ]

        result = client.create_process_structure(
            space_id="space_123",
            process_name="Processo de Vendas",
            activities=activities
        )

        assert result['folder_id'] == 'folder_1'
        assert result['list_id'] == 'list_1'
        assert len(result['tasks']) == 1
        mock_folder.assert_called_once()
        mock_list.assert_called_once()
        mock_task.assert_called_once()
        mock_checklist.assert_called_once()


class TestClickUpClientErrorHandling:
    """Testes de tratamento de erros."""

    @patch('requests.get')
    def test_handle_api_error(self, mock_get):
        """Testa tratamento de erro de API."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'err': 'Unauthorized'}
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_get.return_value = mock_response

        client = ClickUpClient(api_token="invalid_token")

        with pytest.raises(Exception):
            client.get_teams()

    @patch('requests.get')
    def test_handle_not_found(self, mock_get):
        """Testa tratamento de recurso nao encontrado."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'err': 'Resource not found'}
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        client = ClickUpClient(api_token="test")

        with pytest.raises(Exception):
            client.get_task("nonexistent_task")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
