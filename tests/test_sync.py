"""
Testes para o modulo de sincronizacao Miro-ClickUp.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.sync.miro_clickup_sync import MiroClickUpSync, SyncResult
from src.models.process_model import Process, ProcessElement, ProcessIntegrationMetadata
from src.models.hierarchy_model import (
    OrganizationHierarchy, ValueChain, Macroprocess, SIPOC, SIPOCItem
)


class TestSyncResult:
    """Testes para a classe SyncResult."""

    def test_create_sync_result(self):
        """Testa criacao de resultado de sincronizacao."""
        result = SyncResult(
            success=True,
            operation='test_operation'
        )

        assert result.success is True
        assert result.operation == 'test_operation'
        assert result.miro_board_id is None
        assert result.errors == []

    def test_add_error(self):
        """Testa adicao de erro."""
        result = SyncResult(success=True, operation='test')
        result.add_error("Erro de teste")

        assert result.success is False
        assert len(result.errors) == 1
        assert "Erro de teste" in result.errors

    def test_add_warning(self):
        """Testa adicao de aviso."""
        result = SyncResult(success=True, operation='test')
        result.add_warning("Aviso de teste")

        assert result.success is True  # Warning nao muda success
        assert len(result.warnings) == 1

    def test_to_dict(self):
        """Testa conversao para dicionario."""
        result = SyncResult(
            success=True,
            operation='test_op',
            miro_board_id='board_123',
            miro_board_url='https://miro.com/board/123',
            clickup_space_id='space_456'
        )

        d = result.to_dict()

        assert d['success'] is True
        assert d['operation'] == 'test_op'
        assert d['miro']['board_id'] == 'board_123'
        assert d['clickup']['space_id'] == 'space_456'


class TestMiroClickUpSyncInit:
    """Testes de inicializacao do sincronizador."""

    def test_init_with_clients(self):
        """Testa inicializacao com clientes fornecidos."""
        mock_miro = Mock()
        mock_clickup = Mock()

        sync = MiroClickUpSync(
            miro_client=mock_miro,
            clickup_client=mock_clickup
        )

        assert sync.miro == mock_miro
        assert sync.clickup == mock_clickup

    def test_init_without_clickup(self):
        """Testa inicializacao sem cliente ClickUp."""
        mock_miro = Mock()

        sync = MiroClickUpSync(miro_client=mock_miro)

        assert sync.miro == mock_miro
        assert sync.clickup is None


class TestMiroClickUpSyncProcess:
    """Testes de sincronizacao de processo."""

    def _create_mock_process(self):
        """Cria um processo mock para testes."""
        element1 = ProcessElement(
            id="elem_1",
            name="Analisar Pedido",
            type="task",
            actor="Analista"
        )
        element2 = ProcessElement(
            id="elem_2",
            name="Aprovar Pedido",
            type="task",
            actor="Gerente"
        )

        process = Process(
            name="Processo de Vendas",
            process_id="PROC-001",
            elements=[element1, element2],
            actors=["Analista", "Gerente"]
        )

        return process

    @patch('src.sync.miro_clickup_sync.MiroClient')
    @patch('src.sync.miro_clickup_sync.ProcessLayout')
    @patch('src.sync.miro_clickup_sync.VisualToMiroConverter')
    @patch('src.sync.miro_clickup_sync.POPGenerator')
    @patch('src.sync.miro_clickup_sync.ITGenerator')
    @patch('src.sync.miro_clickup_sync.ChecklistGenerator')
    def test_sync_process_miro_only(
        self, mock_cl_gen, mock_it_gen, mock_pop_gen,
        mock_converter, mock_layout, mock_miro_class
    ):
        """Testa sincronizacao apenas para Miro."""
        # Setup mocks
        mock_miro = Mock()
        mock_miro.create_board.return_value = {'id': 'board_123'}
        mock_miro.get_board_url.return_value = 'https://miro.com/board_123'

        mock_converter_instance = Mock()
        mock_converter_instance.convert_and_upload.return_value = {'elem_1': 'miro_1'}
        mock_converter.return_value = mock_converter_instance

        mock_layout_instance = Mock()
        mock_layout_instance.create_layout.return_value = Mock()
        mock_layout.return_value = mock_layout_instance

        mock_pop_gen.return_value.generate.return_value = Mock(code='POP-001')
        mock_it_gen.return_value.generate_for_activity.return_value = Mock()
        mock_cl_gen.return_value.generate_for_activity.return_value = Mock()

        process = self._create_mock_process()

        sync = MiroClickUpSync(miro_client=mock_miro, clickup_client=None)

        result = sync.sync_process_to_both(
            process,
            create_miro_board=True,
            create_clickup_tasks=False
        )

        assert result.success is True
        assert result.miro_board_id == 'board_123'
        assert result.miro_board_url == 'https://miro.com/board_123'

    @patch('src.sync.miro_clickup_sync.ProcessLayout')
    @patch('src.sync.miro_clickup_sync.VisualToMiroConverter')
    @patch('src.sync.miro_clickup_sync.POPGenerator')
    @patch('src.sync.miro_clickup_sync.ITGenerator')
    @patch('src.sync.miro_clickup_sync.ChecklistGenerator')
    def test_sync_process_both_platforms(
        self, mock_cl_gen, mock_it_gen, mock_pop_gen,
        mock_converter, mock_layout
    ):
        """Testa sincronizacao para ambas plataformas."""
        # Setup Miro mock
        mock_miro = Mock()
        mock_miro.create_board.return_value = {'id': 'board_123'}
        mock_miro.get_board_url.return_value = 'https://miro.com/board_123'
        mock_miro.create_frame.return_value = {'id': 'frame_1'}

        # Setup ClickUp mock
        mock_clickup = Mock()
        mock_clickup.create_folder.return_value = {'id': 'folder_1'}
        mock_clickup.create_list.return_value = {'id': 'list_1'}
        mock_clickup.create_task.return_value = {'id': 'task_1'}
        mock_clickup.add_checklist_with_items.return_value = {'checklist': {'id': 'cl_1'}}
        mock_clickup.create_process_structure.return_value = {
            'folder_id': 'folder_1',
            'list_id': 'list_1',
            'tasks': [{'id': 'task_1'}, {'id': 'task_2'}]
        }
        mock_clickup.add_comment.return_value = {}

        # Setup other mocks
        mock_converter_instance = Mock()
        mock_converter_instance.convert_and_upload.return_value = {'elem_1': 'miro_1'}
        mock_converter.return_value = mock_converter_instance

        mock_layout_instance = Mock()
        mock_layout_instance.create_layout.return_value = Mock()
        mock_layout.return_value = mock_layout_instance

        mock_pop = Mock()
        mock_pop.code = 'POP-001'
        mock_pop_gen.return_value.generate.return_value = mock_pop

        mock_it = Mock()
        mock_it_gen.return_value.generate_for_activity.return_value = mock_it
        mock_it_gen.return_value.to_markdown.return_value = "# IT"

        mock_cl = Mock()
        mock_cl.items = []
        mock_cl_gen.return_value.generate_for_activity.return_value = mock_cl

        process = self._create_mock_process()

        sync = MiroClickUpSync(miro_client=mock_miro, clickup_client=mock_clickup)

        result = sync.sync_process_to_both(
            process,
            space_id='space_123',
            create_miro_board=True,
            create_clickup_tasks=True
        )

        assert result.success is True
        assert result.miro_board_id == 'board_123'
        assert result.clickup_folder_id == 'folder_1'
        assert result.clickup_list_id == 'list_1'

    def test_sync_process_no_space_id_warning(self):
        """Testa aviso quando space_id nao e fornecido."""
        mock_miro = Mock()
        mock_miro.create_board.return_value = {'id': 'board_1'}
        mock_miro.get_board_url.return_value = 'https://miro.com/board_1'

        mock_clickup = Mock()

        process = self._create_mock_process()

        with patch('src.sync.miro_clickup_sync.ProcessLayout'):
            with patch('src.sync.miro_clickup_sync.VisualToMiroConverter') as mock_conv:
                mock_conv.return_value.convert_and_upload.return_value = {}
                with patch('src.sync.miro_clickup_sync.POPGenerator'):
                    with patch('src.sync.miro_clickup_sync.ITGenerator'):
                        with patch('src.sync.miro_clickup_sync.ChecklistGenerator'):
                            sync = MiroClickUpSync(
                                miro_client=mock_miro,
                                clickup_client=mock_clickup
                            )

                            result = sync.sync_process_to_both(
                                process,
                                space_id=None,  # Sem space_id
                                create_clickup_tasks=True
                            )

        assert len(result.warnings) > 0
        assert any('space_id' in w for w in result.warnings)


class TestMiroClickUpSyncValueChain:
    """Testes de sincronizacao de Cadeia de Valor."""

    def _create_mock_hierarchy(self):
        """Cria uma hierarquia mock para testes."""
        value_chain = ValueChain(
            name="Empresa Teste",
            primary_macroprocesses=["macro_vendas"],
            support_macroprocesses=["macro_ti"]
        )

        macros = {
            "macro_vendas": Macroprocess(
                id="macro_vendas",
                name="Vendas",
                type="primario"
            ),
            "macro_ti": Macroprocess(
                id="macro_ti",
                name="TI",
                type="apoio"
            )
        }

        return OrganizationHierarchy(
            name="Empresa Teste",
            value_chain=value_chain,
            macroprocesses=macros
        )

    @patch('src.sync.miro_clickup_sync.ValueChainLayout')
    @patch('src.sync.miro_clickup_sync.VisualToMiroConverter')
    def test_sync_value_chain(self, mock_converter, mock_layout):
        """Testa sincronizacao de Cadeia de Valor."""
        mock_miro = Mock()
        mock_miro.create_board.return_value = {'id': 'vc_board'}
        mock_miro.get_board_url.return_value = 'https://miro.com/vc_board'

        mock_layout_instance = Mock()
        mock_layout_instance.create_layout.return_value = Mock()
        mock_layout.return_value = mock_layout_instance

        mock_converter_instance = Mock()
        mock_converter_instance.convert_and_upload.return_value = {}
        mock_converter.return_value = mock_converter_instance

        hierarchy = self._create_mock_hierarchy()

        with patch.object(MiroClickUpSync, '_sync_macroprocess') as mock_sync_macro:
            mock_sync_macro.return_value = SyncResult(success=True, operation='sync_macro')

            sync = MiroClickUpSync(miro_client=mock_miro)
            result = sync.sync_value_chain(hierarchy)

        assert result.success is True
        assert result.miro_board_id == 'vc_board'

    def test_sync_value_chain_no_vc(self):
        """Testa erro quando hierarquia nao tem Cadeia de Valor."""
        hierarchy = OrganizationHierarchy(name="Teste", value_chain=None)

        sync = MiroClickUpSync(miro_client=Mock())
        result = sync.sync_value_chain(hierarchy)

        assert result.success is False
        assert len(result.errors) > 0


class TestMiroClickUpSyncMacroprocess:
    """Testes de sincronizacao de Macroprocesso."""

    @patch('src.sync.miro_clickup_sync.SIPOCLayout')
    @patch('src.sync.miro_clickup_sync.VisualToMiroConverter')
    def test_sync_macroprocess_with_sipoc(self, mock_converter, mock_layout):
        """Testa sincronizacao de macroprocesso com SIPOC."""
        mock_miro = Mock()
        mock_miro.create_board.return_value = {'id': 'macro_board'}
        mock_miro.get_board_url.return_value = 'https://miro.com/macro_board'

        mock_layout_instance = Mock()
        mock_layout_instance.create_layout.return_value = Mock()
        mock_layout.return_value = mock_layout_instance

        mock_converter_instance = Mock()
        mock_converter_instance.convert_and_upload.return_value = {}
        mock_converter.return_value = mock_converter_instance

        sipoc = SIPOC(
            suppliers=[SIPOCItem(name="Fornecedor")],
            process_steps=["Etapa 1", "Etapa 2"]
        )

        macro = Macroprocess(
            id="macro_1",
            name="Macroprocesso Teste",
            type="primario",
            sipoc=sipoc
        )

        sync = MiroClickUpSync(miro_client=mock_miro)
        result = sync.sync_macroprocess(macro)

        assert result.success is True
        assert result.miro_board_id == 'macro_board'

    def test_sync_macroprocess_with_clickup(self):
        """Testa sincronizacao de macroprocesso com ClickUp."""
        mock_miro = Mock()
        mock_miro.create_board.return_value = {'id': 'macro_board'}
        mock_miro.get_board_url.return_value = 'https://miro.com/macro_board'

        mock_clickup = Mock()
        mock_clickup.create_folder.return_value = {'id': 'folder_macro'}

        macro = Macroprocess(
            id="macro_1",
            name="Macroprocesso Teste",
            type="primario"
        )

        sync = MiroClickUpSync(miro_client=mock_miro, clickup_client=mock_clickup)
        result = sync.sync_macroprocess(macro, space_id='space_123')

        assert result.success is True
        assert result.clickup_folder_id == 'folder_macro'
        mock_clickup.create_folder.assert_called_once()


class TestMiroClickUpSyncCrossReferences:
    """Testes de referencias cruzadas."""

    def test_add_miro_links_to_clickup(self):
        """Testa adicao de links do Miro no ClickUp."""
        mock_miro = Mock()
        mock_clickup = Mock()
        mock_clickup.add_comment.return_value = {}

        metadata = ProcessIntegrationMetadata(
            miro_board_id='board_1',
            miro_board_url='https://miro.com/board_1',
            miro_element_ids={'elem_1': 'miro_item_1'},
            clickup_task_ids={'elem_1': 'task_1'}
        )

        sync = MiroClickUpSync(miro_client=mock_miro, clickup_client=mock_clickup)
        result = sync.add_miro_links_to_clickup(metadata)

        assert result.success is True
        mock_clickup.add_comment.assert_called_once()

    def test_add_miro_links_no_url(self):
        """Testa erro quando URL do Miro nao esta disponivel."""
        mock_miro = Mock()
        mock_clickup = Mock()

        metadata = ProcessIntegrationMetadata(
            miro_board_id='board_1',
            miro_board_url=None  # Sem URL
        )

        sync = MiroClickUpSync(miro_client=mock_miro, clickup_client=mock_clickup)
        result = sync.add_miro_links_to_clickup(metadata)

        assert result.success is False
        assert len(result.errors) > 0


class TestMiroClickUpSyncMetadata:
    """Testes de geracao de metadata."""

    def test_generate_integration_metadata(self):
        """Testa geracao de metadata de integracao."""
        mock_miro = Mock()

        process = Process(name="Processo Teste")

        sync_result = SyncResult(
            success=True,
            operation='test',
            miro_board_id='board_1',
            miro_board_url='https://miro.com/board_1',
            miro_item_ids={'elem_1': 'miro_1'},
            clickup_space_id='space_1',
            clickup_folder_id='folder_1',
            clickup_list_id='list_1',
            clickup_task_ids={'elem_1': 'task_1'}
        )
        sync_result.metadata['pop_code'] = 'POP-001'

        sync = MiroClickUpSync(miro_client=mock_miro)
        metadata = sync.generate_integration_metadata(process, sync_result)

        assert metadata.miro_board_id == 'board_1'
        assert metadata.miro_board_url == 'https://miro.com/board_1'
        assert metadata.clickup_space_id == 'space_1'
        assert metadata.pop_code == 'POP-001'
        assert 'elem_1' in metadata.miro_element_ids
        assert 'elem_1' in metadata.clickup_task_ids


class TestSyncProcessFunction:
    """Testes para funcao utilitaria sync_process."""

    @patch('src.sync.miro_clickup_sync.MiroClient')
    @patch('src.sync.miro_clickup_sync.ClickUpClient')
    @patch.object(MiroClickUpSync, 'sync_process_to_both')
    def test_sync_process_helper(self, mock_sync, mock_clickup_class, mock_miro_class):
        """Testa funcao helper sync_process."""
        from src.sync.miro_clickup_sync import sync_process

        mock_sync.return_value = SyncResult(success=True, operation='test')

        process = Process(name="Teste")
        result = sync_process(
            process,
            miro_token="miro_token",
            clickup_token="clickup_token",
            space_id="space_1"
        )

        assert result.success is True
        mock_miro_class.assert_called_once_with(api_token="miro_token")
        mock_clickup_class.assert_called_once_with(api_token="clickup_token")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
