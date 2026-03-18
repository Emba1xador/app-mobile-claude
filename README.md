# BANCA APP 2.0

Aplicacao desktop em Python + PySide6 para digitacao rapida de apostas, conferencia reativa, controle financeiro por bloco e integracao com WhatsApp.

## Direcao atual

O projeto agora segue a arquitetura **PC + Mobile**:

- o desktop continua como interface principal;
- o mobile sera um cliente separado, focado somente em lancamento de valores;
- a sessao viva compartilhada fica em `runtime/active_session.json`;
- a primeira base do backend mobile esta documentada em `docs/pc_mobile_direction.md`.

## Requisitos

- Windows com Python 3.11+
- `pip`

## Executar

Opcao 1, instalacao automatica:

```bat
setup_venv.bat
run.bat
```

Opcao 2, manual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Backend e UI mobile

Para subir o backend HTTP com a UI web mobile:

```powershell
python mobile_api.py --host 0.0.0.0 --port 8765
```

Endpoints disponiveis:

- `GET /health`
- `GET /api/mobile/session`
- `GET /api/mobile/blocks/<block_id>/pages`
- `GET /api/mobile/pages/<page_id>`
- `POST /api/mobile/lines/<line_id>/value`
- `POST /api/mobile/pages/<page_id>/fill`

Rotas web mobile:

- `/mobile`
- `/mobile/blocks`
- `/mobile/block/<block_id>/pages`
- `/mobile/page/<page_id>`

Fluxo mobile entregue:

- sessao ativa;
- lista de blocos;
- lista de paginas;
- tela de valores com placeholder fantasma;
- botao `OK` por linha;
- modal de `Preencher pagina`.

## Estrutura

- `core/`: parser, validacoes, conferencia, financeiro, resumo e regras.
- `app_state/`: estado persistente e projecoes achatadas para a tabela principal.
- `services/`: controlador principal, formatacao e WhatsApp.
- `storage/`: serializacao JSON e persistencia do mapa de WhatsApp.
- `ui/`: janela principal, modelos Qt, delegates, dialogs e widgets.
- `tests/`: testes unitarios do core e da persistencia.

## Atalhos principais

- `B`: criar novo bloco.
- `Enter`: validar entrada e descer.
- `Shift`: converter `M` para `MC` ou confirmar 4 digitos como `MC`.
- `-` numpad: alternar `I.V`.
- `+` numpad: alternar `DE`.
- `*` numpad: alternar `DEM`.
- `,` numpad na coluna de aposta: criar nova pagina.
- `F9`: inserir resultado.
- `Shift + seta`: selecao multipla da tabela.

## Salvar e abrir

- `Salvar`: gera arquivo em `saves/banca_save_YYYYMMDD_HHMMSS.json`.
- `Abrir`: restaura blocos, paginas, linhas, valores, flags, resultado, dinheiro, porcentagem, WhatsApp e estado basico da janela.
- O mapa de WhatsApp tambem e salvo em `banca_whatsapp_map.json`.

## Fluxo recomendado

1. Pressione `B` e informe o numero do bloco.
2. Digite as apostas na coluna `Cambistas`.
3. Depois preencha os valores na coluna `Valor`.
4. Use `F9` para inserir o resultado.
5. Confira resumo, financeiro e envie o resumo do bloco via WhatsApp na coluna financeira.

## Testes

```powershell
python -m pytest
```
