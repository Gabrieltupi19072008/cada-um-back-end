# CadaUm — Perfil expandido, candidatura direta, orientação e verificação de empresa

## Contexto

O dono do projeto (também síndico de todo o produto) levantou uma lista de melhorias depois
de observar cadastros de plataformas de vaga conhecidas (tipo Gupy) e de pensar no público-alvo
real do CadaUm — pessoas com TEA/PcD buscando o primeiro emprego, estágio ou vaga efetiva, e
empresas que precisam confiar nos dados que recebem. O objetivo é:

1. Deixar o currículo do candidato mais completo e mais parecido com o que empresas já esperam
   ver (escolaridade, cursos, experiência — que já existe), sem perder o que é específico do
   CadaUm (adaptações necessárias, tipo de vínculo desejado).
2. Dar ao candidato controle explícito sobre sua própria visibilidade (LGPD).
3. Permitir candidatura direta do candidato pra vaga, não só a empresa buscando candidato
   (fluxo hoje é unidirecional).
4. Ajudar quem está buscando o primeiro emprego (estágio/menor aprendiz) com conteúdo de
   orientação básica.
5. Dar mais confiança pro Admin ao aprovar uma empresa, comparando o que ela preencheu com o
   dado oficial da Receita Federal.

Um protótipo navegável ("Cada Um Talentos") foi revisado e aprovado pelo dono do projeto antes
deste documento — as decisões abaixo refletem esse protótipo.

## Fora de escopo (registrado, não decidido)

- **Aceitar só agências de emprego como empresa no início**: foi levantado como ideia, mas o
  dono do projeto não decidiu se quer isso. Não faz parte desta spec. Se decidir mais pra frente,
  vira uma spec própria (é uma regra de negócio, não um campo/tela).

## Candidato — Perfil expandido

Novos campos no cadastro/perfil do candidato (tabela `candidatos`, aba de dados pessoais no
front-end):

- **Tipo de vínculo desejado** — múltipla escolha: Efetivo (CLT), Estágio, Menor aprendiz.
  Guardar como lista (nova tabela `candidato_tipos_vinculo` com um enum `TipoVinculoEnum`, já
  que é N-pra-N conceitual: um candidato pode aceitar mais de um tipo). Reaproveita o
  `ContratoEnum` existente em `Vaga.py` não é ideal (tem `pj`/`temporario` que não fazem sentido
  aqui) — criar enum próprio `TipoVinculoEnum` (`efetivo`, `estagio`, `menor_aprendiz`).
- **Escolaridade ou grau de instrução** — campo simples (`Enum` ou `String`) direto em
  `Candidato`, não depende de ter uma `Formacao` cadastrada. Valores: Ensino médio incompleto,
  Ensino médio completo, Ensino superior incompleto, Ensino superior completo, Pós-graduação.
- **Cursos profissionalizantes** — `Text` livre em `Candidato` (não precisa de tabela própria,
  é texto corrido, diferente de `Formacao` que é estruturada).
- **O que preciso para trabalhar bem** — `Text` livre em `Candidato`. É essencialmente o campo
  `necessidades_especiais` que já existe, só que reapresentado com rótulo mais claro e amigável
  na tela — **reaproveitar a coluna existente**, só mudar o rótulo no front-end, sem migração.
- **Bairros que aceito trabalhar** — `String` livre em `Candidato` (texto livre, decisão já
  tomada com o usuário).

Todos os campos novos são opcionais (`nullable=True` / `Optional` no schema), seguindo o padrão
já usado nos outros campos do cadastro.

## Candidato — Privacidade (LGPD)

Novo campo `visivel_para_empresas: Boolean` em `Candidato`, **default `True`** (decisão tomada
com o usuário: visível por padrão, candidato desativa se quiser). Tela nova "Privacidade" no
painel do candidato com um toggle. A rota de busca de candidatos (`AbaBuscarCandidatos`,
back-end `rotas/empresas.py`) precisa filtrar por `visivel_para_empresas == True` — importante:
mesmo assim, o candidato deve continuar podendo se candidatar direto a vagas (visibilidade não
bloqueia candidatura, só a busca ativa da empresa).

## Candidato — Candidatura direta em vaga ("Enviar meu currículo")

Hoje o model `Interesse` já suporta `vaga_id` opcional e já liga `empresa_id` + `candidato_id`,
mas só a empresa cria esse registro. Precisa de:

- Nova rota `POST /candidatos/vagas/{vaga_id}/candidatar` (candidato autenticado) que cria um
  `Interesse` com `vaga_id` preenchido. Adicionar um campo `origem: Enum('empresa', 'candidato')`
  em `Interesse` pra diferenciar quem iniciou o contato (a tela de "Candidaturas recebidas" da
  empresa filtra por `origem == 'candidato'`; "Interesses enviados" mostra `origem == 'empresa'`).
- Impedir candidatura duplicada na mesma vaga (unique constraint ou checagem antes de criar).
- Front-end: botão "Enviar meu currículo" em `VagasDisponiveis.jsx`, com tela/modal de
  confirmação (ver protótipo).
- Nova aba "Candidaturas Recebidas" em `PainelEmpresa.jsx` / `paginas/empresa/`, separada de
  `AbaInteressesEnviados.jsx` — lista `Interesse` com `origem == 'candidato'`.

## Candidato — Orientação

Nova página `Orientacao.jsx`, com uma lista de conteúdos fixa no front-end (não precisa de
tabela no banco agora — é conteúdo editorial, não dado de usuário): título, categoria, descrição
curta, duração, link do YouTube. Por enquanto os links reais **não existem** — a lista vem com
os 6 tópicos do protótipo como placeholder, e o dono do projeto substitui os links depois
editando o array no código (sem precisar de painel admin pra isso, é baixo volume de conteúdo).
A aba aparece pro candidato que marcou "Estágio" ou "Menor aprendiz" no tipo de vínculo desejado.

## Empresa — Verificação de CNPJ na aprovação

No Painel Admin, tela de aprovação de empresa: buscar automaticamente os dados do CNPJ via
**BrasilAPI** (`https://brasilapi.com.br/api/cnpj/v1/{cnpj}`, gratuita, sem chave, dados públicos
da Receita) quando o Admin abre a tela de aprovação de uma empresa pendente. Mostrar lado a lado
com o que a empresa preencheu (razão social, situação cadastral, nome fantasia, data de abertura).
**Decisão tomada**: isso é só informativo — a aprovação continua sendo um clique manual do Admin,
sem bloqueio automático. Se a BrasilAPI falhar/CNPJ não for encontrado, mostrar aviso mas não
travar a aprovação manual.

## Notificação por e-mail

Quando uma empresa demonstra interesse num candidato (fluxo que já existe, `origem == 'empresa'`)
**e** quando uma empresa muda o status de uma candidatura recebida, o candidato recebe um e-mail.
Isso não existe hoje no projeto (o fluxo de "esqueci senha" comenta explicitamente que envio de
e-mail ainda não está configurado). Precisa de:

- Escolher um provedor com tier gratuito: **Resend** (3.000 e-mails/mês grátis, API simples,
  biblioteca Python oficial `resend`).
- Nova env var `RESEND_API_KEY` no back-end.
- Função utilitária `enviar_email(destinatario, assunto, corpo_html)` em `back-end/notificacoes.py`.
- Chamar essa função nos pontos relevantes de `rotas/empresas.py` (quando cria Interesse) e
  `rotas/candidatos.py` (quando responde a candidatura, se fizer sentido avisar a empresa também
  — a decidir na hora de implementar, não é bloqueante).
- Se `RESEND_API_KEY` não estiver configurada, a função deve logar e não quebrar o fluxo
  principal (nunca falhar uma ação do usuário por causa de e-mail).

## Testagem / verificação

- Back-end: testar manualmente cada rota nova via curl (candidatura, listagem de candidaturas
  recebidas, toggle de visibilidade, busca de CNPJ) contra o banco de desenvolvimento antes de
  subir pra produção — mesmo padrão já usado nas sessões anteriores deste projeto (sem suíte de
  testes automatizados configurada ainda).
- Front-end: rodar `npm run build` sem erros e testar manualmente os fluxos novos no navegador
  local (`npm run dev`) antes de publicar.
- Confirmar que candidatos/empresas já existentes no banco de produção não quebram com os campos
  novos (todos opcionais/com default, sem `NOT NULL` sem default).
