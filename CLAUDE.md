# CLAUDE.md — Conferix / Banca APP

> Este arquivo é lido automaticamente pelo Claude Code a cada sessão.
> Ele define o contexto permanente do projeto para que o assistente opere com precisão máxima.

---

## 🧭 O que é este sistema

**Conferix** (também chamado de **Banca APP**) é um aplicativo desktop operacional focado em:

- Lançamento rápido de apostas por bloco e por página
- Conferência de resultados do sorteio
- Identificação de apostas premiadas
- Controle financeiro por bloco
- Fechamento de horário/sessão
- Observações operacionais
- Integração com interface mobile para lançamento de valores

O foco principal é: **velocidade operacional + clareza visual + confiabilidade de uso.**

---

## 🛠️ Stack técnica

| Camada | Tecnologia |
|--------|-----------|
| Desktop | Python + PyQt5 |
| Backend/API | Flask |
| Mobile/Web | HTML + JS (interface web separada) |
| Sincronização | API REST entre mobile e desktop |

---

## 🗂️ Arquitetura de arquivos principais

```
├── core/
│   └── entities.py         # Entidades: BetLine, Page, Block, ResultPrize, ProjectionRow
├── ui/
│   ├── main_window.py      # Janela principal (~1033 linhas) — NÃO quebrar
│   └── views/
│       └── bets_table_view.py  # Coluna de lançamentos — área mais crítica
├── services/
│   └── controller.py       # Controlador central
├── mobile_api.py           # API Flask para sincronização mobile
└── mobile_web/             # Interface web/mobile
```

---

## 🖥️ Layout da interface desktop

A interface é organizada em **3 colunas fixas**:

### Coluna Esquerda — Lançamentos ⚡ (MAIS CRÍTICA)
- Blocos, páginas, apostas
- Linha de ação para nova aposta
- Área de maior velocidade de operação

### Coluna Central — Resultado / Resumo / Pendências
- Resultados dos 5 prêmios
- Resumo da sessão
- Blocos premiados
- Pendências do horário

### Coluna Direita — Financeiro
- Situação financeira por bloco
- Dinheiro recebido / Bruto / Líquido (70%) / Saldo
- Resumo financeiro
- Observações

---

## 📐 Modelo de dados

```
Sessão/Horário
└── Bloco (conjunto de apostas de um cliente)
    └── Página (subdivisão do bloco)
        └── Aposta (linha individual — BetLine)

Resultado → comparado com apostas → gera Premiados e Pendências

Bloco → possui dados financeiros próprios:
  - dinheiro recebido
  - bruto
  - líquido/repasse (70%)
  - saldo
  - contato/WhatsApp
```

---

## 📱 Contexto mobile

- O desktop é a interface **principal**
- O mobile é cliente operacional para **lançamento de valores**
- Alterações no mobile devem refletir no desktop via sync
- A API Flask (`mobile_api.py`) gerencia essa comunicação

---

## ⚡ Filosofia de desenvolvimento

### PRIORIDADES (em ordem):
1. **Velocidade operacional** — poucos cliques, foco automático
2. **Clareza visual** — leitura instantânea do que importa
3. **Confiabilidade** — nunca quebrar o fluxo principal
4. **Estética** — moderna e sóbria, nunca no lugar da funcionalidade

### SEMPRE fazer:
- Navegação rápida por teclado
- Foco automático na próxima ação
- Hierarquia visual clara entre: bloco / página / aposta / ação / premiado / pendência
- Densidade útil alta (informação sem poluição)

### NUNCA fazer:
- Quebrar o fluxo principal do desktop
- Adicionar elementos visuais desnecessários
- Tornar a interface bonita porém lenta
- Encher de caixas dentro de caixas
- Remover comportamento existente sem substituição equivalente

---

## 🎨 Direção visual

**A interface DEVE parecer:**
- Operação profissional e moderna
- Rápida, clara, hierárquica
- Densa mas legível
- Sóbria (não colorida demais)

**A interface NÃO DEVE parecer:**
- Sistema antigo com grades pesadas
- Software confuso ou prototipado
- Painel genérico de dashboard

---

## 🤖 Como o Claude deve atuar neste projeto

### Papel esperado:
Parceiro técnico de desenvolvimento e design funcional — não apenas executor de código.

### Ao propor mudanças, sempre avaliar:
- ✅ Impacto na **velocidade operacional**
- ✅ Impacto na **clareza visual**
- ✅ Impacto no **fluxo de trabalho**
- ✅ Risco de **quebrar comportamento existente**

### Postura:
- Entender o sistema como produto real de trabalho
- Propor soluções práticas, não genéricas
- Preservar o que já funciona
- Melhorar UX/UI com foco em uso real
- Quando houver dúvida entre "mais bonito" e "mais rápido": **escolher mais rápido**

---

## 📋 Status do projeto

- [x] App desktop funcional (PyQt5)
- [x] Layout 3 colunas implementado
- [x] Sistema blocos/páginas/apostas operacional
- [x] Resultado dos sorteios
- [x] Resumo e pendências
- [x] Financeiro por bloco
- [x] Barra superior e inferior
- [x] Interface mobile/web separada
- [x] Sincronização mobile ↔ desktop
- [ ] Ajustes finos de UX em andamento
- [ ] Refinamentos estruturais em andamento

---

## 🔑 Regras rápidas para o Claude

```
1. main_window.py é o núcleo — alterações aqui exigem cuidado máximo
2. bets_table_view.py é a área mais crítica de UX — velocidade acima de tudo
3. Toda mudança visual deve manter ou melhorar a legibilidade
4. Sincronização mobile/desktop passa pela mobile_api.py — não contornar
5. O usuário chama o sistema de "Conferix" ou "Banca APP" — ambos são o mesmo projeto
```
