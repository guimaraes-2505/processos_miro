# Biblioteca de Ícones BPMN

## 📋 Visão Geral

Esta pasta contém os ícones SVG utilizados para representar elementos BPMN (Business Process Model and Notation) nos diagramas gerados pelo sistema Processos_Miro.

O sistema mapeia automaticamente cada tipo de elemento BPMN ao seu respectivo ícone, criando diagramas visuais consistentes e padronizados.

---

## 📁 Estrutura de Diretórios

```
data/icons/
├── tasks/                              # Ícones para tarefas (retângulos)
│   ├── task.svg                        # Tarefa genérica (fallback)
│   ├── user-task.svg                   # Tarefa de usuário
│   ├── service-task.svg                # Tarefa de serviço/automação
│   └── subprocess.svg                  # Subprocesso
│
├── events/                             # Ícones para eventos (círculos)
│   ├── start-event.svg                 # Início simples
│   ├── start-timer-event.svg           # Início por timer
│   ├── start-message-event.svg         # Início por mensagem
│   ├── start-conditional-event.svg     # Início condicional
│   ├── start-error-event.svg           # Início por erro
│   ├── start-signal-event.svg          # Início por sinal
│   ├── start-multiple-event.svg        # Início múltiplo
│   ├── intermediate-timer-event.svg    # Intermediário timer
│   ├── intermediate-message-event.svg  # Intermediário mensagem
│   ├── intermediate-conditional-event.svg
│   ├── intermediate-signal-event.svg
│   ├── intermediate-compensation-event.svg
│   ├── intermediate-multiple-event.svg
│   ├── intermediate-link-catch-event.svg
│   ├── intermediate-link-throw-event.svg
│   ├── intermediate-cancel-event.svg
│   ├── end-event.svg                   # Fim simples
│   ├── end-message-event.svg           # Fim por mensagem
│   ├── end-signal-event.svg            # Fim por sinal
│   └── end-multiple-event.svg          # Fim múltiplo
│
├── gateways/                           # Símbolos para gateways (losangos)
│   ├── exclusive-gateway.svg           # XOR - Escolha exclusiva
│   ├── inclusive-gateway.svg           # OR - Escolha inclusiva
│   ├── parallel-gateway.svg            # AND - Execução paralela
│   └── event-based-gateway.svg         # Baseado em evento
│
├── icons.yaml          # Configuração e mapeamento
└── README.md           # Este arquivo
```

---

## 🎨 Especificações Técnicas dos SVGs

Para garantir compatibilidade e qualidade, os arquivos SVG devem seguir estas especificações:

### Formato
- **Padrão**: SVG 1.1 ou superior
- **ViewBox**: `viewBox="0 0 24 24"` (recomendado)
- **Tamanho**: Máximo 5KB por arquivo
- **Encoding**: UTF-8

### Estilo
- **Cores**: Usar `currentColor` para herdar cor do elemento pai
- **Preenchimento**: Definir `fill` e `stroke` conforme necessário
- **Transparência**: Evitar transparências complexas

### Exemplo de SVG Válido

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <!-- Ícone de User Task -->
  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
        fill="currentColor"/>
</svg>
```

---

## 📝 Como Adicionar Seus Ícones

### Passo 1: Preparar o arquivo SVG

1. Certifique-se de que o SVG está otimizado (sem elementos desnecessários)
2. Ajuste o `viewBox` para `0 0 24 24`
3. Use `currentColor` para cores que devem herdar do tema
4. Teste o SVG em um visualizador

### Passo 2: Nomear o arquivo

Use **kebab-case** (palavras separadas por hífen):

✅ **Correto**:
- `user-task.svg`
- `exclusive-gateway.svg`
- `start-timer-event.svg`

❌ **Incorreto**:
- `UserTask.svg`
- `exclusive_gateway.svg`
- `StartTimerEvent.svg`

### Passo 3: Colocar na pasta correta

| Tipo de Elemento | Pasta | Exemplos |
|-----------------|-------|----------|
| Tarefas | `tasks/` | user-task, service-task, manual-task |
| Eventos | `events/` | start-event, end-event, timer-event |
| Gateways | `gateways/` | exclusive-gateway, parallel-gateway |

### Passo 4: Verificar o mapeamento

Abra o arquivo [`icons.yaml`](icons.yaml) e verifique se o nome do arquivo está mapeado corretamente:

```yaml
tasks:
  user_task: "tasks/user-task.svg"  # ✅ Correto
```

---

## 🔄 Mapeamento Automático

O sistema identifica o tipo do elemento BPMN e aplica o ícone automaticamente:

### Como funciona

1. **Extração**: Sistema lê arquivo Markdown ou JSON com definição de processo
2. **Identificação**: Determina tipo do elemento (task, event, gateway)
3. **Resolução**: Consulta `icons.yaml` para encontrar o arquivo SVG
4. **Renderização**: Aplica o ícone no diagrama Miro

### Exemplo Prático

**Arquivo Markdown**:
```markdown
## Elementos do Processo

1. Preencher Formulário
   - Tipo: task
   - Ator: Funcionário
   - Metadata: task_type=user
```

**Mapeamento Automático**:
```
ProcessElement {
  type: "task",
  metadata: { task_type: "user" }
}
↓
Tipo BPMN: "user_task"
↓
icons.yaml: tasks.user_task = "tasks/user-task.svg"
↓
Ícone aplicado: /data/icons/tasks/user-task.svg
```

---

## 📊 Tipos de Elementos BPMN Suportados

### Tasks (Tarefas)

| Tipo | Arquivo | Descrição |
|------|---------|-----------|
| `task` | `tasks/task.svg` | Tarefa genérica (fallback) |
| `user_task` | `tasks/user-task.svg` | Tarefa realizada por pessoa |
| `service_task` | `tasks/service-task.svg` | Tarefa automatizada/serviço |
| `subprocess` | `tasks/subprocess.svg` | Subprocesso |

### Events - Início

| Tipo | Arquivo | Descrição |
|------|---------|-----------|
| `start_event` | `events/start-event.svg` | Início simples |
| `start_timer_event` | `events/start-timer-event.svg` | Início por timer |
| `start_message_event` | `events/start-message-event.svg` | Início por mensagem |
| `start_conditional_event` | `events/start-conditional-event.svg` | Início condicional |
| `start_error_event` | `events/start-error-event.svg` | Início por erro |
| `start_signal_event` | `events/start-signal-event.svg` | Início por sinal |
| `start_multiple_event` | `events/start-multiple-event.svg` | Início múltiplo |

### Events - Intermediários

| Tipo | Arquivo | Descrição |
|------|---------|-----------|
| `intermediate_timer_event` | `events/intermediate-timer-event.svg` | Timer intermediário |
| `intermediate_message_event` | `events/intermediate-message-event.svg` | Mensagem intermediária |
| `intermediate_conditional_event` | `events/intermediate-conditional-event.svg` | Condicional intermediário |
| `intermediate_signal_event` | `events/intermediate-signal-event.svg` | Sinal intermediário |
| `intermediate_compensation_event` | `events/intermediate-compensation-event.svg` | Compensação |
| `intermediate_multiple_event` | `events/intermediate-multiple-event.svg` | Múltiplo intermediário |
| `intermediate_link_catch_event` | `events/intermediate-link-catch-event.svg` | Link entrada |
| `intermediate_link_throw_event` | `events/intermediate-link-throw-event.svg` | Link saída |
| `intermediate_cancel_event` | `events/intermediate-cancel-event.svg` | Cancelamento |

### Events - Fim

| Tipo | Arquivo | Descrição |
|------|---------|-----------|
| `end_event` | `events/end-event.svg` | Fim simples |
| `end_message_event` | `events/end-message-event.svg` | Fim por mensagem |
| `end_signal_event` | `events/end-signal-event.svg` | Fim por sinal |
| `end_multiple_event` | `events/end-multiple-event.svg` | Fim múltiplo |

### Gateways (Decisões)

| Tipo | Arquivo | Descrição |
|------|---------|-----------|
| `exclusive_gateway` | `gateways/exclusive-gateway.svg` | XOR - Escolha exclusiva |
| `inclusive_gateway` | `gateways/inclusive-gateway.svg` | OR - Escolha inclusiva |
| `parallel_gateway` | `gateways/parallel-gateway.svg` | AND - Execução paralela |
| `event_based_gateway` | `gateways/event-based-gateway.svg` | Baseado em evento |

---

## ✅ Validação de Ícones

Após adicionar ou modificar ícones, execute a validação:

```bash
# Validar todos os ícones
python -m src.utils.validate_icons

# Validar apenas a estrutura do YAML
python -m src.utils.validate_icons --yaml-only

# Listar todos os ícones disponíveis
python -m src.utils.validate_icons --list

# Validar um ícone específico
python -m src.utils.validate_icons --file tasks/user-task.svg
```

### O que é validado

✅ **Estrutura**:
- Arquivo `icons.yaml` é YAML válido
- Todos os caminhos de arquivo estão corretos
- Não há entradas duplicadas

✅ **Arquivos SVG**:
- Arquivo existe e é legível
- É XML válido
- Contém tag `<svg>` raiz
- Tamanho < 5KB
- Possui `viewBox` (recomendado)

✅ **Mapeamento**:
- Todos os tipos BPMN têm ícone associado
- Não há ícones órfãos (sem referência)

---

## 🔧 Configuração Avançada

O arquivo [`icons.yaml`](icons.yaml) permite configurações avançadas:

### Tamanhos Customizados

```yaml
config:
  icon_sizes:
    task: 20      # Tamanho para ícones de tarefas
    event: 16     # Tamanho para ícones de eventos
    gateway: 18   # Tamanho para símbolos de gateways
```

### Posicionamento

```yaml
config:
  icon_position:
    task: "left"      # Ícone à esquerda do texto
    event: "inside"   # Ícone dentro do círculo
    gateway: "center" # Símbolo centralizado
```

### Estratégia de Fallback

```yaml
config:
  fallback_strategy: "emoji"  # Opções: "none", "emoji", "text", "default_icon"
```

### URL Base para Renderização no Miro

Configure a variável de ambiente `ICON_BASE_URL` no `.env`:

```env
ICON_BASE_URL=https://raw.githubusercontent.com/seu-usuario/seu-repo/main/data/icons
```

O sistema constrói a URL completa: `ICON_BASE_URL` + caminho relativo do ícone (ex: `tasks/user-task.svg`).

---

## 🎯 Boas Práticas

### ✅ DO (Faça)

- Use ícones simples e reconhecíveis
- Mantenha consistência visual entre ícones do mesmo tipo
- Otimize SVGs antes de adicionar (remova metadados desnecessários)
- Use `currentColor` para permitir tematização
- Documente ícones customizados

### ❌ DON'T (Não faça)

- Não use ícones muito detalhados (ficam ilegíveis em tamanho pequeno)
- Não misture estilos visuais diferentes
- Não use cores hardcoded (prefira `currentColor`)
- Não adicione arquivos muito grandes (> 5KB)
- Não use formatos diferentes de SVG

---

## 🔗 Integração com o Sistema

### Pipeline de Renderização

```
Markdown (.md)
    ↓
ProcessElement (type, metadata)
    ↓
IconResolver.get_icon_svg(bpmn_type)
    ↓
VisualElement (icon_svg + icon_relative_path in metadata)
    ↓
VisualToMiroConverter
    ↓ ICON_BASE_URL + icon_relative_path → URL pública
    ↓ miro_client.create_image(url=...) sobre o shape
Miro Board (shape + ícone SVG via URL)
```

### Arquivos Relacionados

| Arquivo | Responsabilidade |
|---------|-----------------|
| `src/models/icon_model.py` | Modelos de dados para ícones |
| `src/utils/icon_library.py` | Carregamento e resolução de ícones |
| `src/converters/process_to_visual.py` | Aplica ícones aos elementos visuais |
| `src/converters/visual_to_miro.py` | Renderiza ícones no Miro |
| `src/utils/validate_icons.py` | Validação de ícones |

---

## 📚 Recursos

### Bibliotecas de Ícones BPMN Gratuitas

- [BPMN.io Icons](https://github.com/bpmn-io/bpmn-font) - Oficial
- [Flaticon BPMN](https://www.flaticon.com/search?word=bpmn) - Coleção de ícones
- [Noun Project](https://thenounproject.com/) - Ícones genéricos
- [Feather Icons](https://feathericons.com/) - Ícones minimalistas (boa base)

### Ferramentas de Otimização

- [SVGOMG](https://jakearchibald.github.io/svgomg/) - Otimizador online
- [SVG Path Editor](https://yqnn.github.io/svg-path-editor/) - Editor visual
- [Inkscape](https://inkscape.org/) - Editor SVG completo

### Documentação BPMN

- [BPMN 2.0 Specification](https://www.omg.org/spec/BPMN/2.0/)
- [BPMN Quick Guide](https://www.bpmnquickguide.com/)

---

## 🆘 Troubleshooting

### Problema: Ícone não aparece no Miro

**Possíveis causas**:
1. Arquivo SVG não existe no caminho especificado
2. Nome do arquivo não corresponde ao mapeamento em `icons.yaml`
3. SVG inválido (XML malformado)
4. Tipo BPMN não mapeado corretamente

**Solução**:
```bash
# Verificar se arquivo existe
ls -lh data/icons/tasks/user-task.svg

# Validar mapeamento
python -m src.utils.validate_icons

# Testar SVG isoladamente
# Abrir no navegador ou editor SVG
```

### Problema: Ícone aparece distorcido

**Causa**: `viewBox` incorreto ou ausente

**Solução**:
```xml
<!-- Adicionar/corrigir viewBox -->
<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  ...
</svg>
```

### Problema: Cores não aparecem

**Causa**: Cores hardcoded no SVG

**Solução**:
```xml
<!-- ANTES -->
<path fill="#000000" .../>

<!-- DEPOIS -->
<path fill="currentColor" .../>
```

---

## 📞 Suporte

Para problemas ou dúvidas:

1. Verifique a documentação em [`CLAUDE.md`](../../CLAUDE.md)
2. Consulte o guia de uso em [`COMO_USAR.md`](../../COMO_USAR.md)
3. Execute validação: `python -m src.utils.validate_icons`

---

**Última atualização**: 2026-01-28
**Versão**: 2.0
**Autor**: Sistema Processos_Miro
