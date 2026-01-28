# CLAUDE.md - Processos_Miro

## Visao Geral

Sistema de mapeamento de processos BPM com geracao automatica de documentacao e integracao com Miro e ClickUp.

**Objetivo**: Ajudar no mapeamento de macroprocessos, processos e subprocessos, alem de gerar documentacao para padronizacao (POP, checklists, instrucoes de trabalho).

---

## Manifesto da Metodologia BPM

### Filosofia Central

> "O simples funciona - e muito!"

- **Simplicidade**: Evitar complexidade desnecessaria, foco no que funciona
- **Conexao**: Toda documentacao deve estar conectada a hierarquia de processos
- **Autonomia**: Colaborador deve ser capaz de executar sem apoio externo
- **Melhoria continua**: Ciclo AS-IS (como e hoje) para TO-BE (como deve ser)

---

### Hierarquia de Processos (5 Niveis)

```
NIVEL 1: CADEIA DE VALOR (Estrategico)
├── Visao completa do negocio
├── Apresentar para: CEO, Diretores
├── Ferramenta: Miro (board principal)
└── Frameworks: Porter, HAP (O2C, H2R, P2P, R2R)
        ↓
NIVEL 2: MACROPROCESSOS (Tatico)
├── Tipos: Primarios | Apoio | Gestao
├── Apresentar para: Gerentes
├── Ferramenta: Miro (board com SIPOC)
└── Indicadores de planejamento estrategico
        ↓
NIVEL 3: PROCESSOS E SUBPROCESSOS (Operacional)
├── Documentacao: POP (Procedimento Operacional Padrao)
├── Ferramenta: Miro (BPMN simplificado com swimlanes)
└── Indicadores: Qualidade, Produtividade, Compliance
        ↓
NIVEL 4: ATIVIDADES (Tatico-Operacional)
├── Documentacao: IT (Instrucao de Trabalho)
├── Ferramenta: ClickUp (Tasks com descricao detalhada)
└── Verbos: Gerar, Verificar, Encaminhar, Processar
        ↓
NIVEL 5: TAREFAS (Operacional Detalhado)
├── Documentacao: Checklist
├── Ferramenta: ClickUp (Checklists nativos + Subtarefas)
└── "Como" executar (cliques, acessos, transacoes)
```

---

### Tipos de Macroprocessos

| Tipo | Descricao | Exemplos |
|------|-----------|----------|
| **Primarios** | Impacto direto no produto/servico, contem conhecimento tecnico do negocio | Marketing, Vendas, Producao, Entrega |
| **Apoio** | Suportam os primarios, garantem funcionamento eficiente | RH, TI, Financeiro, Juridico |
| **Gestao** | Monitoram, medem e controlam | Qualidade, Estrategia, Compliance, Auditoria |

---

### Mapeamento Ferramenta por Nivel

| Nivel | Ferramenta | Representacao | Documento |
|-------|------------|---------------|-----------|
| Cadeia de Valor | **Miro** | Board com frames por area | - |
| Macroprocessos | **Miro** | Board com SIPOC + conexoes | - |
| Processos | **Miro** | Board BPMN com swimlanes | POP |
| Atividades | **ClickUp** | Tasks com descricao IT | IT |
| Tarefas | **ClickUp** | Checklists nativos | Checklist |

---

### SIPOC - Ferramenta Central

Para cada macroprocesso e processo, definir:

| Componente | Descricao | Perguntas |
|------------|-----------|-----------|
| **S**uppliers | Quem fornece os insumos | Quem me entrega algo? (interno/externo) |
| **I**nputs | O que e necessario para iniciar | O que preciso para comecar? |
| **P**rocess | Passos principais (resumo) | Quais as etapas macro? |
| **O**utputs | Entregas geradas | O que eu entrego? |
| **C**ustomers | Quem recebe as entregas | Para quem eu entrego? (interno/externo) |

---

### Tipos de Documentacao

| Documento | Codigo | Nivel | Objetivo | Caracteristicas |
|-----------|--------|-------|----------|-----------------|
| **POP** | POP-XXX | Processo | Documenta o fluxo completo | BPMN numerado + descricoes, novo colaborador executa sem apoio |
| **IT** | IT-XXX | Atividade | Instrucoes detalhadas | Maximo de detalhes (prints, imagens, fotos) |
| **Checklist** | CL-XXX | Tarefa/Entrega | Garante execucao correta | "O simples funciona!" - evita esquecimentos |
| **Manual** | MAN-XXX | Ferramenta | Uso de sistemas e frameworks | Como manual de uma TV |
| **Politica** | POL-XXX | Organizacao | Diretrizes e regras macro | Visao macro, guia acoes e decisoes |

---

## Arquitetura do Sistema

### Pipeline Principal

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PIPELINE DE DADOS                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  MARKDOWN           MODELOS                MIRO                      │
│  ┌──────┐          ┌──────────┐          ┌──────────┐               │
│  │.md   │ ──parse→ │ Process  │ ────────→│ Board    │               │
│  │file  │          │ Model    │          │ + Frames │               │
│  └──────┘          └──────────┘          └──────────┘               │
│                          │                     │                     │
│                          │                     │ board_id            │
│                          ↓                     ↓                     │
│                    ┌──────────┐          ┌──────────┐               │
│                    │ Documen- │          │ Reference│               │
│                    │ tation   │          │ Links    │               │
│                    │ Models   │          └──────────┘               │
│                    │(POP,IT)  │               │                      │
│                    └──────────┘               │                      │
│                          │                    │                      │
│                          ↓                    ↓                      │
│                    ┌─────────────────────────────────┐              │
│                    │           CLICKUP               │              │
│                    │  ┌───────────────────────────┐  │              │
│                    │  │ Tasks with:               │  │              │
│                    │  │ - IT as description       │  │              │
│                    │  │ - Checklists              │  │              │
│                    │  │ - Miro board link         │  │              │
│                    │  │ - Dependencies            │  │              │
│                    │  └───────────────────────────┘  │              │
│                    └─────────────────────────────────┘              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Estrutura de Diretorios

```
Processos_Miro/
├── CLAUDE.md                    # Este arquivo - manifesto e orientacoes
├── config/
│   ├── settings.py              # Configuracoes centralizadas (Pydantic)
│   ├── mcp_miro.json            # Config MCP Miro
│   └── mcp_clickup.json         # Config MCP ClickUp
│
├── src/
│   ├── models/                  # Modelos de dados (Pydantic)
│   │   ├── process_model.py     # Process, ProcessElement, ProcessFlow
│   │   ├── visual_model.py      # VisualElement, VisualDiagram
│   │   ├── hierarchy_model.py   # ValueChain, Macroprocess, SIPOC
│   │   └── documentation_model.py # POP, IT, Checklist
│   │
│   ├── parsers/                 # Extracao e parsing
│   │   ├── markdown_parser.py   # Parse de Markdown
│   │   ├── llm_extractor.py     # Extracao via Claude
│   │   └── hierarchy_extractor.py # Extracao de hierarquia
│   │
│   ├── converters/              # Conversao entre formatos
│   │   ├── process_to_visual.py # Process -> VisualDiagram
│   │   ├── visual_to_miro.py    # VisualDiagram -> Miro
│   │   ├── hierarchy_to_miro.py # Hierarquia -> Miro
│   │   └── process_to_clickup.py # Process -> ClickUp
│   │
│   ├── generators/              # Geradores de documentacao
│   │   ├── base_generator.py    # Classe base abstrata
│   │   ├── pop_generator.py     # Gerador de POPs
│   │   ├── it_generator.py      # Gerador de ITs
│   │   ├── checklist_generator.py # Gerador de Checklists
│   │   └── sipoc_generator.py   # Gerador de SIPOCs
│   │
│   ├── layout/                  # Calculo de layout
│   │   ├── swimlane_layout.py   # Layout de swimlanes
│   │   ├── auto_layout.py       # Layered graph drawing
│   │   ├── value_chain_layout.py # Layout Cadeia de Valor
│   │   └── sipoc_layout.py      # Layout SIPOC
│   │
│   ├── integrations/            # Clientes de APIs
│   │   ├── miro_client.py       # Cliente Miro REST API
│   │   └── clickup_client.py    # Cliente ClickUp API
│   │
│   ├── sync/                    # Sincronizacao
│   │   └── miro_clickup_sync.py # Sync Miro <-> ClickUp
│   │
│   └── utils/                   # Utilitarios
│       ├── logger.py            # Logging com Loguru
│       └── exceptions.py        # Excecoes customizadas
│
├── data/
│   ├── input/                   # Arquivos de entrada (.md)
│   ├── intermediate/            # Arquivos intermediarios (.json)
│   ├── output/                  # Logs e saidas
│   └── templates/               # Templates de documentacao
│       ├── pop_template.md
│       ├── it_template.md
│       ├── checklist_template.md
│       └── sipoc_template.md
│
└── tests/                       # Testes automatizados
```

---

## Modelos de Dados

### Hierarquia (hierarchy_model.py)

```python
ValueChain           # Cadeia de Valor - nivel estrategico
├── id, name, description
├── mission, vision
└── macroprocesses: List[str]  # IDs

Macroprocess         # Macroprocesso - nivel tatico
├── id, name, description
├── type: 'primario' | 'apoio' | 'gestao'
├── objective, owner
├── processes: List[str]  # IDs
└── sipoc: SIPOC

SIPOC                # Ferramenta SIPOC
├── suppliers: List[SIPOCItem]
├── inputs: List[SIPOCItem]
├── process_steps: List[str]
├── outputs: List[SIPOCItem]
└── customers: List[SIPOCItem]
```

### Documentacao (documentation_model.py)

```python
POP                  # Procedimento Operacional Padrao
├── code: str        # POP-001
├── title, version, status
├── objective, scope
├── process_map: ProcessMap  # BPMN numerado
└── step_descriptions: List[StepDescription]

IT                   # Instrucao de Trabalho
├── code: str        # IT-001
├── activity_id
├── steps: List[ITStep]  # Com prints/imagens
└── quality_criteria

Checklist            # Checklist de verificacao
├── code: str        # CL-001
├── purpose, frequency
└── items: List[ChecklistItem]
```

---

## Padroes de Nomenclatura

### Processos e Macroprocessos

| Tipo | Padrao | Exemplo |
|------|--------|---------|
| Macroprocesso Primario | `MACRO-PRI-{numero}` | MACRO-PRI-001 |
| Macroprocesso Apoio | `MACRO-APO-{numero}` | MACRO-APO-001 |
| Macroprocesso Gestao | `MACRO-GES-{numero}` | MACRO-GES-001 |
| Processo | `PROC-{area}-{numero}` | PROC-MKT-001 |
| Subprocesso | `SUB-{processo}-{numero}` | SUB-MKT001-001 |

### Documentos

| Tipo | Padrao | Exemplo |
|------|--------|---------|
| POP | `POP-{numero}` | POP-001 |
| IT | `IT-{numero}` | IT-001 |
| Checklist | `CL-{numero}` | CL-001 |
| Manual | `MAN-{numero}` | MAN-001 |
| Politica | `POL-{numero}` | POL-001 |

### Elementos de Processo

| Tipo | Padrao | Exemplo |
|------|--------|---------|
| Elemento | `{processo}_E{numero}` | PROC-MKT-001_E01 |
| Atividade numerada | `{swimlane}.{sequencia}` | 1.1, 1.2, 2.1 |

---

## Convencoes de Codigo

### Python

- **Versao**: Python 3.10+
- **Modelos**: Pydantic v2 com type hints completos
- **Validacao**: Field validators para regras de negocio
- **Logging**: Loguru via `src/utils/logger.py`
- **Excecoes**: Hierarquia em `src/utils/exceptions.py`

### Imports

```python
# Padrao de imports
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator
from config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.exceptions import ProcessMapperError
```

### Docstrings

```python
def funcao(param1: str, param2: int) -> Dict:
    """
    Descricao breve da funcao.

    Args:
        param1: Descricao do parametro 1
        param2: Descricao do parametro 2

    Returns:
        Descricao do retorno

    Raises:
        ProcessMapperError: Quando algo da errado
    """
```

---

## Regras de Negocio

### Processos

1. Todo processo deve ter inicio (evento start) e fim (evento end)
2. Gateways (decisoes) devem ter >= 2 saidas
3. Elementos devem ter responsavel (actor) definido
4. Nomes de elementos devem usar verbos no infinitivo

### Documentacao

1. POP requer mapeamento BPMN numerado
2. IT deve ter nivel de detalhe suficiente para execucao autonoma
3. Checklists devem ser baseados em entregas/outputs
4. Toda documentacao deve referenciar o processo pai

### Integracao

1. Boards do Miro devem ter links para ClickUp
2. Tasks do ClickUp devem ter link para board do Miro
3. Metadata deve manter referencias cruzadas (IDs)

---

## Estrutura Visual no Miro

### Cadeia de Valor

```
┌────────────────────────────────────────────────────────────────┐
│                    CADEIA DE VALOR                             │
├────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐  │
│ │              MACROPROCESSOS PRIMARIOS                     │  │
│ │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │  │
│ │  │Marketing│→ │ Vendas  │→ │Producao │→ │ Entrega │     │  │
│ │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │  │
│ └──────────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │              MACROPROCESSOS DE APOIO                      │  │
│ │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │  │
│ │  │   RH    │  │   TI    │  │Financeiro│  │ Juridico│     │  │
│ │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │  │
│ └──────────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │              MACROPROCESSOS DE GESTAO                     │  │
│ │  ┌─────────┐  ┌─────────┐  ┌─────────┐                  │  │
│ │  │Qualidade│  │Estrategia│  │Compliance│                  │  │
│ │  └─────────┘  └─────────┘  └─────────┘                  │  │
│ └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### SIPOC

```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│SUPPLIERS │ │  INPUTS  │ │ PROCESS  │ │ OUTPUTS  │ │CUSTOMERS │
├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤
│ Item 1   │ │ Item 1   │ │→ Etapa 1 │ │ Item 1   │ │ Item 1   │
│ Item 2   │ │ Item 2   │ │→ Etapa 2 │ │ Item 2   │ │ Item 2   │
│ Item 3   │ │ Item 3   │ │→ Etapa 3 │ │ Item 3   │ │ Item 3   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## Estrutura no ClickUp

```
📁 Space: [Nome do Macroprocesso]
│
├── 📂 Folder: [Nome do Processo]
│   │
│   ├── 📋 List: Atividades
│   │   ├── ✅ Task: [Codigo] [Nome da Atividade]
│   │   │   ├── Description: Instrucao de Trabalho (IT)
│   │   │   ├── Checklist: Pontos de verificacao
│   │   │   ├── Subtasks: Tarefas detalhadas
│   │   │   └── Custom Fields: Miro Link, Codigo POP, Responsavel, SLA
│   │   └── ...
│   │
│   └── 📋 List: Documentacao
│       ├── 📄 POP do Processo (link Miro)
│       └── 📄 SIPOC (link Miro)
```

---

## Variaveis de Ambiente

```env
# Miro (OBRIGATORIO)
MIRO_API_TOKEN=seu_token_miro

# ClickUp (OBRIGATORIO para integracao)
CLICKUP_API_TOKEN=seu_token_clickup
CLICKUP_TEAM_ID=seu_team_id
CLICKUP_SPACE_ID=seu_space_id

# Claude API (OPCIONAL - para modo automatico)
ANTHROPIC_API_KEY=sua_api_key

# Modo de extracao
EXTRACTION_MODE=claude-code  # claude-code | api | manual

# Configuracoes de layout
SWIMLANE_HEIGHT=200
ELEMENT_SPACING_X=150
```

---

## Comandos Uteis

```bash
# Pipeline completo: Markdown -> Miro
python -m src.main process data/input/processo.md

# Gerar documentacao
python -m src.main generate-pop PROC-001
python -m src.main generate-it PROC-001_E01
python -m src.main generate-checklist PROC-001

# Sincronizar com ClickUp
python -m src.main sync-clickup PROC-001

# Criar Cadeia de Valor no Miro
python -m src.main create-value-chain data/input/cadeia.md

# Testes
pytest tests/
pytest tests/test_hierarchy_model.py -v
```

---

## Referencias

### Metodologia BPM

- Arquivos em `base_teoria/` contem a base teorica completa
- Cadeia de Valor de Porter
- Cadeias HAP: O2C, H2R, P2P, R2R
- Notacao BPMN simplificada

### APIs

- [Miro REST API v2](https://developers.miro.com/reference/api-reference)
- [ClickUp API v2](https://clickup.com/api)
- [Claude API](https://docs.anthropic.com/claude/reference)

### Projeto

- README.md: Visao geral e instalacao
- COMO_USAR.md: Guia pratico em portugues
- FASE5_MIRO.md: Detalhes da integracao Miro
