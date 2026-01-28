"""
Validador de processos.
Verifica integridade e consistência de processos extraídos.
"""

from typing import List, Set

from src.models.process_model import Process, ProcessElement
from src.utils.exceptions import ValidationError
from src.utils.logger import get_logger

logger = get_logger()


class ProcessValidator:
    """
    Validador de processos.
    Aplica regras de negócio e verifica consistência.
    """

    def __init__(self, strict: bool = False):
        """
        Inicializa o validador.

        Args:
            strict: Se True, erros críticos impedem o uso do processo.
                   Se False, apenas gera warnings.
        """
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, process: Process) -> bool:
        """
        Valida um processo completo.

        Args:
            process: Processo a validar

        Returns:
            True se válido, False caso contrário

        Raises:
            ValidationError: Se strict=True e houver erros
        """
        logger.info(f"Validating process: {process.name}")

        self.errors = []
        self.warnings = []

        # Executar todas as validações
        self._validate_has_start_event(process)
        self._validate_has_end_event(process)
        self._validate_unique_ids(process)
        self._validate_flows_reference_valid_elements(process)
        self._validate_gateways_have_multiple_outputs(process)
        self._validate_elements_are_reachable(process)
        self._validate_no_orphan_elements(process)
        self._validate_actors_exist(process)
        self._validate_annotations_reference_valid_elements(process)

        # Log resultados
        if self.errors:
            logger.error(f"Validation failed with {len(self.errors)} error(s)")
            for error in self.errors:
                logger.error(f"  - {error}")

        if self.warnings:
            logger.warning(f"Validation completed with {len(self.warnings)} warning(s)")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        # Se strict, lançar exceção com erros
        if self.strict and self.errors:
            raise ValidationError(self.errors, process.name)

        return len(self.errors) == 0

    def _validate_has_start_event(self, process: Process):
        """Valida que o processo tem pelo menos um evento de início."""
        start_events = process.get_start_events()
        if not start_events:
            self.errors.append("Process must have at least one start event")
        elif len(start_events) > 1:
            self.warnings.append(f"Process has {len(start_events)} start events (unusual)")

    def _validate_has_end_event(self, process: Process):
        """Valida que o processo tem pelo menos um evento de fim."""
        end_events = process.get_end_events()
        if not end_events:
            self.errors.append("Process must have at least one end event")

    def _validate_unique_ids(self, process: Process):
        """Valida que todos os IDs são únicos."""
        ids = [e.id for e in process.elements]
        duplicates = [id for id in ids if ids.count(id) > 1]
        if duplicates:
            unique_duplicates = list(set(duplicates))
            self.errors.append(f"Duplicate element IDs found: {unique_duplicates}")

    def _validate_flows_reference_valid_elements(self, process: Process):
        """Valida que todos os flows referenciam elementos que existem."""
        element_ids = {e.id for e in process.elements}

        for flow in process.flows:
            if flow.from_element not in element_ids:
                self.errors.append(
                    f"Flow references non-existent element: {flow.from_element}"
                )
            if flow.to_element not in element_ids:
                self.errors.append(
                    f"Flow references non-existent element: {flow.to_element}"
                )

    def _validate_gateways_have_multiple_outputs(self, process: Process):
        """Valida que gateways têm pelo menos 2 saídas."""
        for element in process.get_gateways():
            outgoing = process.get_outgoing_flows(element.id)
            if len(outgoing) < 2:
                self.errors.append(
                    f"Gateway '{element.name}' ({element.id}) must have at least 2 outgoing flows, "
                    f"has {len(outgoing)}"
                )
            # Verificar se flows de gateway têm condições
            for flow in outgoing:
                if not flow.condition:
                    self.warnings.append(
                        f"Gateway flow from '{element.name}' to '{flow.to_element}' "
                        f"should have a condition"
                    )

    def _validate_elements_are_reachable(self, process: Process):
        """Valida que todos os elementos são alcançáveis a partir do início."""
        start_events = process.get_start_events()
        if not start_events:
            # Já validado em outra função
            return

        # BFS para encontrar elementos alcançáveis
        reachable: Set[str] = set()
        to_visit = [e.id for e in start_events]

        while to_visit:
            current_id = to_visit.pop(0)
            if current_id in reachable:
                continue

            reachable.add(current_id)

            # Adicionar próximos elementos
            for flow in process.get_outgoing_flows(current_id):
                if flow.to_element not in reachable:
                    to_visit.append(flow.to_element)

        # Verificar elementos não alcançáveis (exceto anotações)
        all_ids = {e.id for e in process.elements if not e.is_annotation()}
        unreachable = all_ids - reachable

        if unreachable:
            unreachable_names = [
                process.get_element(id).name for id in unreachable
            ]
            self.warnings.append(
                f"Elements not reachable from start: {unreachable_names}"
            )

    def _validate_no_orphan_elements(self, process: Process):
        """Valida que não há elementos órfãos (sem conexões)."""
        for element in process.elements:
            # Skip anotações e eventos
            if element.is_annotation() or element.is_event():
                continue

            incoming = process.get_incoming_flows(element.id)
            outgoing = process.get_outgoing_flows(element.id)

            if not incoming and not outgoing:
                self.warnings.append(
                    f"Orphan element (no connections): '{element.name}' ({element.id})"
                )

    def _validate_actors_exist(self, process: Process):
        """Valida que todos os atores referenciados existem na lista de atores."""
        declared_actors = set(process.actors)
        used_actors = {e.actor for e in process.elements if e.actor}

        # Atores usados mas não declarados
        undeclared = used_actors - declared_actors
        if undeclared:
            self.warnings.append(
                f"Actors used but not declared in actors list: {list(undeclared)}"
            )

        # Atores declarados mas não usados
        unused = declared_actors - used_actors
        if unused:
            self.warnings.append(
                f"Actors declared but not used: {list(unused)}"
            )

    def _validate_annotations_reference_valid_elements(self, process: Process):
        """Valida que anotações referenciam elementos válidos."""
        element_ids = {e.id for e in process.elements}

        for element in process.elements:
            if element.is_annotation():
                attached_to = element.metadata.get('attached_to')
                if attached_to and attached_to not in element_ids:
                    self.warnings.append(
                        f"Annotation '{element.name}' references non-existent element: {attached_to}"
                    )

    def get_errors(self) -> List[str]:
        """Retorna lista de erros encontrados."""
        return self.errors.copy()

    def get_warnings(self) -> List[str]:
        """Retorna lista de warnings encontrados."""
        return self.warnings.copy()

    def get_all_issues(self) -> List[str]:
        """Retorna todos os problemas (erros + warnings)."""
        return self.errors + self.warnings


def validate_process(process: Process, strict: bool = False) -> List[str]:
    """
    Função utilitária para validar um processo.

    Args:
        process: Processo a validar
        strict: Se True, lança exceção em caso de erro

    Returns:
        Lista de erros (vazia se válido)

    Raises:
        ValidationError: Se strict=True e houver erros
    """
    validator = ProcessValidator(strict=strict)
    validator.validate(process)
    return validator.get_errors()


def validate_and_fix_process(process: Process) -> Process:
    """
    Valida e tenta corrigir problemas comuns automaticamente.

    Args:
        process: Processo a validar/corrigir

    Returns:
        Processo corrigido
    """
    logger.info(f"Validating and fixing process: {process.name}")

    # Atualizar lista de atores baseado em elementos
    used_actors = {e.actor for e in process.elements if e.actor}
    if used_actors != set(process.actors):
        logger.info("Updating actors list based on element assignments")
        process.actors = sorted(list(used_actors))

    # Validar
    validator = ProcessValidator(strict=False)
    validator.validate(process)

    # Log problemas que não podem ser corrigidos automaticamente
    if validator.errors:
        logger.warning("Process has validation errors that require manual fix:")
        for error in validator.errors:
            logger.warning(f"  - {error}")

    return process
