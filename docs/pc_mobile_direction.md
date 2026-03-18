# Direcao PC + Mobile

## Decisao oficial

O projeto passa a seguir a arquitetura **PC + Mobile**:

- **Desktop (PC)** continua como interface principal.
- **Mobile** sera um cliente separado, focado somente em lancamento de valores.
- A UI atual do desktop nao sera redesenhada nesta etapa.
- O mobile consumira a mesma sessao central por meio de um backend HTTP leve.

## Como fica a arquitetura

### Desktop

- Continua em `PySide6`, com o `MainWindow` atual preservado.
- Segue responsavel por estrutura, digitacao de apostas, flags, conferencia, resultado e financeiro.
- Passa a sincronizar a sessao ativa em `runtime/active_session.json`.

### Backend mobile

- Novo backend HTTP em `services/mobile_api.py`.
- Le o estado ativo do projeto e expõe endpoints JSON para:
  - sessao ativa
  - blocos
  - paginas
  - valores por linha
  - preencher pagina
- Reaproveita as mesmas regras de dominio do desktop via `BancaController`.

### Cliente mobile

- Sera uma interface web separada e vertical.
- Vai consumir a API mobile, sem reaproveitar o layout de 3 colunas do desktop.
- O foco sera bloco, pagina, aposta, valor, pendencia e progresso.

## Sessao compartilhada

Para a primeira etapa, a base central da convivencia PC + Mobile passa a ser:

- `runtime/active_session.json`

Essa sessao ativa:

- e restaurada automaticamente pelo desktop quando existir;
- e atualizada pelo desktop a cada mudanca relevante de estado;
- sera a fonte de verdade da primeira versao do backend mobile.

Isso preserva a UI do PC e cria a fundacao para o cliente mobile sem exigir banco ou migracao grande agora.

## Etapa 1 implementada

### O que entrou agora

- sincronizacao de sessao ativa no desktop;
- backend HTTP inicial para mobile;
- servico de leitura e escrita focado em valores;
- payloads de bloco, pagina, progresso e placeholder fantasma;
- testes cobrindo sessao ativa, servico mobile e API HTTP.

### O que ainda fica para as proximas etapas

- UI web mobile;
- fluxo visual de bloco -> pagina -> valores;
- acao "preencher pagina" na tela mobile;
- locks de concorrencia em tempo real entre clientes;
- feedback visual completo de pendencia e pagina em uso.

## Partes do projeto que precisaram mudar

- `services/controller.py`
  - sincroniza e restaura a sessao ativa sem alterar a UI desktop.
- `storage/active_session_store.py`
  - persiste o estado vivo compartilhado.
- `app_state/projections.py`
  - centraliza o placeholder fantasma para reuso entre desktop e mobile.
- `services/mobile_service.py`
  - monta os dados operacionais do mobile e aplica alteracoes de valor.
- `services/mobile_api.py`
  - expõe o backend HTTP para o cliente mobile.
- `mobile_api.py`
  - ponto de entrada para subir a API.
- `tests/test_mobile_backend.py`
  - cobre a fundacao PC + Mobile da Etapa 1.

## Endpoints da Etapa 1

- `GET /health`
- `GET /api/mobile/session`
- `GET /api/mobile/blocks/<block_id>/pages`
- `GET /api/mobile/pages/<page_id>`
- `POST /api/mobile/lines/<line_id>/value`
- `POST /api/mobile/pages/<page_id>/fill`

## Operacao recomendada agora

1. Abrir ou criar a sessao no desktop.
2. Deixar o desktop seguir como fluxo principal.
3. Subir o backend mobile com `python mobile_api.py`.
4. Na proxima etapa, ligar uma UI mobile web a esses endpoints.
