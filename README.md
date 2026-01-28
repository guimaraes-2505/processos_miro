# Sistema de Mapeamento de Processos

Sistema automatizado para mapear processos de agência de marketing digital, convertendo transcrições em diagramas visuais simplificados no Miro e tarefas no ClickUp.

## Visão Geral

Este sistema realiza três etapas principais:

1. **Leitura e Extração**: Processa transcrições em Markdown usando IA (Claude) para extrair elementos de processo
2. **Visualização no Miro**: Cria diagramas visuais simplificados (não BPMN complexo) via MCP
3. **Gestão no ClickUp**: Sincroniza tarefas e responsáveis no ClickUp via MCP

### Representação Visual Simplificada

O sistema utiliza elementos visuais simples e intuitivos:
- 📦 **Tarefas**: Retângulos com texto descritivo
- 💎 **Decisões**: Diamantes para pontos de decisão
- 🟢 **Início**: Círculos verdes
- 🔴 **Fim**: Círculos vermelhos
- 📝 **Notas**: Sticky notes amarelas para observações
- ➡️ **Conexões**: Setas simples entre elementos

## Instalação

### Pré-requisitos

- Python 3.10 ou superior
- Node.js e npm (para servidores MCP)
- Contas configuradas:
  - **[Miro](https://miro.com/)** (obrigatório)
  - [Anthropic Claude API](https://console.anthropic.com/) **OU** acesso ao [Claude.ai](https://claude.ai) (web/CLI)
  - [ClickUp](https://clickup.com/) (opcional - Fase 6)

### Modos de Operação

**🆓 Modo Claude Code (Recomendado)**
- Usa Claude.ai ou este ambiente Claude Code
- Processo interativo (copiar/colar)
- **Grátis** - sem custos de API

**💳 Modo API**
- Totalmente automático
- Requer API key do Anthropic
- Custos de acordo com uso

### Setup

1. Clone o repositório e navegue até o diretório:
```bash
cd Processos_Miro
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

5. Configure os servidores MCP (veja [docs/mcp_setup.md](docs/mcp_setup.md))

## Configuração

### Escolher Modo de Extração

Edite o arquivo `.env`:

```env
# Modo Claude Code (grátis, interativo)
EXTRACTION_MODE=claude-code

# OU Modo API (pago, automático)
# EXTRACTION_MODE=api
# ANTHROPIC_API_KEY=sk-ant-...
```

### Obter Credenciais

#### Claude API (OPCIONAL - só para modo API)
1. Acesse https://console.anthropic.com/
2. Crie uma API key
3. Adicione ao `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

#### Miro (OBRIGATÓRIO)
1. Acesse https://miro.com/app/settings/user-profile/apps
2. Crie um novo app com permissões `boards:read` e `boards:write`
3. Copie o Access Token
4. Adicione ao `.env`: `MIRO_API_TOKEN=...`

#### ClickUp (OPCIONAL - Fase 6)
1. Acesse ClickUp Settings → Apps → API Token
2. Gere um Personal API Token
3. Obtenha o Team ID da URL do workspace: `https://app.clickup.com/{TEAM_ID}/...`
4. Adicione ao `.env`:
   ```
   CLICKUP_API_TOKEN=...
   CLICKUP_TEAM_ID=...
   ```

**Nota**: ClickUp é opcional. O sistema funciona perfeitamente apenas com Miro.

## Uso

### Teste Rápido (com exemplo)

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar teste completo
python3 test_miro_integration.py
```

**No modo Claude Code**: O sistema pausará e pedirá que você cole uma resposta JSON. Siga as instruções na tela.

### Processar uma Transcrição

```bash
python -m src.main process data/input/meu_processo.md
```

### Opções Avançadas
```bash
# Apenas extrair e validar (sem criar no Miro/ClickUp)
python -m src.main process input.md --skip-miro --skip-clickup

# Processar com nível de log específico
python -m src.main process input.md --log-level DEBUG
```

## Formato de Entrada

As transcrições devem estar em formato Markdown (.md). Exemplo:

```markdown
# Processo de Aprovação de Projetos

## Descrição
Fluxo para aprovar novos projetos de clientes.

## Etapas

1. **Receber briefing** (Cliente)
   - Cliente envia requisitos do projeto

2. **Analisar viabilidade** (Gerente de Projetos)
   - Revisar escopo e recursos necessários
   - Estimar prazos e custos

3. **Decisão: Projeto é viável?** (Gerente de Projetos)
   - Se sim: continuar para criação de proposta
   - Se precisa ajustes: solicitar mais informações ao cliente
   - Se não: arquivar e notificar cliente

4. **Criar proposta** (Gerente de Projetos)
   - Elaborar documento com escopo, cronograma e orçamento
   - **Nota**: Sempre usar o template padrão da empresa

5. **Enviar para aprovação** (Diretor)
   - Revisar e aprovar proposta

6. **Fim**: Projeto aprovado e pronto para execução
```

## Estrutura do Projeto

```
Processos_Miro/
├── config/           # Configurações e MCP
├── src/              # Código fonte
│   ├── parsers/      # Extração de transcrições
│   ├── models/       # Modelos de dados
│   ├── converters/   # Conversão de formatos
│   ├── layout/       # Cálculo de posicionamento
│   ├── integrations/ # Clientes MCP (Miro/ClickUp)
│   └── utils/        # Utilitários (logger, exceptions)
├── data/             # Dados de entrada/saída
├── tests/            # Testes automatizados
└── docs/             # Documentação detalhada
```

## Arquitetura

```
Markdown → Parser → LLM Extractor → Modelo → Conversor → Layout → Miro
                                                                    ↓
                                                                 ClickUp
```

1. **Parser**: Pré-processa o markdown
2. **LLM Extractor**: Usa Claude para extrair elementos estruturados
3. **Modelo**: Formato intermediário neutro
4. **Conversor**: Adapta para formato interno simplificado
5. **Layout**: Calcula posições dos elementos
6. **Miro**: Cria diagrama visual
7. **ClickUp**: Cria tarefas e dependências

## Desenvolvimento

### Executar Testes
```bash
pytest tests/
```

### Verificar Tipagem
```bash
mypy src/
```

### Formatar Código
```bash
black src/ tests/
```

### Linting
```bash
flake8 src/ tests/
```

## Documentação

- [Arquitetura Detalhada](docs/architecture.md)
- [Configuração MCP](docs/mcp_setup.md)
- [Exemplos](docs/examples.md)

## Roadmap

- [x] Fase 1: Fundação (estrutura, modelos, utils)
- [x] Fase 2: Parsing e Extração via LLM (com modo interativo!)
- [x] Fase 3: Conversão de Dados
- [x] Fase 4: Layout Automático
- [x] Fase 5: Integração Miro
- [ ] Fase 6: Integração ClickUp
- [ ] Fase 7: CLI e Orquestração
- [ ] Fase 8: Refinamento e Otimização

**Status atual**: 62.5% concluído! 🎉

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
Se você está usando `EXTRACTION_MODE=claude-code`, isso é normal! Você não precisa de API key.

**Solução**: Verifique o `.env`:
```env
EXTRACTION_MODE=claude-code  # Deve estar assim
```

### Sistema não pede resposta interativa
- Confirme que `EXTRACTION_MODE=claude-code` no `.env`
- Verifique os logs em `data/output/process_mapper.log`

### Modo API não funciona
- Verifique se a API key do Claude está correta no `.env`
- Confirme que `EXTRACTION_MODE=api`
- Verifique se tem créditos disponíveis em console.anthropic.com

### Erro de conexão MCP
- Verifique se Node.js está instalado: `node --version`
- Verifique os tokens no arquivo `.env`
- Consulte [docs/mcp_setup.md](docs/mcp_setup.md)

### Problemas de layout
- Ajuste os parâmetros de espaçamento no `.env`
- Verifique os logs em `data/output/process_mapper.log`

## Contribuindo

1. Crie uma branch para sua feature: `git checkout -b feature/minha-feature`
2. Faça commit das mudanças: `git commit -m 'Adiciona nova feature'`
3. Push para a branch: `git push origin feature/minha-feature`
4. Abra um Pull Request

## Licença

MIT License - veja LICENSE para detalhes

## Suporte

Para problemas ou dúvidas:
- Abra uma issue no repositório
- Consulte a documentação em `/docs`
- Verifique os logs em `data/output/`

---

**Nota**: Este sistema foi projetado para simplificar o mapeamento de processos, evitando complexidade desnecessária de notações BPMN formais. O foco é na clareza e facilidade de uso para equipes com baixa maturidade em modelagem de processos.
