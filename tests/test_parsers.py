"""
Testes para os parsers de markdown e extração LLM.
"""

import pytest
from pathlib import Path

from src.parsers.markdown_parser import MarkdownParser, parse_markdown_file
from src.parsers.process_validator import ProcessValidator, validate_process
from src.models.process_model import Process, ProcessElement, ProcessFlow
from src.utils.exceptions import FileNotFoundError, InvalidFileFormatError


class TestMarkdownParser:
    """Testes para MarkdownParser"""

    def test_load_file_success(self, tmp_path):
        """Testa carregamento de arquivo válido"""
        # Criar arquivo temporário
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Process\n\nThis is a test.", encoding='utf-8')

        parser = MarkdownParser()
        content = parser.load_file(str(test_file))

        assert content == "# Test Process\n\nThis is a test."
        assert parser.file_path == str(test_file)

    def test_load_file_not_found(self):
        """Testa erro quando arquivo não existe"""
        parser = MarkdownParser()

        with pytest.raises(FileNotFoundError):
            parser.load_file("nonexistent.md")

    def test_load_file_invalid_format(self, tmp_path):
        """Testa erro quando arquivo não é .md"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test", encoding='utf-8')

        parser = MarkdownParser()

        with pytest.raises(InvalidFileFormatError):
            parser.load_file(str(test_file))

    def test_extract_title(self):
        """Testa extração de título"""
        parser = MarkdownParser()
        parser.content = "# My Process\n\nDescription here"

        title = parser.extract_title()
        assert title == "My Process"

    def test_extract_title_no_h1(self):
        """Testa quando não há título H1"""
        parser = MarkdownParser()
        parser.content = "## Section\n\nNo H1 here"

        title = parser.extract_title()
        assert title is None

    def test_extract_sections(self):
        """Testa extração de seções"""
        parser = MarkdownParser()
        parser.content = """
# Title

## Section 1
Content 1

## Section 2
Content 2
"""

        sections = parser.extract_sections()
        assert "Section 1" in sections
        assert "Section 2" in sections
        assert sections["Section 1"] == "Content 1"
        assert sections["Section 2"] == "Content 2"

    def test_extract_lists(self):
        """Testa extração de listas"""
        parser = MarkdownParser()
        parser.content = """
- Item 1
- Item 2
* Item 3

1. Numbered 1
2. Numbered 2
"""

        items = parser.extract_lists()
        assert "Item 1" in items
        assert "Item 2" in items
        assert "Item 3" in items
        assert "Numbered 1" in items
        assert "Numbered 2" in items

    def test_identify_keywords(self):
        """Testa identificação de palavras-chave"""
        parser = MarkdownParser()
        parser.content = """
Responsável: João
(Gerente de Projetos)

Decisão: Aprovar ou rejeitar
Se aprovado: continuar
Se rejeitado: parar

Início: Receber solicitação
Fim: Projeto concluído
"""

        keywords = parser.identify_keywords()

        assert len(keywords['responsaveis']) > 0
        assert len(keywords['decisoes']) > 0
        assert len(keywords['eventos']) > 0

    def test_preprocess_for_llm(self):
        """Testa pré-processamento para LLM"""
        parser = MarkdownParser()
        parser.content = """
# Title

Content with    multiple   spaces


And multiple blank lines
"""

        processed = parser.preprocess_for_llm()

        # Deve remover espaços extras e linhas vazias excessivas
        assert "    " not in processed
        assert "\n\n\n" not in processed
        assert processed.startswith("#")


class TestProcessValidator:
    """Testes para ProcessValidator"""

    def test_valid_simple_process(self):
        """Testa validação de processo válido simples"""
        process = Process(
            name="Test Process",
            description="A simple test process",
            actors=["Actor1"],
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
                    name="Do Something",
                    actor="Actor1"
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
                ProcessFlow(from_element="task1", to_element="end")
            ]
        )

        validator = ProcessValidator(strict=False)
        is_valid = validator.validate(process)

        assert is_valid
        assert len(validator.get_errors()) == 0

    def test_missing_start_event(self):
        """Testa erro quando falta evento de início"""
        process = Process(
            name="Test",
            elements=[
                ProcessElement(
                    id="task1",
                    type="task",
                    name="Task",
                    actor="Actor1"
                ),
                ProcessElement(
                    id="end",
                    type="event",
                    name="End",
                    metadata={"event_type": "end"}
                )
            ],
            flows=[]
        )

        validator = ProcessValidator(strict=False)
        validator.validate(process)

        assert len(validator.get_errors()) > 0
        assert any("start event" in error.lower() for error in validator.get_errors())

    def test_missing_end_event(self):
        """Testa erro quando falta evento de fim"""
        process = Process(
            name="Test",
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
                    name="Task",
                    actor="Actor1"
                )
            ],
            flows=[]
        )

        validator = ProcessValidator(strict=False)
        validator.validate(process)

        assert len(validator.get_errors()) > 0
        assert any("end event" in error.lower() for error in validator.get_errors())

    def test_duplicate_ids(self):
        """Testa erro quando há IDs duplicados"""
        process = Process(
            name="Test",
            elements=[
                ProcessElement(
                    id="task1",
                    type="task",
                    name="Task 1",
                    actor="Actor1"
                ),
                ProcessElement(
                    id="task1",  # Duplicado
                    type="task",
                    name="Task 2",
                    actor="Actor1"
                )
            ],
            flows=[]
        )

        validator = ProcessValidator(strict=False)
        validator.validate(process)

        assert len(validator.get_errors()) > 0
        assert any("duplicate" in error.lower() for error in validator.get_errors())

    def test_invalid_flow_reference(self):
        """Testa erro quando flow referencia elemento inexistente"""
        process = Process(
            name="Test",
            elements=[
                ProcessElement(
                    id="task1",
                    type="task",
                    name="Task",
                    actor="Actor1"
                )
            ],
            flows=[
                ProcessFlow(from_element="task1", to_element="nonexistent")
            ]
        )

        validator = ProcessValidator(strict=False)
        validator.validate(process)

        assert len(validator.get_errors()) > 0
        assert any("non-existent" in error.lower() for error in validator.get_errors())

    def test_gateway_with_insufficient_outputs(self):
        """Testa erro quando gateway tem menos de 2 saídas"""
        process = Process(
            name="Test",
            elements=[
                ProcessElement(
                    id="gateway1",
                    type="gateway",
                    name="Decision",
                    actor="Actor1",
                    metadata={"gateway_type": "exclusive"}
                ),
                ProcessElement(
                    id="task1",
                    type="task",
                    name="Task",
                    actor="Actor1"
                )
            ],
            flows=[
                ProcessFlow(from_element="gateway1", to_element="task1")
            ]
        )

        validator = ProcessValidator(strict=False)
        validator.validate(process)

        assert len(validator.get_errors()) > 0
        assert any("gateway" in error.lower() and "2" in error for error in validator.get_errors())

    def test_utility_function_validate_process(self):
        """Testa função utilitária validate_process"""
        process = Process(
            name="Test",
            elements=[
                ProcessElement(
                    id="start",
                    type="event",
                    name="Start",
                    metadata={"event_type": "start"}
                ),
                ProcessElement(
                    id="end",
                    type="event",
                    name="End",
                    metadata={"event_type": "end"}
                )
            ],
            flows=[
                ProcessFlow(from_element="start", to_element="end")
            ]
        )

        errors = validate_process(process, strict=False)
        assert len(errors) == 0


class TestProcessModel:
    """Testes para modelos de Process"""

    def test_process_element_validation(self):
        """Testa validação de ProcessElement"""
        # ID vazio deve falhar
        with pytest.raises(ValueError):
            ProcessElement(
                id="",
                type="task",
                name="Test"
            )

        # Nome vazio deve falhar
        with pytest.raises(ValueError):
            ProcessElement(
                id="test",
                type="task",
                name=""
            )

    def test_process_get_element(self):
        """Testa busca de elemento por ID"""
        process = Process(
            name="Test",
            elements=[
                ProcessElement(id="task1", type="task", name="Task 1"),
                ProcessElement(id="task2", type="task", name="Task 2")
            ]
        )

        element = process.get_element("task1")
        assert element is not None
        assert element.name == "Task 1"

        # Elemento inexistente
        element = process.get_element("nonexistent")
        assert element is None

    def test_process_get_flows(self):
        """Testa busca de flows"""
        process = Process(
            name="Test",
            elements=[
                ProcessElement(id="task1", type="task", name="Task 1"),
                ProcessElement(id="task2", type="task", name="Task 2"),
                ProcessElement(id="task3", type="task", name="Task 3")
            ],
            flows=[
                ProcessFlow(from_element="task1", to_element="task2"),
                ProcessFlow(from_element="task2", to_element="task3"),
                ProcessFlow(from_element="task1", to_element="task3")
            ]
        )

        # Outgoing flows
        outgoing = process.get_outgoing_flows("task1")
        assert len(outgoing) == 2

        # Incoming flows
        incoming = process.get_incoming_flows("task3")
        assert len(incoming) == 2


# Fixtures
@pytest.fixture
def sample_markdown_file(tmp_path):
    """Cria um arquivo markdown de exemplo"""
    content = """
# Sample Process

## Description
This is a sample process for testing.

## Steps

1. **Start** (Actor1)
   - Begin the process

2. **Process Data** (Actor2)
   - Process the information

3. **Decision: Approve?** (Actor1)
   - If yes: continue
   - If no: reject

4. **End**
   - Process complete
"""
    file_path = tmp_path / "sample.md"
    file_path.write_text(content, encoding='utf-8')
    return str(file_path)


def test_parse_markdown_file_integration(sample_markdown_file):
    """Teste de integração do parsing completo"""
    content, metadata = parse_markdown_file(sample_markdown_file)

    assert content is not None
    assert len(content) > 0
    assert metadata['title'] == "Sample Process"
    assert 'sections' in metadata
    assert 'statistics' in metadata
