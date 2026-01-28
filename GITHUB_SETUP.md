# Setup do Repositório GitHub

## Passos para Configurar o ICON_BASE_URL

### Opção 1: Usando GitHub CLI (Recomendado)

Se você tiver o GitHub CLI instalado:

```bash
# 1. Instalar GitHub CLI (se necessário)
# macOS:
brew install gh

# 2. Autenticar
gh auth login

# 3. Criar repositório
gh repo create processos-miro --public --source=. --remote=origin --push

# 4. Obter seu username
GITHUB_USER=$(gh api user -q .login)

# 5. Atualizar .env
sed -i '' "s|SEU_USUARIO|$GITHUB_USER|g" .env
```

### Opção 2: Manual (Via GitHub.com)

1. **Criar Repositório no GitHub**
   - Acesse https://github.com/new
   - Nome: `processos-miro`
   - Visibilidade: **Public** (importante para raw.githubusercontent.com funcionar)
   - NÃO inicialize com README, .gitignore ou licença
   - Clique em "Create repository"

2. **Conectar Repositório Local**
   ```bash
   git remote add origin https://github.com/SEU_USUARIO/processos-miro.git
   git branch -M main
   git push -u origin main
   ```

3. **Atualizar .env**
   - Abra o arquivo `.env`
   - Substitua `SEU_USUARIO` pelo seu username do GitHub
   - A URL final será algo como:
     ```
     ICON_BASE_URL=https://raw.githubusercontent.com/seu-usuario-real/processos-miro/main/data/icons
     ```

### Opção 3: Repositório Privado + Token

Se preferir repositório privado, você precisará usar tokens de autenticação:

1. Crie um Personal Access Token em https://github.com/settings/tokens
2. Use a URL com token:
   ```
   ICON_BASE_URL=https://SEU_TOKEN@raw.githubusercontent.com/SEU_USUARIO/processos-miro/main/data/icons
   ```

**⚠️ Atenção**: Não commite o `.env` com token no repositório!

---

## Verificar Configuração

Após configurar, teste se os ícones estão acessíveis:

```bash
# Substitua pela sua URL real
curl -I https://raw.githubusercontent.com/SEU_USUARIO/processos-miro/main/data/icons/events/start-event.svg

# Deve retornar HTTP 200 OK
```

Ou rode os testes:

```bash
pytest tests/test_icon_library.py -v
```

---

## Estrutura dos Ícones no Repositório

Os ícones estão organizados em:

```
data/icons/
├── README.md
├── icons.yaml          # Configuração dos ícones
├── events/            # Eventos BPMN
│   ├── start-event.svg
│   ├── end-event.svg
│   └── ...
├── gateways/          # Gateways (decisões)
│   ├── exclusive-gateway.svg
│   ├── parallel-gateway.svg
│   └── ...
└── tasks/             # Tarefas e atividades
    ├── task.svg
    ├── user-task.svg
    └── ...
```

A biblioteca carrega automaticamente de `{ICON_BASE_URL}/icons.yaml` e resolve os caminhos SVG relativos.

---

## Troubleshooting

### Erro: "404 Not Found"
- Verifique se o repositório é **público**
- Confirme que o push foi feito com sucesso: `git log --oneline`
- Teste a URL diretamente no navegador

### Erro: "ICON_BASE_URL not configured"
- Verifique se a variável está definida no `.env`
- Rode: `python -c "from config.settings import get_settings; print(get_settings().icon_base_url)"`

### Ícones não aparecem no Miro
- Aguarde alguns minutos (cache do GitHub)
- Verifique se os SVGs são válidos: `xmllint --noout data/icons/events/*.svg`
- Confirme que o Miro consegue acessar URLs públicas

---

## Próximos Passos

Depois de configurar:

1. ✅ Verifique os testes: `pytest tests/test_icon_library.py -v`
2. ✅ Teste criação de elementos no Miro: `python -m src.main process data/input/exemplo.md`
3. ✅ Confirme que os ícones aparecem corretamente nos shapes

**Dica**: Mantenha este arquivo (`GITHUB_SETUP.md`) no repositório para referência futura!
