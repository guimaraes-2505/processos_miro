# SIPOC - {process_name}

**Codigo:** {process_id}
**Macroprocesso:** {macroprocess_name}
**Data de Criacao:** {created_at}

---

## Visao Geral

{description}

---

## Diagrama SIPOC

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  SUPPLIERS   │  │    INPUTS    │  │   PROCESS    │  │   OUTPUTS    │  │  CUSTOMERS   │
│ (Fornecedores)│  │  (Entradas)  │  │  (Processo)  │  │   (Saidas)   │  │  (Clientes)  │
├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤
{sipoc_diagram}
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

---

## Detalhamento

### Suppliers (Fornecedores)

Quem fornece os insumos necessarios para o processo.

| Fornecedor | Tipo | Descricao |
|------------|------|-----------|
{suppliers_table}

---

### Inputs (Entradas)

O que e necessario para iniciar o processo.

| Entrada | Fornecedor | Descricao |
|---------|------------|-----------|
{inputs_table}

---

### Process (Processo)

Passos principais do processo (visao macro).

| No. | Etapa | Descricao |
|-----|-------|-----------|
{process_steps_table}

---

### Outputs (Saidas)

Entregas geradas pelo processo.

| Saida | Cliente | Descricao |
|-------|---------|-----------|
{outputs_table}

---

### Customers (Clientes)

Quem recebe as entregas do processo.

| Cliente | Tipo | Descricao |
|---------|------|-----------|
{customers_table}

---

## Processos Relacionados

| Codigo | Nome | Relacao |
|--------|------|---------|
{related_processes_table}

---

## Links

- **Miro (Diagrama):** {miro_board_url}
- **POP:** {pop_reference}

---

**Elaborado por:** {author}
**Data:** {created_at}
