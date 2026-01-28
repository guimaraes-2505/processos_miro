"""
Sincronizacao entre Miro e ClickUp.
Mantem referencias cruzadas entre boards Miro e tarefas ClickUp.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.process_model import Process, ProcessElement, ProcessIntegrationMetadata
from src.models.hierarchy_model import (
    OrganizationHierarchy, ValueChain, Macroprocess, SIPOC
)
from src.models.documentation_model import POP, IT, Checklist
from src.models.visual_model import VisualDiagram
from src.integrations.miro_client import MiroClient
from src.integrations.clickup_client import ClickUpClient
from src.layout.value_chain_layout import ValueChainLayout
from src.layout.sipoc_layout import SIPOCLayout
from src.layout.process_layout import ProcessLayout
from src.converters.visual_to_miro import VisualToMiroConverter
from src.generators.pop_generator import POPGenerator
from src.generators.it_generator import ITGenerator
from src.generators.checklist_generator import ChecklistGenerator
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class SyncResult:
    """Resultado de uma operacao de sincronizacao."""

    success: bool
    operation: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Referencias Miro
    miro_board_id: Optional[str] = None
    miro_board_url: Optional[str] = None
    miro_item_ids: Dict[str, str] = field(default_factory=dict)

    # Referencias ClickUp
    clickup_space_id: Optional[str] = None
    clickup_folder_id: Optional[str] = None
    clickup_list_id: Optional[str] = None
    clickup_task_ids: Dict[str, str] = field(default_factory=dict)

    # Erros e avisos
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Metadata adicional
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Adiciona um erro ao resultado."""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str) -> None:
        """Adiciona um aviso ao resultado."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario."""
        return {
            'success': self.success,
            'operation': self.operation,
            'timestamp': self.timestamp.isoformat(),
            'miro': {
                'board_id': self.miro_board_id,
                'board_url': self.miro_board_url,
                'item_ids': self.miro_item_ids
            },
            'clickup': {
                'space_id': self.clickup_space_id,
                'folder_id': self.clickup_folder_id,
                'list_id': self.clickup_list_id,
                'task_ids': self.clickup_task_ids
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


class MiroClickUpSync:
    """
    Sincronizador entre Miro e ClickUp.

    Responsabilidades:
    - Criar boards Miro com layouts hierarquicos
    - Criar estrutura de tarefas no ClickUp
    - Manter referencias cruzadas entre as plataformas
    - Gerar documentacao (POP, IT, Checklist) para ambas
    """

    def __init__(
        self,
        miro_client: Optional[MiroClient] = None,
        clickup_client: Optional[ClickUpClient] = None
    ):
        """
        Inicializa o sincronizador.

        Args:
            miro_client: Cliente Miro (opcional, cria novo se nao fornecido)
            clickup_client: Cliente ClickUp (opcional, cria novo se nao fornecido)
        """
        self.miro = miro_client or MiroClient()
        self.clickup = clickup_client

        # Layouts
        self.value_chain_layout = ValueChainLayout()
        self.sipoc_layout = SIPOCLayout()
        self.process_layout = ProcessLayout()

        # Geradores de documentacao
        self.pop_generator = POPGenerator()
        self.it_generator = ITGenerator()
        self.checklist_generator = ChecklistGenerator()

        # Conversor visual -> Miro
        self.miro_converter = VisualToMiroConverter()

    def sync_process_to_both(
        self,
        process: Process,
        space_id: Optional[str] = None,
        create_miro_board: bool = True,
        create_clickup_tasks: bool = True,
        generate_documentation: bool = True,
        **kwargs
    ) -> SyncResult:
        """
        Sincroniza um processo para Miro e ClickUp.

        Args:
            process: Processo a sincronizar
            space_id: ID do space no ClickUp (obrigatorio se create_clickup_tasks=True)
            create_miro_board: Se deve criar board no Miro
            create_clickup_tasks: Se deve criar tarefas no ClickUp
            generate_documentation: Se deve gerar documentacao automatica
            **kwargs: Argumentos adicionais

        Returns:
            SyncResult com referencias e status
        """
        logger.info(f"Iniciando sincronizacao do processo: {process.name}")

        result = SyncResult(
            success=True,
            operation='sync_process_to_both',
            metadata={'process_name': process.name, 'process_id': process.process_id}
        )

        # Gerar documentacao se solicitado
        pop = None
        its = {}
        checklists = {}

        if generate_documentation:
            try:
                pop = self.pop_generator.generate(process)
                result.metadata['pop_code'] = pop.code

                # Gerar IT e Checklist para cada tarefa
                for element in process.elements:
                    if element.is_task():
                        it = self.it_generator.generate_for_activity(element, process)
                        its[element.id] = it

                        cl = self.checklist_generator.generate_for_activity(element, process)
                        checklists[element.id] = cl

                logger.info(f"Documentacao gerada: 1 POP, {len(its)} ITs, {len(checklists)} Checklists")

            except Exception as e:
                result.add_warning(f"Erro ao gerar documentacao: {str(e)}")

        # Criar board no Miro
        if create_miro_board:
            try:
                miro_result = self._create_miro_board(process, pop, **kwargs)
                result.miro_board_id = miro_result.get('board_id')
                result.miro_board_url = miro_result.get('board_url')
                result.miro_item_ids = miro_result.get('item_ids', {})
                logger.info(f"Board Miro criado: {result.miro_board_url}")

            except Exception as e:
                result.add_error(f"Erro ao criar board Miro: {str(e)}")

        # Criar tarefas no ClickUp
        if create_clickup_tasks and self.clickup:
            if not space_id:
                result.add_warning("space_id nao fornecido, pulando criacao no ClickUp")
            else:
                try:
                    clickup_result = self._create_clickup_structure(
                        process, space_id, its, checklists,
                        miro_board_url=result.miro_board_url,
                        **kwargs
                    )
                    result.clickup_space_id = space_id
                    result.clickup_folder_id = clickup_result.get('folder_id')
                    result.clickup_list_id = clickup_result.get('list_id')
                    result.clickup_task_ids = clickup_result.get('task_ids', {})
                    logger.info(f"Estrutura ClickUp criada: folder={result.clickup_folder_id}")

                except Exception as e:
                    result.add_error(f"Erro ao criar estrutura ClickUp: {str(e)}")

        # Adicionar links cruzados
        if result.miro_board_url and result.clickup_list_id:
            try:
                self._add_cross_references(
                    result.miro_board_id,
                    result.clickup_list_id,
                    result.miro_item_ids,
                    result.clickup_task_ids
                )
                logger.info("Referencias cruzadas adicionadas")

            except Exception as e:
                result.add_warning(f"Erro ao adicionar referencias cruzadas: {str(e)}")

        return result

    def sync_value_chain(
        self,
        hierarchy: OrganizationHierarchy,
        space_id: Optional[str] = None,
        **kwargs
    ) -> SyncResult:
        """
        Sincroniza uma Cadeia de Valor completa.

        Args:
            hierarchy: Hierarquia organizacional com Cadeia de Valor
            space_id: ID do space no ClickUp
            **kwargs: Argumentos adicionais

        Returns:
            SyncResult com referencias
        """
        logger.info(f"Sincronizando Cadeia de Valor: {hierarchy.value_chain.name if hierarchy.value_chain else 'N/A'}")

        result = SyncResult(
            success=True,
            operation='sync_value_chain'
        )

        if not hierarchy.value_chain:
            result.add_error("Hierarquia nao possui Cadeia de Valor")
            return result

        try:
            # Criar board de Cadeia de Valor no Miro
            vc_diagram = self.value_chain_layout.create_layout(
                hierarchy.value_chain,
                hierarchy.macroprocesses
            )

            board_name = f"Cadeia de Valor - {hierarchy.value_chain.name}"
            board_result = self.miro.create_board(board_name)
            board_id = board_result.get('id')

            if board_id:
                # Renderizar diagrama no board
                miro_items = self.miro_converter.convert_and_upload(
                    self.miro, board_id, vc_diagram
                )

                result.miro_board_id = board_id
                result.miro_board_url = self.miro.get_board_url(board_id)
                result.miro_item_ids = miro_items

                # Criar boards para cada macroprocesso
                macro_boards = {}
                for macro_id, macro in hierarchy.macroprocesses.items():
                    macro_result = self._sync_macroprocess(
                        macro, hierarchy, space_id, **kwargs
                    )
                    macro_boards[macro_id] = macro_result
                    result.metadata[f'macro_{macro_id}'] = macro_result.to_dict()

                result.metadata['macro_boards'] = {
                    mid: mb.miro_board_url for mid, mb in macro_boards.items()
                }

        except Exception as e:
            result.add_error(f"Erro ao sincronizar Cadeia de Valor: {str(e)}")

        return result

    def sync_macroprocess(
        self,
        macroprocess: Macroprocess,
        sipoc: Optional[SIPOC] = None,
        space_id: Optional[str] = None,
        **kwargs
    ) -> SyncResult:
        """
        Sincroniza um Macroprocesso.

        Args:
            macroprocess: Macroprocesso a sincronizar
            sipoc: SIPOC do macroprocesso (opcional)
            space_id: ID do space no ClickUp
            **kwargs: Argumentos adicionais

        Returns:
            SyncResult com referencias
        """
        logger.info(f"Sincronizando Macroprocesso: {macroprocess.name}")

        result = SyncResult(
            success=True,
            operation='sync_macroprocess',
            metadata={'macroprocess_id': macroprocess.id, 'macroprocess_name': macroprocess.name}
        )

        try:
            # Usar SIPOC do macroprocesso se nao fornecido
            sipoc = sipoc or macroprocess.sipoc

            # Criar board no Miro
            board_name = f"MACRO - {macroprocess.name}"
            board_result = self.miro.create_board(board_name)
            board_id = board_result.get('id')

            if board_id:
                result.miro_board_id = board_id
                result.miro_board_url = self.miro.get_board_url(board_id)

                # Se tiver SIPOC, criar layout
                if sipoc:
                    sipoc_diagram = self.sipoc_layout.create_layout(
                        sipoc, macroprocess.name
                    )
                    miro_items = self.miro_converter.convert_and_upload(
                        self.miro, board_id, sipoc_diagram
                    )
                    result.miro_item_ids = miro_items

                # Criar space no ClickUp se solicitado
                if self.clickup and space_id:
                    folder_result = self.clickup.create_folder(
                        space_id, macroprocess.name
                    )
                    result.clickup_folder_id = folder_result.get('id')
                    result.clickup_space_id = space_id

        except Exception as e:
            result.add_error(f"Erro ao sincronizar Macroprocesso: {str(e)}")

        return result

    def _sync_macroprocess(
        self,
        macroprocess: Macroprocess,
        hierarchy: OrganizationHierarchy,
        space_id: Optional[str],
        **kwargs
    ) -> SyncResult:
        """Metodo interno para sincronizar macroprocesso dentro de hierarquia."""
        return self.sync_macroprocess(
            macroprocess,
            macroprocess.sipoc,
            space_id,
            **kwargs
        )

    def _create_miro_board(
        self,
        process: Process,
        pop: Optional[POP] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria board no Miro para um processo.

        Returns:
            Dict com board_id, board_url, item_ids
        """
        # Criar o board
        board_name = f"PROC - {process.name}"
        if process.process_id:
            board_name = f"{process.process_id} - {process.name}"

        board_result = self.miro.create_board(board_name)
        board_id = board_result.get('id')

        if not board_id:
            raise ValueError("Falha ao criar board no Miro")

        # Gerar layout do processo
        diagram = self.process_layout.create_layout(process)

        # Converter e enviar para Miro
        item_ids = self.miro_converter.convert_and_upload(
            self.miro, board_id, diagram
        )

        # Adicionar frame com info do POP se disponivel
        if pop:
            self.miro.create_frame(
                board_id,
                x=-300, y=0,
                width=250, height=200,
                title=f"POP: {pop.code}"
            )

        return {
            'board_id': board_id,
            'board_url': self.miro.get_board_url(board_id),
            'item_ids': item_ids
        }

    def _create_clickup_structure(
        self,
        process: Process,
        space_id: str,
        its: Dict[str, IT],
        checklists: Dict[str, Checklist],
        miro_board_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria estrutura no ClickUp para um processo.

        Returns:
            Dict com folder_id, list_id, task_ids
        """
        if not self.clickup:
            raise ValueError("ClickUp client nao configurado")

        # Preparar atividades para o ClickUp
        activities = []
        for element in process.elements:
            if element.is_task():
                it = its.get(element.id)
                cl = checklists.get(element.id)

                # Gerar descricao da tarefa a partir da IT
                description = ""
                if it:
                    description = self.it_generator.to_markdown(it)

                # Preparar checklist items
                checklist_items = []
                if cl:
                    checklist_items = [item.description for item in cl.items]

                activities.append({
                    'name': element.name,
                    'numbering': element.numbering or "",
                    'actor': element.actor or "",
                    'description': description,
                    'checklist_items': checklist_items,
                    'element_id': element.id
                })

        # Criar estrutura completa no ClickUp
        result = self.clickup.create_process_structure(
            space_id=space_id,
            process_name=process.name,
            activities=activities
        )

        folder_id = result.get('folder_id')
        list_id = result.get('list_id')
        task_ids = {a['element_id']: result['tasks'][i]['id'] for i, a in enumerate(activities) if i < len(result.get('tasks', []))}

        # Adicionar link do Miro em cada tarefa
        if miro_board_url:
            for task_id in task_ids.values():
                try:
                    self.clickup.add_comment(
                        task_id,
                        f"📊 [Board Miro do Processo]({miro_board_url})"
                    )
                except Exception:
                    pass

        return {
            'folder_id': folder_id,
            'list_id': list_id,
            'task_ids': task_ids
        }

    def _add_cross_references(
        self,
        miro_board_id: str,
        clickup_list_id: str,
        miro_item_ids: Dict[str, str],
        clickup_task_ids: Dict[str, str]
    ) -> None:
        """Adiciona referencias cruzadas entre Miro e ClickUp."""
        # Adicionar embed do ClickUp no board Miro
        clickup_url = f"https://app.clickup.com/list/{clickup_list_id}"

        try:
            self.miro.create_clickup_embed(
                miro_board_id,
                x=-300, y=250,
                clickup_url=clickup_url,
                title="Tarefas no ClickUp"
            )
        except Exception as e:
            logger.warning(f"Nao foi possivel criar embed ClickUp no Miro: {e}")

    def update_clickup_from_miro(
        self,
        board_id: str,
        list_id: str,
        element_mapping: Dict[str, str]
    ) -> SyncResult:
        """
        Atualiza tarefas ClickUp com base em mudancas no Miro.

        Args:
            board_id: ID do board Miro
            list_id: ID da lista ClickUp
            element_mapping: Mapeamento element_id -> task_id

        Returns:
            SyncResult com status
        """
        logger.info(f"Atualizando ClickUp a partir do board Miro: {board_id}")

        result = SyncResult(
            success=True,
            operation='update_clickup_from_miro',
            metadata={'miro_board_id': board_id, 'clickup_list_id': list_id}
        )

        if not self.clickup:
            result.add_error("ClickUp client nao configurado")
            return result

        try:
            # Buscar items do Miro
            miro_items = self.miro.list_items(board_id, limit=100)

            for item in miro_items.get('data', []):
                item_id = item.get('id')
                # Buscar element_id correspondente
                for element_id, miro_id in element_mapping.items():
                    if miro_id == item_id:
                        task_id = element_mapping.get(element_id)
                        if task_id:
                            # Atualizar tarefa no ClickUp
                            content = item.get('data', {}).get('content', '')
                            if content:
                                self.clickup.update_task(
                                    task_id,
                                    name=content
                                )

        except Exception as e:
            result.add_error(f"Erro na sincronizacao: {str(e)}")

        return result

    def add_miro_links_to_clickup(
        self,
        metadata: ProcessIntegrationMetadata
    ) -> SyncResult:
        """
        Adiciona links do Miro nas tarefas do ClickUp.

        Args:
            metadata: Metadata de integracao do processo

        Returns:
            SyncResult com status
        """
        logger.info("Adicionando links Miro ao ClickUp")

        result = SyncResult(
            success=True,
            operation='add_miro_links_to_clickup'
        )

        if not self.clickup:
            result.add_error("ClickUp client nao configurado")
            return result

        if not metadata.miro_board_url:
            result.add_error("URL do board Miro nao disponivel")
            return result

        for element_id, task_id in metadata.clickup_task_ids.items():
            try:
                miro_item_id = metadata.miro_element_ids.get(element_id)
                if miro_item_id:
                    item_url = f"{metadata.miro_board_url}?moveToWidget={miro_item_id}"
                    self.clickup.add_comment(
                        task_id,
                        f"📊 [Ver no Miro]({item_url})"
                    )
                    result.clickup_task_ids[element_id] = task_id
            except Exception as e:
                result.add_warning(f"Erro ao adicionar link para {element_id}: {str(e)}")

        return result

    def generate_integration_metadata(
        self,
        process: Process,
        sync_result: SyncResult
    ) -> ProcessIntegrationMetadata:
        """
        Gera metadata de integracao a partir do resultado de sincronizacao.

        Args:
            process: Processo sincronizado
            sync_result: Resultado da sincronizacao

        Returns:
            ProcessIntegrationMetadata preenchido
        """
        return ProcessIntegrationMetadata(
            miro_board_id=sync_result.miro_board_id,
            miro_board_url=sync_result.miro_board_url,
            miro_element_ids=sync_result.miro_item_ids,
            clickup_space_id=sync_result.clickup_space_id,
            clickup_folder_id=sync_result.clickup_folder_id,
            clickup_list_id=sync_result.clickup_list_id,
            clickup_task_ids=sync_result.clickup_task_ids,
            pop_code=sync_result.metadata.get('pop_code'),
            it_codes={},  # Seria preenchido durante geracao
            last_sync=sync_result.timestamp
        )


def sync_process(
    process: Process,
    miro_token: str,
    clickup_token: Optional[str] = None,
    space_id: Optional[str] = None,
    **kwargs
) -> SyncResult:
    """
    Funcao utilitaria para sincronizar um processo.

    Args:
        process: Processo a sincronizar
        miro_token: Token da API Miro
        clickup_token: Token da API ClickUp (opcional)
        space_id: ID do space ClickUp (obrigatorio se clickup_token fornecido)
        **kwargs: Argumentos adicionais

    Returns:
        SyncResult com resultado da sincronizacao
    """
    miro_client = MiroClient(api_token=miro_token)
    clickup_client = ClickUpClient(api_token=clickup_token) if clickup_token else None

    sync = MiroClickUpSync(miro_client, clickup_client)

    return sync.sync_process_to_both(
        process,
        space_id=space_id,
        create_clickup_tasks=clickup_token is not None,
        **kwargs
    )
