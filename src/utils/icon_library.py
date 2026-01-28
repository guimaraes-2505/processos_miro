"""
Biblioteca de resolução e carregamento de ícones BPMN.

Este módulo fornece a classe IconResolver que carrega a configuração
de ícones do arquivo YAML e resolve caminhos de ícones SVG baseado
em tipos BPMN.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any
import yaml

from src.models.icon_model import IconLibrary, IconLibraryConfig, TypeMapping
from src.utils.logger import get_logger
from src.utils.exceptions import ProcessMapperError

logger = get_logger()


class IconLoadError(ProcessMapperError):
    """Exceção levantada quando há erro no carregamento de ícones."""

    pass


class IconResolver:
    """
    Carrega e resolve ícones da biblioteca YAML.

    Esta classe é responsável por:
    - Carregar o arquivo icons.yaml
    - Resolver caminhos de ícones baseado em tipos BPMN
    - Ler conteúdo de arquivos SVG
    - Gerenciar cache de ícones

    Attributes:
        library: Instância de IconLibrary com os mapeamentos
        base_path: Caminho base para os arquivos de ícones
        type_mapping: Mapeamento de metadata para tipos BPMN
        _svg_cache: Cache de conteúdo SVG

    Examples:
        >>> resolver = IconResolver("data/icons/icons.yaml")
        >>> svg_content = resolver.get_icon_svg("user_task")
        >>> print(svg_content)
        '<svg xmlns="http://www.w3.org/2000/svg">...</svg>'
    """

    def __init__(self, icons_yaml_path: Union[Path, str]):
        """
        Inicializa o resolver com o arquivo YAML de ícones.

        Args:
            icons_yaml_path: Caminho para o arquivo icons.yaml

        Raises:
            IconLoadError: Se o arquivo não puder ser carregado
        """
        self.yaml_path = Path(icons_yaml_path)
        self.library: Optional[IconLibrary] = None
        self.base_path: Optional[Path] = None
        self.type_mapping = TypeMapping()
        self._svg_cache: Dict[str, str] = {}

        self._load_library()

    def _load_library(self) -> None:
        """
        Carrega a biblioteca de ícones do arquivo YAML.

        Raises:
            IconLoadError: Se o arquivo não existir ou for inválido
        """
        if not self.yaml_path.exists():
            logger.warning(
                f"Arquivo de ícones não encontrado: {self.yaml_path}. "
                f"Sistema usará fallback."
            )
            # Criar biblioteca vazia com configuração padrão
            self.library = IconLibrary()
            self.base_path = Path("data/icons")
            return

        try:
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                raise IconLoadError("Arquivo YAML vazio")

            # Extrair seções
            tasks = data.get("tasks", {})
            events = data.get("events", {})
            gateways = data.get("gateways", {})
            config_data = data.get("config", {})

            # Criar configuração
            config = IconLibraryConfig(**config_data)

            # Criar biblioteca
            self.library = IconLibrary(
                tasks=tasks, events=events, gateways=gateways, config=config
            )

            self.base_path = Path(config.base_path)

            logger.info(
                f"Biblioteca de ícones carregada: "
                f"{len(tasks)} tasks, {len(events)} events, {len(gateways)} gateways"
            )

        except yaml.YAMLError as e:
            raise IconLoadError(f"Erro ao parsear YAML: {e}")
        except Exception as e:
            raise IconLoadError(f"Erro ao carregar biblioteca de ícones: {e}")

    def get_icon_path(
        self, element_type: str, bpmn_type: Optional[str] = None
    ) -> Optional[Path]:
        """
        Resolve o caminho completo do arquivo de ícone.

        Args:
            element_type: Tipo do elemento ('task', 'event', 'gateway')
            bpmn_type: Tipo BPMN específico (ex: 'user_task')
                      Se None, usa element_type como fallback

        Returns:
            Path absoluto do arquivo SVG ou None se não encontrado

        Examples:
            >>> resolver.get_icon_path('task', 'user_task')
            Path('/path/to/data/icons/tasks/user-task.svg')
        """
        if not self.library:
            return None

        if not bpmn_type:
            bpmn_type = element_type

        return self.library.get_icon_path(element_type, bpmn_type)

    def get_icon_svg(
        self, element_type: str, bpmn_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Retorna o conteúdo SVG do ícone.

        Args:
            element_type: Tipo do elemento ('task', 'event', 'gateway')
            bpmn_type: Tipo BPMN específico

        Returns:
            String com conteúdo SVG ou None se não encontrado

        Examples:
            >>> svg = resolver.get_icon_svg('task', 'user_task')
            >>> print(svg[:50])
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox='
        """
        if not bpmn_type:
            bpmn_type = element_type

        # Verificar cache
        cache_key = f"{element_type}:{bpmn_type}"
        if cache_key in self._svg_cache:
            return self._svg_cache[cache_key]

        # Resolver caminho
        icon_path = self.get_icon_path(element_type, bpmn_type)
        if not icon_path or not icon_path.exists():
            logger.debug(
                f"Ícone não encontrado para {element_type}:{bpmn_type} "
                f"(path: {icon_path})"
            )
            return None

        try:
            # Ler arquivo SVG
            svg_content = icon_path.read_text(encoding="utf-8")

            # Adicionar ao cache
            self._svg_cache[cache_key] = svg_content

            logger.debug(f"Ícone carregado: {icon_path} ({len(svg_content)} bytes)")
            return svg_content

        except Exception as e:
            logger.error(f"Erro ao ler arquivo SVG {icon_path}: {e}")
            return None

    def resolve_bpmn_type(
        self, element_type: str, metadata: Dict[str, Any]
    ) -> str:
        """
        Resolve o tipo BPMN completo baseado no elemento e metadata.

        Args:
            element_type: Tipo base ('task', 'event', 'gateway')
            metadata: Dicionário de metadata do ProcessElement

        Returns:
            Tipo BPMN completo (ex: 'user_task', 'start_event')

        Examples:
            >>> resolver.resolve_bpmn_type('task', {'task_type': 'service'})
            'service_task'
        """
        resolved = self.type_mapping.resolve_bpmn_type(element_type, metadata)
        return resolved if resolved else element_type

    def has_icon(self, element_type: str, bpmn_type: str) -> bool:
        """
        Verifica se um ícone existe para o tipo especificado.

        Args:
            element_type: Tipo do elemento
            bpmn_type: Tipo BPMN específico

        Returns:
            True se o ícone existe e é acessível
        """
        if not self.library:
            return False

        icon_path = self.get_icon_path(element_type, bpmn_type)
        return icon_path is not None and icon_path.exists()

    def get_icon_size(self, element_type: str) -> int:
        """
        Retorna o tamanho apropriado para o ícone.

        Args:
            element_type: Tipo do elemento

        Returns:
            Tamanho em pixels
        """
        if not self.library:
            return 24  # Tamanho padrão

        return self.library.get_icon_size(element_type)

    def get_icon_position(self, element_type: str) -> str:
        """
        Retorna a posição apropriada para o ícone.

        Args:
            element_type: Tipo do elemento

        Returns:
            Posição ('left', 'inside', 'center')
        """
        if not self.library:
            return "left"

        return self.library.get_icon_position(element_type)

    def get_mode(self) -> str:
        """
        Retorna o modo de renderização configurado.

        Returns:
            Modo ('svg', 'emoji', 'hybrid')
        """
        if not self.library:
            return "emoji"  # Fallback para modo legado

        return self.library.config.mode

    def clear_cache(self) -> None:
        """Limpa o cache de SVGs."""
        self._svg_cache.clear()
        logger.debug("Cache de ícones limpo")

    def reload(self) -> None:
        """
        Recarrega a biblioteca do arquivo YAML.

        Útil para desenvolvimento ou quando o arquivo é modificado.
        """
        self.clear_cache()
        self._load_library()
        logger.info("Biblioteca de ícones recarregada")

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas sobre a biblioteca.

        Returns:
            Dicionário com estatísticas
        """
        if not self.library:
            return {"loaded": False}

        return {
            "loaded": True,
            "yaml_path": str(self.yaml_path),
            "base_path": str(self.base_path),
            "mode": self.library.config.mode,
            "total_tasks": len(self.library.tasks),
            "total_events": len(self.library.events),
            "total_gateways": len(self.library.gateways),
            "cache_size": len(self._svg_cache),
            "fallback_strategy": self.library.config.fallback_strategy,
        }


# Singleton global para uso em todo o sistema
_icon_resolver_instance: Optional[IconResolver] = None


def get_icon_resolver(
    icons_yaml_path: Optional[Union[Path, str]] = None, reload: bool = False
) -> IconResolver:
    """
    Retorna instância singleton do IconResolver.

    Args:
        icons_yaml_path: Caminho para icons.yaml (usa padrão se None)
        reload: Se True, força recarregamento da biblioteca

    Returns:
        Instância global de IconResolver

    Examples:
        >>> resolver = get_icon_resolver()
        >>> svg = resolver.get_icon_svg('task', 'user_task')
    """
    global _icon_resolver_instance

    if icons_yaml_path is None:
        icons_yaml_path = Path("data/icons/icons.yaml")

    if _icon_resolver_instance is None or reload:
        _icon_resolver_instance = IconResolver(icons_yaml_path)

    return _icon_resolver_instance
