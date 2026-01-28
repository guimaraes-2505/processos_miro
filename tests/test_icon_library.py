"""
Testes para o sistema de ícones BPMN.
"""

import pytest
from pathlib import Path
from src.models.icon_model import IconLibrary, IconLibraryConfig, TypeMapping
from src.utils.icon_library import IconResolver, IconLoadError


class TestIconLibrary:
    """Testes para IconLibrary."""

    def test_icon_library_creation(self):
        """Testa criação de IconLibrary."""
        config = IconLibraryConfig(base_path="data/icons", mode="svg")
        library = IconLibrary(
            tasks={"user_task": "tasks/user-task.svg"},
            events={"start_event": "events/start-event.svg"},
            gateways={"exclusive_gateway": "gateways/exclusive-gateway.svg"},
            config=config,
        )

        assert library.config.mode == "svg"
        assert library.tasks["user_task"] == "tasks/user-task.svg"

    def test_get_icon_path(self):
        """Testa resolução de caminho de ícone."""
        library = IconLibrary(
            tasks={"user_task": "tasks/user-task.svg"},
            config=IconLibraryConfig(base_path="data/icons"),
        )

        path = library.get_icon_path("task", "user_task")
        assert path == Path("data/icons/tasks/user-task.svg")

    def test_get_icon_path_fallback(self):
        """Testa fallback para tipo genérico."""
        library = IconLibrary(
            tasks={"task": "tasks/generic-task.svg"},
            config=IconLibraryConfig(base_path="data/icons"),
        )

        # Tipo específico não existe, deve usar fallback genérico
        path = library.get_icon_path("task", "unknown_task")
        assert path == Path("data/icons/tasks/generic-task.svg")

    def test_get_icon_size(self):
        """Testa obtenção de tamanho de ícone."""
        library = IconLibrary(
            config=IconLibraryConfig(
                icon_sizes={"task": 20, "event": 16, "gateway": 18}
            )
        )

        assert library.get_icon_size("task") == 20
        assert library.get_icon_size("event") == 16
        assert library.get_icon_size("unknown") == 24  # default

    def test_has_icon(self, tmp_path):
        """Testa verificação de existência de ícone."""
        # Criar arquivo temporário
        icon_file = tmp_path / "tasks" / "user-task.svg"
        icon_file.parent.mkdir(parents=True)
        icon_file.write_text('<svg></svg>')

        library = IconLibrary(
            tasks={"user_task": "tasks/user-task.svg"},
            config=IconLibraryConfig(base_path=str(tmp_path)),
        )

        assert library.has_icon("task", "user_task") is True
        assert library.has_icon("task", "nonexistent") is False


class TestTypeMapping:
    """Testes para TypeMapping."""

    def test_resolve_task_type(self):
        """Testa resolução de tipo de tarefa."""
        mapping = TypeMapping()

        result = mapping.resolve_bpmn_type("task", {"task_type": "user"})
        assert result == "user_task"

        result = mapping.resolve_bpmn_type("task", {"task_type": "service"})
        assert result == "service_task"

        # Default
        result = mapping.resolve_bpmn_type("task", {})
        assert result == "user_task"

    def test_resolve_event_type(self):
        """Testa resolução de tipo de evento."""
        mapping = TypeMapping()

        result = mapping.resolve_bpmn_type("event", {"event_type": "start"})
        assert result == "start_event"

        result = mapping.resolve_bpmn_type("event", {"event_type": "timer"})
        assert result == "timer_event"

    def test_resolve_gateway_type(self):
        """Testa resolução de tipo de gateway."""
        mapping = TypeMapping()

        result = mapping.resolve_bpmn_type("gateway", {"gateway_type": "exclusive"})
        assert result == "exclusive_gateway"

        result = mapping.resolve_bpmn_type("gateway", {"gateway_type": "parallel"})
        assert result == "parallel_gateway"


class TestIconResolver:
    """Testes para IconResolver."""

    def test_resolver_with_missing_yaml(self, tmp_path):
        """Testa resolver com arquivo YAML ausente."""
        yaml_path = tmp_path / "icons.yaml"

        # Deve criar biblioteca vazia sem erro
        resolver = IconResolver(yaml_path)
        assert resolver.library is not None
        stats = resolver.get_stats()
        assert stats["loaded"] is True

    def test_resolver_with_valid_yaml(self, tmp_path):
        """Testa resolver com arquivo YAML válido."""
        # Criar arquivo YAML
        yaml_content = """
tasks:
  user_task: "tasks/user-task.svg"
  service_task: "tasks/service-task.svg"

events:
  start_event: "events/start-event.svg"

gateways:
  exclusive_gateway: "gateways/exclusive-gateway.svg"

config:
  base_path: "data/icons"
  mode: "svg"
  icon_size: 24
"""
        yaml_path = tmp_path / "icons.yaml"
        yaml_path.write_text(yaml_content)

        resolver = IconResolver(yaml_path)

        stats = resolver.get_stats()
        assert stats["total_tasks"] == 2
        assert stats["total_events"] == 1
        assert stats["total_gateways"] == 1
        assert stats["mode"] == "svg"

    def test_get_icon_svg(self, tmp_path):
        """Testa leitura de arquivo SVG."""
        # Criar estrutura
        yaml_content = """
tasks:
  user_task: "tasks/user-task.svg"

config:
  base_path: "{base_path}"
  mode: "svg"
""".format(
            base_path=str(tmp_path)
        )

        yaml_path = tmp_path / "icons.yaml"
        yaml_path.write_text(yaml_content)

        # Criar arquivo SVG
        svg_file = tmp_path / "tasks" / "user-task.svg"
        svg_file.parent.mkdir(parents=True)
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><circle r="10"/></svg>'
        svg_file.write_text(svg_content)

        # Testar
        resolver = IconResolver(yaml_path)
        svg = resolver.get_icon_svg("task", "user_task")

        assert svg == svg_content
        assert '<circle r="10"/>' in svg

    def test_svg_caching(self, tmp_path):
        """Testa cache de SVGs."""
        yaml_content = f"""
tasks:
  user_task: "tasks/user-task.svg"
config:
  base_path: "{tmp_path}"
"""
        yaml_path = tmp_path / "icons.yaml"
        yaml_path.write_text(yaml_content)

        svg_file = tmp_path / "tasks" / "user-task.svg"
        svg_file.parent.mkdir(parents=True)
        svg_file.write_text('<svg></svg>')

        resolver = IconResolver(yaml_path)

        # Primeira chamada
        svg1 = resolver.get_icon_svg("task", "user_task")

        # Segunda chamada (deve usar cache)
        svg2 = resolver.get_icon_svg("task", "user_task")

        assert svg1 == svg2
        stats = resolver.get_stats()
        assert stats["cache_size"] == 1

    def test_clear_cache(self, tmp_path):
        """Testa limpeza de cache."""
        yaml_content = f"""
tasks:
  user_task: "tasks/user-task.svg"
config:
  base_path: "{tmp_path}"
"""
        yaml_path = tmp_path / "icons.yaml"
        yaml_path.write_text(yaml_content)

        svg_file = tmp_path / "tasks" / "user-task.svg"
        svg_file.parent.mkdir(parents=True)
        svg_file.write_text('<svg></svg>')

        resolver = IconResolver(yaml_path)
        resolver.get_icon_svg("task", "user_task")

        assert resolver.get_stats()["cache_size"] == 1

        resolver.clear_cache()
        assert resolver.get_stats()["cache_size"] == 0

    def test_resolve_bpmn_type(self):
        """Testa resolução de tipo BPMN."""
        resolver = IconResolver(Path("data/icons/icons.yaml"))

        result = resolver.resolve_bpmn_type("task", {"task_type": "user"})
        assert result == "user_task"

        result = resolver.resolve_bpmn_type("event", {"event_type": "start"})
        assert result == "start_event"


class TestIconValidation:
    """Testes para validação de ícones."""

    def test_valid_svg(self, tmp_path):
        """Testa validação de SVG válido."""
        from src.utils.validate_icons import validate_svg_file

        svg_file = tmp_path / "test.svg"
        svg_file.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle r="10"/></svg>'
        )

        result = validate_svg_file(svg_file)
        assert result.is_valid is True

    def test_invalid_svg(self, tmp_path):
        """Testa validação de SVG inválido."""
        from src.utils.validate_icons import validate_svg_file

        svg_file = tmp_path / "test.svg"
        svg_file.write_text('<not-xml>')

        result = validate_svg_file(svg_file)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_missing_file(self, tmp_path):
        """Testa validação de arquivo inexistente."""
        from src.utils.validate_icons import validate_svg_file

        svg_file = tmp_path / "nonexistent.svg"

        result = validate_svg_file(svg_file)
        assert result.is_valid is False
        assert "não encontrado" in result.errors[0].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
