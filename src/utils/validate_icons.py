"""
Utilitário para validação de ícones BPMN.

Este módulo fornece funções para validar:
- Arquivos SVG (formato, tamanho, estrutura)
- Arquivo icons.yaml (sintaxe, referências)
- Biblioteca completa de ícones

Pode ser executado como script de linha de comando:
    python -m src.utils.validate_icons
    python -m src.utils.validate_icons --yaml-only
    python -m src.utils.validate_icons --list
"""

import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, List, Dict, Any
import yaml

from src.utils.logger import get_logger
from src.utils.icon_library import IconResolver, IconLoadError

logger = get_logger(__name__)


class ValidationResult:
    """
    Resultado de validação.

    Attributes:
        is_valid: Se a validação passou
        errors: Lista de erros encontrados
        warnings: Lista de avisos
        info: Informações adicionais
    """

    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def add_error(self, message: str) -> None:
        """Adiciona um erro."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Adiciona um aviso."""
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        """Adiciona informação."""
        self.info.append(message)

    def print_summary(self) -> None:
        """Imprime resumo da validação."""
        print("\n" + "=" * 70)
        print("RESUMO DA VALIDAÇÃO")
        print("=" * 70)

        if self.info:
            print(f"\nℹ️  INFORMAÇÕES ({len(self.info)}):")
            for msg in self.info:
                print(f"  • {msg}")

        if self.warnings:
            print(f"\n⚠️  AVISOS ({len(self.warnings)}):")
            for msg in self.warnings:
                print(f"  • {msg}")

        if self.errors:
            print(f"\n❌ ERROS ({len(self.errors)}):")
            for msg in self.errors:
                print(f"  • {msg}")

        print(f"\n{'✅ VALIDAÇÃO PASSOU' if self.is_valid else '❌ VALIDAÇÃO FALHOU'}")
        print("=" * 70 + "\n")


def validate_svg_file(file_path: Path, max_size_kb: int = 5) -> ValidationResult:
    """
    Valida um arquivo SVG individual.

    Verifica:
    - Arquivo existe e é legível
    - É XML válido
    - Contém tag <svg> raiz
    - Tamanho é aceitável
    - Possui viewBox (recomendado)

    Args:
        file_path: Caminho do arquivo SVG
        max_size_kb: Tamanho máximo em KB

    Returns:
        ValidationResult com resultados da validação
    """
    result = ValidationResult()

    # Verificar existência
    if not file_path.exists():
        result.add_error(f"Arquivo não encontrado: {file_path}")
        return result

    # Verificar tamanho
    size_kb = file_path.stat().st_size / 1024
    if size_kb > max_size_kb:
        result.add_warning(
            f"Arquivo muito grande: {size_kb:.1f}KB (máximo recomendado: {max_size_kb}KB)"
        )

    # Verificar se é XML válido
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        result.add_error(f"XML inválido: {e}")
        return result

    # Verificar tag <svg>
    # Namespace SVG
    if not (root.tag.endswith("svg") or root.tag == "svg"):
        result.add_error(f"Tag raiz não é <svg>: {root.tag}")
        return result

    # Verificar viewBox (recomendado mas não obrigatório)
    if "viewBox" not in root.attrib:
        result.add_warning("Atributo 'viewBox' não encontrado (recomendado)")

    # Verificar xmlns
    if "xmlns" not in root.attrib and not root.tag.startswith("{"):
        result.add_info("Namespace SVG não declarado explicitamente")

    result.add_info(f"Arquivo válido: {file_path.name} ({size_kb:.1f}KB)")
    return result


def validate_yaml_syntax(yaml_path: Path) -> ValidationResult:
    """
    Valida sintaxe do arquivo icons.yaml.

    Args:
        yaml_path: Caminho do arquivo YAML

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    if not yaml_path.exists():
        result.add_error(f"Arquivo não encontrado: {yaml_path}")
        return result

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            result.add_error("Arquivo YAML vazio")
            return result

        # Verificar seções esperadas
        expected_sections = ["tasks", "events", "gateways", "config"]
        for section in expected_sections:
            if section not in data:
                result.add_warning(f"Seção '{section}' não encontrada")
            else:
                count = len(data[section]) if isinstance(data[section], dict) else 0
                result.add_info(f"Seção '{section}': {count} entradas")

        result.add_info(f"YAML válido: {yaml_path}")

    except yaml.YAMLError as e:
        result.add_error(f"Erro de sintaxe YAML: {e}")

    return result


def validate_icon_references(yaml_path: Path) -> ValidationResult:
    """
    Valida se todos os arquivos referenciados no YAML existem.

    Args:
        yaml_path: Caminho do arquivo icons.yaml

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        base_path = Path(data.get("config", {}).get("base_path", "data/icons"))

        # Verificar todas as referências
        total_refs = 0
        missing_refs = 0

        for category in ["tasks", "events", "gateways"]:
            if category not in data:
                continue

            for icon_type, icon_path in data[category].items():
                total_refs += 1
                full_path = base_path / icon_path

                if not full_path.exists():
                    result.add_error(
                        f"Arquivo não encontrado: {icon_type} → {icon_path}"
                    )
                    missing_refs += 1

        if missing_refs == 0:
            result.add_info(
                f"✓ Todas as {total_refs} referências apontam para arquivos existentes"
            )
        else:
            result.add_error(
                f"{missing_refs} de {total_refs} referências não encontradas"
            )

    except Exception as e:
        result.add_error(f"Erro ao validar referências: {e}")

    return result


def validate_icon_library(yaml_path: Path) -> ValidationResult:
    """
    Valida a biblioteca completa de ícones.

    Executa validação completa:
    - Sintaxe YAML
    - Referências de arquivos
    - Validação de cada SVG
    - Carregamento pelo IconResolver

    Args:
        yaml_path: Caminho do arquivo icons.yaml

    Returns:
        ValidationResult agregado
    """
    overall_result = ValidationResult()

    print("\n🔍 Validando biblioteca de ícones...")
    print(f"   Arquivo: {yaml_path}\n")

    # 1. Validar sintaxe YAML
    print("1️⃣  Validando sintaxe YAML...")
    yaml_result = validate_yaml_syntax(yaml_path)
    overall_result.errors.extend(yaml_result.errors)
    overall_result.warnings.extend(yaml_result.warnings)
    overall_result.info.extend(yaml_result.info)

    if not yaml_result.is_valid:
        overall_result.is_valid = False
        return overall_result

    # 2. Validar referências
    print("2️⃣  Validando referências de arquivos...")
    ref_result = validate_icon_references(yaml_path)
    overall_result.errors.extend(ref_result.errors)
    overall_result.warnings.extend(ref_result.warnings)
    overall_result.info.extend(ref_result.info)

    if not ref_result.is_valid:
        overall_result.is_valid = False

    # 3. Validar cada arquivo SVG
    print("3️⃣  Validando arquivos SVG...")
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        base_path = Path(data.get("config", {}).get("base_path", "data/icons"))
        svg_count = 0

        for category in ["tasks", "events", "gateways"]:
            if category not in data:
                continue

            for icon_type, icon_path in data[category].items():
                full_path = base_path / icon_path

                if full_path.exists():
                    svg_result = validate_svg_file(full_path)
                    svg_count += 1

                    overall_result.errors.extend(svg_result.errors)
                    overall_result.warnings.extend(svg_result.warnings)

                    if not svg_result.is_valid:
                        overall_result.is_valid = False

        overall_result.add_info(f"✓ {svg_count} arquivos SVG validados")

    except Exception as e:
        overall_result.add_error(f"Erro ao validar SVGs: {e}")
        overall_result.is_valid = False

    # 4. Testar carregamento com IconResolver
    print("4️⃣  Testando carregamento com IconResolver...")
    try:
        resolver = IconResolver(yaml_path)
        stats = resolver.get_stats()

        if stats.get("loaded"):
            overall_result.add_info(
                f"✓ IconResolver carregado com sucesso: "
                f"{stats['total_tasks']} tasks, "
                f"{stats['total_events']} events, "
                f"{stats['total_gateways']} gateways"
            )
        else:
            overall_result.add_error("IconResolver falhou ao carregar biblioteca")
            overall_result.is_valid = False

    except IconLoadError as e:
        overall_result.add_error(f"Erro ao carregar IconResolver: {e}")
        overall_result.is_valid = False

    return overall_result


def list_available_icons(yaml_path: Path) -> None:
    """
    Lista todos os ícones disponíveis na biblioteca.

    Args:
        yaml_path: Caminho do arquivo icons.yaml
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        base_path = Path(data.get("config", {}).get("base_path", "data/icons"))

        print("\n" + "=" * 70)
        print("ÍCONES DISPONÍVEIS")
        print("=" * 70)

        for category in ["tasks", "events", "gateways"]:
            if category not in data:
                continue

            print(f"\n📂 {category.upper()}")
            print("-" * 70)

            for icon_type, icon_path in sorted(data[category].items()):
                full_path = base_path / icon_path
                status = "✓" if full_path.exists() else "✗"
                size = (
                    f"{full_path.stat().st_size / 1024:.1f}KB"
                    if full_path.exists()
                    else "N/A"
                )

                print(f"  {status} {icon_type:25} → {icon_path:40} ({size})")

        print("\n" + "=" * 70 + "\n")

    except Exception as e:
        print(f"❌ Erro ao listar ícones: {e}")


def main() -> int:
    """
    Função principal do script de validação.

    Returns:
        Código de saída (0 = sucesso, 1 = falha)
    """
    parser = argparse.ArgumentParser(
        description="Valida biblioteca de ícones BPMN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m src.utils.validate_icons                    # Validação completa
  python -m src.utils.validate_icons --yaml-only        # Apenas YAML
  python -m src.utils.validate_icons --list             # Listar ícones
  python -m src.utils.validate_icons --file task.svg    # Validar arquivo específico
        """,
    )

    parser.add_argument(
        "--yaml",
        type=Path,
        default=Path("data/icons/icons.yaml"),
        help="Caminho do arquivo icons.yaml (padrão: data/icons/icons.yaml)",
    )

    parser.add_argument(
        "--yaml-only",
        action="store_true",
        help="Validar apenas sintaxe do YAML",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar todos os ícones disponíveis",
    )

    parser.add_argument(
        "--file",
        type=Path,
        help="Validar arquivo SVG específico",
    )

    args = parser.parse_args()

    # Listar ícones
    if args.list:
        list_available_icons(args.yaml)
        return 0

    # Validar arquivo específico
    if args.file:
        print(f"\n🔍 Validando arquivo SVG: {args.file}\n")
        result = validate_svg_file(args.file)
        result.print_summary()
        return 0 if result.is_valid else 1

    # Validar apenas YAML
    if args.yaml_only:
        print(f"\n🔍 Validando sintaxe YAML: {args.yaml}\n")
        result = validate_yaml_syntax(args.yaml)
        result.print_summary()
        return 0 if result.is_valid else 1

    # Validação completa
    result = validate_icon_library(args.yaml)
    result.print_summary()
    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
