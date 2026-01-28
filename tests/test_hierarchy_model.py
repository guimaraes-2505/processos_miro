"""
Testes para os modelos de hierarquia organizacional.
"""

import pytest
from datetime import datetime

from src.models.hierarchy_model import (
    ValueChain, Macroprocess, SIPOC, SIPOCItem,
    ProcessHierarchy, Activity, Task, OrganizationHierarchy
)


class TestSIPOCItem:
    """Testes para SIPOCItem."""

    def test_create_basic(self):
        """Testa criacao basica de item SIPOC."""
        item = SIPOCItem(
            name="Cliente Externo",
            description="Cliente final do produto",
            type="externo"
        )
        assert item.name == "Cliente Externo"
        assert item.type == "externo"

    def test_create_minimal(self):
        """Testa criacao com campos minimos."""
        item = SIPOCItem(name="Item Simples")
        assert item.name == "Item Simples"
        assert item.description is None
        assert item.type is None


class TestSIPOC:
    """Testes para modelo SIPOC."""

    def test_create_sipoc(self):
        """Testa criacao de SIPOC completo."""
        sipoc = SIPOC(
            suppliers=[
                SIPOCItem(name="Fornecedor A", type="externo"),
                SIPOCItem(name="Departamento X", type="interno")
            ],
            inputs=[
                SIPOCItem(name="Materia Prima"),
                SIPOCItem(name="Informacoes")
            ],
            process_steps=[
                "1. Receber materiais",
                "2. Processar",
                "3. Entregar"
            ],
            outputs=[
                SIPOCItem(name="Produto Final"),
                SIPOCItem(name="Relatorio")
            ],
            customers=[
                SIPOCItem(name="Cliente Final", type="externo")
            ]
        )

        assert len(sipoc.suppliers) == 2
        assert len(sipoc.inputs) == 2
        assert len(sipoc.process_steps) == 3
        assert len(sipoc.outputs) == 2
        assert len(sipoc.customers) == 1

    def test_sipoc_empty(self):
        """Testa SIPOC vazio."""
        sipoc = SIPOC()
        assert len(sipoc.suppliers) == 0
        assert len(sipoc.inputs) == 0


class TestMacroprocess:
    """Testes para modelo Macroprocess."""

    def test_create_macroprocess_primario(self):
        """Testa criacao de macroprocesso primario."""
        macro = Macroprocess(
            id="macro_vendas",
            name="Gestao de Vendas",
            type="primario",
            description="Gerencia todo o ciclo de vendas"
        )

        assert macro.id == "macro_vendas"
        assert macro.name == "Gestao de Vendas"
        assert macro.type == "primario"
        assert macro.processes == []

    def test_create_macroprocess_apoio(self):
        """Testa criacao de macroprocesso de apoio."""
        macro = Macroprocess(
            id="macro_rh",
            name="Gestao de Pessoas",
            type="apoio",
            owner="Diretor de RH"
        )

        assert macro.type == "apoio"
        assert macro.owner == "Diretor de RH"

    def test_create_macroprocess_gestao(self):
        """Testa criacao de macroprocesso de gestao."""
        macro = Macroprocess(
            id="macro_qualidade",
            name="Gestao da Qualidade",
            type="gestao"
        )

        assert macro.type == "gestao"

    def test_macroprocess_with_sipoc(self):
        """Testa macroprocesso com SIPOC."""
        sipoc = SIPOC(
            process_steps=["Etapa 1", "Etapa 2"]
        )

        macro = Macroprocess(
            id="macro_test",
            name="Teste",
            type="primario",
            sipoc=sipoc
        )

        assert macro.sipoc is not None
        assert len(macro.sipoc.process_steps) == 2

    def test_macroprocess_with_processes(self):
        """Testa macroprocesso com lista de processos."""
        macro = Macroprocess(
            id="macro_test",
            name="Marketing",
            type="primario",
            processes=["proc_001", "proc_002", "proc_003"]
        )

        assert len(macro.processes) == 3
        assert "proc_002" in macro.processes


class TestValueChain:
    """Testes para modelo ValueChain."""

    def test_create_value_chain(self):
        """Testa criacao de Cadeia de Valor."""
        vc = ValueChain(
            name="Empresa ABC",
            description="Cadeia de valor da Empresa ABC",
            organization="Empresa ABC Ltda",
            mission="Entregar valor ao cliente",
            vision="Ser lider de mercado"
        )

        assert vc.name == "Empresa ABC"
        assert vc.organization == "Empresa ABC Ltda"
        assert vc.primary_macroprocesses == []

    def test_value_chain_with_macroprocesses(self):
        """Testa Cadeia de Valor com macroprocessos."""
        vc = ValueChain(
            name="Empresa XYZ",
            primary_macroprocesses=["marketing", "vendas", "producao"],
            support_macroprocesses=["rh", "ti", "financeiro"],
            management_macroprocesses=["qualidade", "estrategia"]
        )

        assert len(vc.primary_macroprocesses) == 3
        assert len(vc.support_macroprocesses) == 3
        assert len(vc.management_macroprocesses) == 2
        assert "vendas" in vc.primary_macroprocesses
        assert "rh" in vc.support_macroprocesses


class TestProcessHierarchy:
    """Testes para modelo ProcessHierarchy."""

    def test_create_hierarchy(self):
        """Testa criacao de hierarquia de processo."""
        hierarchy = ProcessHierarchy(
            process_id="proc_001",
            name="Processo de Vendas",
            level=3,
            parent_id="macro_vendas"
        )

        assert hierarchy.process_id == "proc_001"
        assert hierarchy.level == 3
        assert hierarchy.subprocesses == []

    def test_hierarchy_with_subprocesses(self):
        """Testa hierarquia com subprocessos."""
        hierarchy = ProcessHierarchy(
            process_id="proc_main",
            name="Processo Principal",
            level=3,
            subprocesses=["sub_001", "sub_002"]
        )

        assert len(hierarchy.subprocesses) == 2


class TestActivity:
    """Testes para modelo Activity."""

    def test_create_activity(self):
        """Testa criacao de atividade."""
        activity = Activity(
            id="act_001",
            name="Analisar Pedido",
            numbering="1.1",
            actor="Analista",
            description="Analisa o pedido recebido"
        )

        assert activity.id == "act_001"
        assert activity.numbering == "1.1"
        assert activity.tasks == []

    def test_activity_with_io(self):
        """Testa atividade com inputs e outputs."""
        activity = Activity(
            id="act_002",
            name="Processar Dados",
            numbering="2.1",
            inputs=["Dados brutos", "Configuracoes"],
            outputs=["Relatorio", "Log"]
        )

        assert len(activity.inputs) == 2
        assert len(activity.outputs) == 2
        assert "Relatorio" in activity.outputs


class TestTask:
    """Testes para modelo Task."""

    def test_create_task(self):
        """Testa criacao de tarefa."""
        task = Task(
            id="task_001",
            name="Verificar Email",
            numbering="1.1.1",
            description="Verificar caixa de entrada"
        )

        assert task.id == "task_001"
        assert task.numbering == "1.1.1"

    def test_task_with_checklist(self):
        """Testa tarefa com checklist."""
        task = Task(
            id="task_002",
            name="Conferir Documentos",
            checklist_items=[
                "RG verificado",
                "CPF verificado",
                "Comprovante de endereco"
            ]
        )

        assert len(task.checklist_items) == 3


class TestOrganizationHierarchy:
    """Testes para modelo OrganizationHierarchy."""

    def test_create_complete_hierarchy(self):
        """Testa criacao de hierarquia organizacional completa."""
        # Criar estrutura
        vc = ValueChain(
            name="Minha Empresa",
            primary_macroprocesses=["macro_vendas"],
            support_macroprocesses=["macro_rh"]
        )

        macros = {
            "macro_vendas": Macroprocess(
                id="macro_vendas",
                name="Vendas",
                type="primario",
                processes=["proc_001"]
            ),
            "macro_rh": Macroprocess(
                id="macro_rh",
                name="RH",
                type="apoio"
            )
        }

        # Criar hierarquia
        org = OrganizationHierarchy(
            name="Minha Empresa",
            value_chain=vc,
            macroprocesses=macros
        )

        assert org.name == "Minha Empresa"
        assert org.value_chain is not None
        assert len(org.macroprocesses) == 2
        assert "macro_vendas" in org.macroprocesses

    def test_get_macroprocess_by_type(self):
        """Testa filtragem de macroprocessos por tipo."""
        org = OrganizationHierarchy(
            name="Test Org",
            macroprocesses={
                "m1": Macroprocess(id="m1", name="M1", type="primario"),
                "m2": Macroprocess(id="m2", name="M2", type="primario"),
                "m3": Macroprocess(id="m3", name="M3", type="apoio"),
                "m4": Macroprocess(id="m4", name="M4", type="gestao")
            }
        )

        primarios = [m for m in org.macroprocesses.values() if m.type == "primario"]
        apoio = [m for m in org.macroprocesses.values() if m.type == "apoio"]
        gestao = [m for m in org.macroprocesses.values() if m.type == "gestao"]

        assert len(primarios) == 2
        assert len(apoio) == 1
        assert len(gestao) == 1


class TestIntegration:
    """Testes de integracao entre modelos."""

    def test_full_hierarchy_structure(self):
        """Testa estrutura hierarquica completa."""
        # Nivel 1: Cadeia de Valor
        value_chain = ValueChain(
            name="Empresa Demo",
            organization="Demo Ltda",
            mission="Demonstrar o sistema",
            primary_macroprocesses=["macro_vendas"],
            support_macroprocesses=["macro_ti"]
        )

        # Nivel 2: Macroprocessos com SIPOC
        sipoc_vendas = SIPOC(
            suppliers=[SIPOCItem(name="Marketing")],
            inputs=[SIPOCItem(name="Lead qualificado")],
            process_steps=["Prospectar", "Negociar", "Fechar"],
            outputs=[SIPOCItem(name="Contrato assinado")],
            customers=[SIPOCItem(name="Cliente")]
        )

        macro_vendas = Macroprocess(
            id="macro_vendas",
            name="Gestao de Vendas",
            type="primario",
            owner="Diretor Comercial",
            sipoc=sipoc_vendas,
            processes=["proc_prospeccao", "proc_negociacao"]
        )

        macro_ti = Macroprocess(
            id="macro_ti",
            name="Tecnologia da Informacao",
            type="apoio"
        )

        # Nivel 3: Processos
        proc_prospeccao = ProcessHierarchy(
            process_id="proc_prospeccao",
            name="Prospeccao de Clientes",
            level=3,
            parent_id="macro_vendas"
        )

        # Nivel 4: Atividades
        act_identificar = Activity(
            id="act_identificar",
            name="Identificar Potenciais Clientes",
            numbering="1.1",
            actor="Vendedor",
            inputs=["Lista de mercado"],
            outputs=["Lista de prospects"]
        )

        # Nivel 5: Tarefas
        task_pesquisar = Task(
            id="task_pesquisar",
            name="Pesquisar empresas no segmento",
            numbering="1.1.1",
            checklist_items=[
                "Acessar base de dados",
                "Filtrar por segmento",
                "Exportar lista"
            ]
        )

        # Montar hierarquia completa
        org = OrganizationHierarchy(
            name="Empresa Demo",
            value_chain=value_chain,
            macroprocesses={
                "macro_vendas": macro_vendas,
                "macro_ti": macro_ti
            },
            processes={
                "proc_prospeccao": proc_prospeccao
            },
            activities={
                "act_identificar": act_identificar
            },
            tasks={
                "task_pesquisar": task_pesquisar
            }
        )

        # Validacoes
        assert org.value_chain.name == "Empresa Demo"
        assert len(org.macroprocesses) == 2
        assert org.macroprocesses["macro_vendas"].sipoc is not None
        assert len(org.macroprocesses["macro_vendas"].sipoc.process_steps) == 3
        assert len(org.processes) == 1
        assert len(org.activities) == 1
        assert len(org.tasks) == 1
        assert len(org.tasks["task_pesquisar"].checklist_items) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
