# Perfil Expandido, Candidatura Direta e LGPD — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the candidate profile (job-type preference, education, courses, workplace needs, neighborhoods), add LGPD visibility control, let candidates apply directly to jobs, add an orientation/content hub, add CNPJ verification for admin company approval, and send email notifications — as approved in the design doc and interactive prototype.

**Architecture:** Two independent git repos (`back-end/` FastAPI+SQLAlchemy+Postgres/Supabase, `front-end/` React+Vite) already in production (Render + Vercel + Supabase). No Alembic — schema changes ship as a one-off idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` script, matching the project's existing `criar_tabelas.py` convention. No automated test suite exists yet — every task is verified manually (curl for back-end, browser for front-end), matching how this project has been verified throughout its history. New multi-value fields (`tipos_vinculo`, future-proofing) are stored as simple comma-separated `String` columns rather than a new join table or Postgres-native enum type, to avoid schema/type-creation complexity in a raw-SQL migration — this is a deliberate simplification from the design doc's join-table suggestion, justified by the small, fixed value set (3 options) and this codebase's existing preference for plain columns over relational complexity.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic 2, Postgres (Supabase), React 19, Vite, axios, react-router-dom, `requests` (new, for BrasilAPI), `resend` (new, for email).

## Global Constraints

- All Portuguese identifiers/copy, matching 100% of the existing codebase (`candidatos`, `visivel_para_empresas`, etc.) — never introduce English field/route names.
- Every new DB column must be nullable or have a default — production already has real user rows (candidato "Gabriel Tupinambá", plus test admin accounts) that must not break.
- No automated test framework in this repo. Each task's "test" step is a manual `curl` command (back-end) or a manual browser check (front-end) with the exact expected output — do not invent a pytest suite.
- Follow the existing generic-update pattern: `PUT /candidatos/me` and `PUT /empresas/me` already loop over `model_dump(exclude_unset=True)` and `setattr` — reuse it for any field that's a plain scalar column; only add a dedicated route when the action isn't a simple field update (e.g., applying to a job).
- Reuse `_obter_candidato_do_usuario` / `_obter_empresa_do_usuario` / `exigir_candidato` / `exigir_empresa` / `exigir_admin` from `dependencias.py` — never re-implement auth/lookup logic.
- Migration script must be idempotent (`ADD COLUMN IF NOT EXISTS`) since it may be run more than once against the same Supabase database.
- Commit after each task, one commit per task, following this repo's existing commit message style (imperative Portuguese, `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` trailer).

---

## Phase A — Candidato: perfil expandido

### Task 1: Migração de colunas (candidatos + interesses)

**Files:**
- Create: `back-end/migrar_perfil_v2.py`

**Interfaces:**
- Produces: columns `candidatos.escolaridade` (VARCHAR 50, nullable), `candidatos.cursos_profissionalizantes` (TEXT, nullable), `candidatos.bairros_aceitos` (VARCHAR 255, nullable), `candidatos.tipos_vinculo` (VARCHAR 60, nullable, CSV of `efetivo`/`estagio`/`menor_aprendiz`), `candidatos.visivel_para_empresas` (BOOLEAN NOT NULL DEFAULT TRUE), `interesses.origem` (VARCHAR 20 NOT NULL DEFAULT `'empresa'`, values `empresa`/`candidato`).

- [ ] **Step 1: Write the migration script**

```python
# migrar_perfil_v2.py - Adiciona colunas do perfil expandido, privacidade e origem do interesse.
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez (IF NOT EXISTS).
# Uso: python migrar_perfil_v2.py

from banco import engine
from sqlalchemy import text

COMANDOS = [
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS escolaridade VARCHAR(50)",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS cursos_profissionalizantes TEXT",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS bairros_aceitos VARCHAR(255)",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS tipos_vinculo VARCHAR(60)",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS visivel_para_empresas BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE interesses ADD COLUMN IF NOT EXISTS origem VARCHAR(20) NOT NULL DEFAULT 'empresa'",
]

with engine.connect() as conexao:
    for comando in COMANDOS:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK:", comando)

print("Migração concluída.")
```

- [ ] **Step 2: Run it against the local `.env` database (Supabase dev connection already configured from earlier sessions)**

Run: `python migrar_perfil_v2.py`
Expected: six `OK: ...` lines followed by `Migração concluída.`, no errors.

- [ ] **Step 3: Verify the columns exist**

Run:
```bash
python -c "
from banco import engine
from sqlalchemy import text
with engine.connect() as c:
    r = c.execute(text(\"select column_name from information_schema.columns where table_name='candidatos' and column_name in ('escolaridade','cursos_profissionalizantes','bairros_aceitos','tipos_vinculo','visivel_para_empresas')\"))
    print(sorted(row[0] for row in r))
    r2 = c.execute(text(\"select column_name from information_schema.columns where table_name='interesses' and column_name='origem'\"))
    print([row[0] for row in r2])
"
```
Expected: first line lists all 5 candidato column names; second line prints `['origem']`.

- [ ] **Step 4: Commit**

```bash
git add migrar_perfil_v2.py
git commit -m "$(cat <<'EOF'
Adiciona script de migracao pro perfil expandido e origem do interesse

Coluna nova em candidatos (escolaridade, cursos, bairros, tipos de
vinculo, visibilidade) e em interesses (origem: empresa ou candidato).
Idempotente (IF NOT EXISTS) porque roda direto contra o Supabase, sem
Alembic.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Model `Candidato` — novos atributos

**Files:**
- Modify: `back-end/Candidato.py`

**Interfaces:**
- Consumes: none.
- Produces: `Candidato.escolaridade: str | None`, `Candidato.cursos_profissionalizantes: str | None`, `Candidato.bairros_aceitos: str | None`, `Candidato.tipos_vinculo: str | None`, `Candidato.visivel_para_empresas: bool`.

- [ ] **Step 1: Add the columns to the model**

In `back-end/Candidato.py`, change the imports line and add the five columns after `necessidades_especiais`:

```python
from sqlalchemy import Column, Integer, String, Boolean, Text, Date, Enum, ForeignKey, TIMESTAMP
```

(unchanged — already imports everything needed)

Insert after the `necessidades_especiais = Column(Text)` line:

```python
    escolaridade = Column(String(50))
    cursos_profissionalizantes = Column(Text)
    bairros_aceitos = Column(String(255))
    tipos_vinculo = Column(String(60))  # CSV: combinação de efetivo, estagio, menor_aprendiz
    visivel_para_empresas = Column(Boolean, default=True, nullable=False)
```

- [ ] **Step 2: Verify the app still imports cleanly**

Run: `python -c "import main; print('OK')"`
Expected: `OK` printed, no traceback.

- [ ] **Step 3: Verify a fresh query returns the new attributes**

Run:
```bash
python -c "
from banco import SessaoLocal
import Usuario, Candidato as CandidatoMod, Empresa, Formacao, Experiencia, Habilidade, Vaga, Interesses
s = SessaoLocal()
c = s.query(CandidatoMod.Candidato).first()
print(c.visivel_para_empresas, c.escolaridade, c.tipos_vinculo)
s.close()
"
```
Expected: prints `True None None` (existing rows get the boolean default, other new columns are `None`).

- [ ] **Step 4: Commit**

```bash
git add Candidato.py
git commit -m "$(cat <<'EOF'
Adiciona campos novos ao model Candidato

escolaridade, cursos_profissionalizantes, bairros_aceitos,
tipos_vinculo (CSV) e visivel_para_empresas (default True).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Model `Interesse` — campo `origem`

**Files:**
- Modify: `back-end/Interesses.py`

**Interfaces:**
- Produces: `Interesse.origem: str` (default `"empresa"`), values used elsewhere: `"empresa"`, `"candidato"`.

- [ ] **Step 1: Add the column**

In `back-end/Interesses.py`, insert after `status = Column(Enum(StatusInteresseEnum), default=StatusInteresseEnum.pendente)`:

```python
    origem = Column(String(20), default="empresa", nullable=False)  # "empresa" ou "candidato"
```

Add `String` to the import line at the top:

```python
from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, TIMESTAMP
```

- [ ] **Step 2: Verify import**

Run: `python -c "import main; print('OK')"`
Expected: `OK`, no traceback.

- [ ] **Step 3: Commit**

```bash
git add Interesses.py
git commit -m "$(cat <<'EOF'
Adiciona campo origem ao model Interesse

Diferencia interesse iniciado pela empresa (busca de candidato) de
candidatura iniciada pelo candidato (enviar curriculo numa vaga).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Schemas — perfil expandido e privacidade

**Files:**
- Modify: `back-end/schemas.py`

**Interfaces:**
- Consumes: none new.
- Produces: `CandidatoAtualizar` gains `escolaridade`, `cursos_profissionalizantes`, `bairros_aceitos`, `tipos_vinculo`, `visivel_para_empresas` (all `Optional`). `CandidatoPerfil` and `CandidatoPublico` gain the same fields (read-only, for responses). `CandidatoAdmin` gains `visivel_para_empresas`.

- [ ] **Step 1: Add `Literal` to the typing import**

At the top of `back-end/schemas.py`, change:

```python
from typing import Optional
```

to:

```python
from typing import Optional, Literal
```

- [ ] **Step 2: Extend `CandidatoAtualizar`**

Replace the `CandidatoAtualizar` class body:

```python
class CandidatoAtualizar(BaseModel):
    data_nascimento: Optional[date] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(default=None, max_length=2)
    telefone: Optional[str] = None
    linkedin: Optional[str] = None
    sobre_mim: Optional[str] = None
    grau_tea: Optional[GrauTeaEnum] = None
    necessidades_especiais: Optional[str] = None
    foto_url: Optional[str] = None
    escolaridade: Optional[
        Literal[
            "fundamental_incompleto",
            "fundamental_completo",
            "medio_incompleto",
            "medio_completo",
            "superior_incompleto",
            "superior_completo",
            "pos_graduacao",
        ]
    ] = None
    cursos_profissionalizantes: Optional[str] = None
    bairros_aceitos: Optional[str] = None
    tipos_vinculo: Optional[str] = None
    visivel_para_empresas: Optional[bool] = None
```

- [ ] **Step 3: Extend `CandidatoPerfil`, `CandidatoPublico` and `CandidatoAdmin`**

In `CandidatoPerfil`, add after `foto_url: Optional[str] = None`:

```python
    escolaridade: Optional[str] = None
    cursos_profissionalizantes: Optional[str] = None
    bairros_aceitos: Optional[str] = None
    tipos_vinculo: Optional[str] = None
    visivel_para_empresas: bool = True
```

In `CandidatoPublico`, add the same five lines after its `foto_url: Optional[str] = None`.

In `CandidatoAdmin`, add after `grau_tea: Optional[GrauTeaEnum] = None`:

```python
    visivel_para_empresas: bool = True
```

- [ ] **Step 4: Verify import**

Run: `python -c "import main; print('OK')"`
Expected: `OK`, no traceback.

- [ ] **Step 5: Commit**

```bash
git add schemas.py
git commit -m "$(cat <<'EOF'
Adiciona campos novos aos schemas de Candidato

CandidatoAtualizar/Perfil/Publico/Admin ganham escolaridade, cursos
profissionalizantes, bairros aceitos, tipos de vinculo e visibilidade.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Filtrar busca de empresa por visibilidade

**Files:**
- Modify: `back-end/rotas/empresas.py:145`

**Interfaces:**
- Consumes: `Candidato.visivel_para_empresas` (Task 2).
- Produces: no new interface — behavior change only.

- [ ] **Step 1: Add the filter**

In `buscar_candidatos` (line 145), change:

```python
    consulta = sessao.query(Candidato).filter(Candidato.aprovado.is_(True))
```

to:

```python
    consulta = sessao.query(Candidato).filter(
        Candidato.aprovado.is_(True), Candidato.visivel_para_empresas.is_(True)
    )
```

Also apply the same filter in `obter_candidato` (line ~169-173): change

```python
    candidato = (
        sessao.query(Candidato)
        .filter(Candidato.id == candidato_id, Candidato.aprovado.is_(True))
        .first()
    )
```

to:

```python
    candidato = (
        sessao.query(Candidato)
        .filter(
            Candidato.id == candidato_id,
            Candidato.aprovado.is_(True),
            Candidato.visivel_para_empresas.is_(True),
        )
        .first()
    )
```

- [ ] **Step 2: Test manually — toggle visibility and confirm the search hides/shows the candidate**

Run (against local `.env` DB, using the real candidato account created earlier this project — replace email if different):
```bash
python -c "
from banco import SessaoLocal
import Usuario as UsuarioMod, Candidato as CandidatoMod, Empresa, Formacao, Experiencia, Habilidade, Vaga, Interesses
s = SessaoLocal()
c = s.query(CandidatoMod.Candidato).join(UsuarioMod.Usuario).filter(UsuarioMod.Usuario.email == 'gabrieltupi19072008@gmail.com').first()
c.aprovado = True
c.visivel_para_empresas = False
s.commit()
print('candidato oculto')
s.close()
"
```
Then start `python -m uvicorn main:app --port 8123` in the background, log in as an approved empresa (or the admin test account with a company you approve), and hit `GET /empresas/candidatos` with a valid empresa Bearer token — expect the candidate to be **absent**. Then flip `visivel_para_empresas` back to `True` the same way and confirm it reappears. Stop the local server afterward.

- [ ] **Step 3: Commit**

```bash
git add rotas/empresas.py
git commit -m "$(cat <<'EOF'
Filtra busca de candidatos por visivel_para_empresas

Candidato que desativou a visibilidade some da busca e da tela de
candidato individual, mas continua podendo se candidatar direto (isso
nao passa por essas rotas).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Front-end — campos novos em "Dados Pessoais" e relabel do TEA

**Files:**
- Modify: `front-end/src/paginas/curriculo/AbaDadosPessoais.jsx`
- Modify: `front-end/src/paginas/curriculo/AbaTea.jsx`

**Interfaces:**
- Consumes: `PUT /candidatos/me` (existing route, now accepts the 5 new optional fields from Task 4).

- [ ] **Step 1: Extend `AbaDadosPessoais.jsx` state and form**

Replace the `useState` block:

```jsx
  const [dados, setDados] = useState({
    data_nascimento: perfil.data_nascimento || '',
    cidade: perfil.cidade || '',
    estado: perfil.estado || '',
    telefone: perfil.telefone || '',
    linkedin: perfil.linkedin || '',
    sobre_mim: perfil.sobre_mim || '',
    escolaridade: perfil.escolaridade || '',
    cursos_profissionalizantes: perfil.cursos_profissionalizantes || '',
    bairros_aceitos: perfil.bairros_aceitos || '',
    tipos_vinculo: perfil.tipos_vinculo ? perfil.tipos_vinculo.split(',') : [],
  })
```

Add a helper right below the `atualizar` function:

```jsx
  function alternarTipoVinculo(tipo) {
    setDados((atual) => {
      const jaTem = atual.tipos_vinculo.includes(tipo)
      const novos = jaTem ? atual.tipos_vinculo.filter((t) => t !== tipo) : [...atual.tipos_vinculo, tipo]
      return { ...atual, tipos_vinculo: novos }
    })
    setSucesso(false)
  }
```

Change `salvar` to join the array back into CSV before sending:

```jsx
  async function salvar() {
    setSalvando(true)
    try {
      await cliente.put('/candidatos/me', { ...dados, tipos_vinculo: dados.tipos_vinculo.join(',') })
      setSucesso(true)
      aoSalvar()
    } finally {
      setSalvando(false)
    }
  }
```

Add the new form fields right before the closing `<Botao icone={Save} ...>` block (after the "Sobre mim" `<label className="campo">`):

```jsx
      <div className="campo">
        Interesse em
        <div className="checks">
          <label className="check-pill">
            <input
              type="checkbox"
              checked={dados.tipos_vinculo.includes('efetivo')}
              onChange={() => alternarTipoVinculo('efetivo')}
            />
            Efetivo (CLT)
          </label>
          <label className="check-pill">
            <input
              type="checkbox"
              checked={dados.tipos_vinculo.includes('estagio')}
              onChange={() => alternarTipoVinculo('estagio')}
            />
            Estágio
          </label>
          <label className="check-pill">
            <input
              type="checkbox"
              checked={dados.tipos_vinculo.includes('menor_aprendiz')}
              onChange={() => alternarTipoVinculo('menor_aprendiz')}
            />
            Menor aprendiz
          </label>
        </div>
      </div>
      <label className="campo">
        Escolaridade ou grau de instrução
        <select
          value={dados.escolaridade}
          onChange={(e) => atualizar('escolaridade', e.target.value)}
        >
          <option value="">Selecione</option>
          <option value="fundamental_incompleto">Ensino fundamental incompleto</option>
          <option value="fundamental_completo">Ensino fundamental completo</option>
          <option value="medio_incompleto">Ensino médio incompleto</option>
          <option value="medio_completo">Ensino médio completo</option>
          <option value="superior_incompleto">Ensino superior incompleto</option>
          <option value="superior_completo">Ensino superior completo</option>
          <option value="pos_graduacao">Pós-graduação</option>
        </select>
      </label>
      <label className="campo">
        Cursos profissionalizantes
        <textarea
          value={dados.cursos_profissionalizantes}
          onChange={(e) => atualizar('cursos_profissionalizantes', e.target.value)}
          placeholder="Ex: Auxiliar administrativo (SENAI, 2024), Informática básica (2023)"
        />
      </label>
      <label className="campo">
        Bairros que aceito trabalhar
        <input
          value={dados.bairros_aceitos}
          onChange={(e) => atualizar('bairros_aceitos', e.target.value)}
          placeholder="Ex: Progresso, Velha Central, Centro"
        />
        <span className="campo-dica">Texto livre — escreva os bairros que ficam bons pra você se deslocar.</span>
      </label>
```

Add the CSS for `.checks` and `.check-pill` (reused from the prototype) to `front-end/src/App.css`, right after the existing `.seletor-tipo button.ativo { ... }` block:

```css
.checks {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 2px;
}

.check-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 14px;
  border: 1px solid var(--borda-sutil);
  border-radius: 8px;
  font-weight: 500;
  font-size: 13.5px;
  color: var(--texto);
  cursor: pointer;
  user-select: none;
}

.check-pill input {
  accent-color: var(--acento);
  width: 15px;
  height: 15px;
}
```

- [ ] **Step 2: Relabel the TEA tab's textarea**

In `front-end/src/paginas/curriculo/AbaTea.jsx`, change:

```jsx
      <label className="campo">
        Necessidades especiais / adaptações que você precisa
```

to:

```jsx
      <label className="campo">
        O que preciso para trabalhar bem
```

- [ ] **Step 3: Build and manually verify**

Run: `npm run build` (inside `front-end/`)
Expected: build succeeds with no errors.

Then `npm run dev`, log in as the real candidato account, go to "Meu Currículo" → "Dados Pessoais", check a couple of the new checkboxes, fill escolaridade/cursos/bairros, click "Salvar rascunho", reload the page and confirm the values persisted (checkboxes still checked, fields still filled). Also open the "TEA & Necessidades" tab and confirm the label now reads "O que preciso para trabalhar bem".

- [ ] **Step 4: Commit**

```bash
git add src/paginas/curriculo/AbaDadosPessoais.jsx src/paginas/curriculo/AbaTea.jsx src/App.css
git commit -m "$(cat <<'EOF'
Adiciona campos novos ao formulario de dados pessoais do candidato

Tipo de vinculo desejado, escolaridade, cursos profissionalizantes e
bairros aceitos. Rotula o campo de necessidades especiais como "O que
preciso para trabalhar bem".

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase B — Privacidade (LGPD)

### Task 7: Front-end — tela de Privacidade

**Files:**
- Create: `front-end/src/paginas/Privacidade.jsx`
- Modify: `front-end/src/App.jsx`
- Modify: `front-end/src/paginas/PainelCandidato.jsx`

**Interfaces:**
- Consumes: `GET /candidatos/me` (existing), `PUT /candidatos/me` (existing, now accepts `visivel_para_empresas`).

- [ ] **Step 1: Create the page**

```jsx
// front-end/src/paginas/Privacidade.jsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ShieldCheck } from 'lucide-react'
import Layout from '../componentes/Layout'
import Cartao from '../componentes/Cartao'
import Botao from '../componentes/Botao'
import Aviso from '../componentes/Aviso'
import cliente from '../api/cliente'

export default function Privacidade() {
  const [perfil, setPerfil] = useState(null)
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)
  const navegar = useNavigate()

  useEffect(() => {
    cliente
      .get('/candidatos/me')
      .then((resposta) => setPerfil(resposta.data))
      .catch(() => setErro('Não foi possível carregar seu perfil'))
  }, [])

  async function alternarVisibilidade() {
    setSalvando(true)
    try {
      const novoValor = !perfil.visivel_para_empresas
      await cliente.put('/candidatos/me', { visivel_para_empresas: novoValor })
      setPerfil((atual) => ({ ...atual, visivel_para_empresas: novoValor }))
    } finally {
      setSalvando(false)
    }
  }

  if (erro) {
    return (
      <Layout>
        <Aviso variante="erro">{erro}</Aviso>
      </Layout>
    )
  }

  if (!perfil) {
    return (
      <Layout>
        <p className="texto-suave">Carregando...</p>
      </Layout>
    )
  }

  return (
    <Layout largura="padrao">
      <Botao variante="contorno" icone={ArrowLeft} onClick={() => navegar('/candidato')} style={{ marginBottom: 16 }}>
        Voltar ao início
      </Botao>
      <Cartao titulo="Privacidade e visibilidade" icone={ShieldCheck}>
        <Aviso variante="sucesso">
          De acordo com a LGPD, você decide quem pode ver o seu perfil. Isso pode ser mudado a qualquer momento.
        </Aviso>
        <div className="linha-toggle">
          <div className="linha-toggle__texto">
            <h3>Meu perfil está visível para empresas</h3>
            <p>
              Empresas aprovadas podem te encontrar na busca de candidatos e ver seu currículo. Você pode
              desligar isso quando quiser — mesmo oculto, você continua podendo se candidatar às vagas.
            </p>
          </div>
          <label className="interruptor">
            <input
              type="checkbox"
              checked={perfil.visivel_para_empresas}
              onChange={alternarVisibilidade}
              disabled={salvando}
            />
            <span className="interruptor-trilho"></span>
          </label>
        </div>
        <p style={{ fontSize: 13, color: 'var(--texto-suave)', marginTop: 16 }}>
          Status atual:{' '}
          <b style={{ color: perfil.visivel_para_empresas ? 'var(--sucesso)' : 'var(--texto-suave)' }}>
            {perfil.visivel_para_empresas ? 'visível para empresas' : 'oculto — só você e o Admin veem'}
          </b>
        </p>
      </Cartao>
    </Layout>
  )
}
```

- [ ] **Step 2: Add the `.linha-toggle` and `.interruptor` CSS**

Append to `front-end/src/App.css`:

```css
.linha-toggle {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 0;
  border-bottom: 1px solid var(--borda-sutil);
}

.linha-toggle:last-child {
  border-bottom: none;
}

.linha-toggle__texto h3 {
  font-size: 14.5px;
  margin-bottom: 4px;
}

.linha-toggle__texto p {
  font-size: 13px;
  color: var(--texto-suave);
  max-width: 46ch;
}

.interruptor {
  position: relative;
  width: 44px;
  height: 25px;
  flex: none;
}

.interruptor input {
  opacity: 0;
  width: 0;
  height: 0;
}

.interruptor-trilho {
  position: absolute;
  inset: 0;
  background: #d8d2c4;
  border-radius: 999px;
  cursor: pointer;
  transition: background 0.15s;
}

.interruptor-trilho::before {
  content: '';
  position: absolute;
  width: 19px;
  height: 19px;
  left: 3px;
  top: 3px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.15s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}

.interruptor input:checked + .interruptor-trilho {
  background: var(--sucesso);
}

.interruptor input:checked + .interruptor-trilho::before {
  transform: translateX(19px);
}
```

- [ ] **Step 3: Wire the route**

In `front-end/src/App.jsx`, add the import:

```jsx
import Privacidade from './paginas/Privacidade'
```

And add the route right after `/candidato/interesses`:

```jsx
          <Route
            path="/candidato/privacidade"
            element={
              <RotaProtegida perfilExigido="candidato">
                <Privacidade />
              </RotaProtegida>
            }
          />
```

- [ ] **Step 4: Add a link from the candidate dashboard**

In `front-end/src/paginas/PainelCandidato.jsx`, add `ShieldCheck` to the `lucide-react` import:

```jsx
import { Home, ClipboardList, Search, Bell, Pencil, LogOut, ShieldCheck } from 'lucide-react'
```

Add a new functionality card right after the "Empresas Interessadas" block (before the closing `</div>` of `.lista-funcionalidades`):

```jsx
            <div className="cartao-funcionalidade">
              <span className="cartao-funcionalidade__icone">
                <ShieldCheck size={20} />
              </span>
              <div className="cartao-funcionalidade__texto">
                <strong>Privacidade</strong>
                <p>Controle quem pode ver o seu perfil</p>
              </div>
              <Botao variante="contorno" onClick={() => navegar('/candidato/privacidade')}>
                Gerenciar
              </Botao>
            </div>
```

- [ ] **Step 5: Build and manually verify**

Run: `npm run build`
Expected: succeeds with no errors.

Then `npm run dev`, log in as the candidato, click "Gerenciar" on the new Privacidade card, toggle the switch off and on, reload and confirm the status label matches what you left it at.

- [ ] **Step 6: Commit**

```bash
git add src/paginas/Privacidade.jsx src/App.jsx src/paginas/PainelCandidato.jsx src/App.css
git commit -m "$(cat <<'EOF'
Adiciona tela de Privacidade (LGPD) pro candidato

Toggle de visivel_para_empresas, acessivel a partir do painel do
candidato.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase C — Candidatura direta em vaga

### Task 8: Schemas — `origem` no Interesse

**Files:**
- Modify: `back-end/schemas.py`

**Interfaces:**
- Produces: `InteresseResposta.origem: str`, `InteresseParaCandidato.origem: str`.

- [ ] **Step 1: Add `origem` to the response schemas**

In `InteresseResposta`, add after `status: StatusInteresseEnum`:

```python
    origem: str
```

In `InteresseParaCandidato`, add the same line after its `status: StatusInteresseEnum`.

- [ ] **Step 2: Verify import**

Run: `python -c "import main; print('OK')"`
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add schemas.py
git commit -m "$(cat <<'EOF'
Expoe origem do interesse nos schemas de resposta

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Rota — candidato se candidata a uma vaga

**Files:**
- Modify: `back-end/rotas/candidatos.py`

**Interfaces:**
- Consumes: `Vaga`, `Interesse`, `Empresa` models (already imported), `exigir_candidato`, `_obter_candidato_do_usuario`.
- Produces: `POST /candidatos/vagas/{vaga_id}/candidatar` → `InteresseResposta`.

- [ ] **Step 1: Add `InteresseResposta` to the schema imports**

In `back-end/rotas/candidatos.py`, change the `schemas` import block to add `InteresseResposta`:

```python
from schemas import (
    CandidatoAtualizar,
    CandidatoPerfil,
    FormacaoCriar,
    FormacaoResposta,
    ExperienciaCriar,
    ExperienciaResposta,
    HabilidadeCriar,
    HabilidadeResposta,
    InteresseParaCandidato,
    InteresseResponder,
    InteresseResposta,
    VagaComEmpresa,
)
```

- [ ] **Step 2: Add the route**

Append at the end of `back-end/rotas/candidatos.py` (after `listar_vagas_disponiveis`):

```python
@roteador.post("/vagas/{vaga_id}/candidatar", response_model=InteresseResposta, status_code=status.HTTP_201_CREATED)
def candidatar_se_a_vaga(
    vaga_id: int,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)

    vaga = (
        sessao.query(Vaga)
        .join(Vaga.empresa)
        .filter(Vaga.id == vaga_id, Vaga.ativa.is_(True), Empresa.aprovada.is_(True))
        .first()
    )
    if vaga is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")

    ja_candidatou = (
        sessao.query(Interesse)
        .filter(Interesse.vaga_id == vaga_id, Interesse.candidato_id == candidato.id)
        .first()
    )
    if ja_candidatou is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Você já se candidatou a esta vaga")

    interesse = Interesse(
        empresa_id=vaga.empresa_id,
        candidato_id=candidato.id,
        vaga_id=vaga.id,
        origem="candidato",
    )
    sessao.add(interesse)
    sessao.commit()
    sessao.refresh(interesse)
    return interesse
```

- [ ] **Step 3: Test manually**

Start `python -m uvicorn main:app --port 8123` in the background. Log in as the real candidato account to get a token, then:

```bash
TOKEN="<token do candidato>"
curl -s -X POST http://localhost:8123/candidatos/vagas/1/candidatar -H "Authorization: Bearer $TOKEN" -w "\nSTATUS:%{http_code}\n"
```
Expected: `201` with a JSON body containing `"origem":"candidato"` and `"status":"pendente"` — **only if a vaga with id 1 exists and is `ativa` from an `aprovada` empresa**; otherwise create one first via `POST /empresas/me/vagas` with an approved empresa account. Run the same candidatar request a second time and expect `400` with `"detail":"Você já se candidatou a esta vaga"`.

- [ ] **Step 4: Commit**

```bash
git add rotas/candidatos.py
git commit -m "$(cat <<'EOF'
Adiciona rota de candidatura direta do candidato numa vaga

POST /candidatos/vagas/{id}/candidatar cria um Interesse com
origem="candidato", bloqueando candidatura duplicada na mesma vaga.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: Rota — empresa lista candidaturas recebidas

**Files:**
- Modify: `back-end/rotas/empresas.py`

**Interfaces:**
- Produces: `GET /empresas/me/candidaturas` → `list[InteresseResposta]`.

- [ ] **Step 1: Add the route**

Append right after `listar_meus_interesses` in `back-end/rotas/empresas.py`:

```python
@roteador.get("/me/candidaturas", response_model=list[InteresseResposta])
def listar_candidaturas_recebidas(
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    empresa = _obter_empresa_do_usuario(usuario, sessao)
    return (
        sessao.query(Interesse)
        .filter(Interesse.empresa_id == empresa.id, Interesse.origem == "candidato")
        .all()
    )
```

- [ ] **Step 2: Test manually**

With the local server still running (`python -m uvicorn main:app --port 8123`) and the candidatura created in Task 9's test, log in as the empresa owner of that vaga and:

```bash
TOKEN_EMPRESA="<token da empresa>"
curl -s http://localhost:8123/empresas/me/candidaturas -H "Authorization: Bearer $TOKEN_EMPRESA" -w "\nSTATUS:%{http_code}\n"
```
Expected: `200` with a JSON array containing the candidatura from Task 9 (check `"origem":"candidato"`). Then stop the local server.

- [ ] **Step 3: Commit**

```bash
git add rotas/empresas.py
git commit -m "$(cat <<'EOF'
Adiciona rota de candidaturas recebidas pela empresa

GET /empresas/me/candidaturas lista interesses com origem="candidato",
separado da lista de interesses que a propria empresa enviou.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 11: Front-end — botão "Enviar meu currículo" e confirmação

**Files:**
- Modify: `front-end/src/paginas/VagasDisponiveis.jsx`

**Interfaces:**
- Consumes: `POST /candidatos/vagas/{vaga_id}/candidatar` (Task 9).

- [ ] **Step 1: Add state and the handler**

In `front-end/src/paginas/VagasDisponiveis.jsx`, add `useState` import already present; add new state below the existing ones:

```jsx
  const [candidatadas, setCandidatadas] = useState(new Set())
  const [enviando, setEnviando] = useState(null)
  const [mensagemConfirmacao, setMensagemConfirmacao] = useState(null)

  async function candidatar(vaga) {
    setEnviando(vaga.id)
    try {
      await cliente.post(`/candidatos/vagas/${vaga.id}/candidatar`)
      setCandidatadas((atual) => new Set(atual).add(vaga.id))
      setMensagemConfirmacao(
        `Currículo enviado! A empresa ${vaga.empresa.razao_social || vaga.empresa.usuario.nome} recebeu seu currículo para a vaga ${vaga.titulo}.`
      )
    } catch (erroRequisicao) {
      setErro(erroRequisicao.response?.data?.detail || 'Não foi possível enviar sua candidatura')
    } finally {
      setEnviando(null)
    }
  }
```

- [ ] **Step 2: Render the button and the confirmation banner**

Add `Botao` import already present. Add `CheckCircle2` to the `lucide-react` import:

```jsx
import { ArrowLeft, Briefcase, CheckCircle2 } from 'lucide-react'
```

Right after the opening `{erro && <p className="aviso aviso--erro">{erro}</p>}` line, add:

```jsx
      {mensagemConfirmacao && <p className="aviso aviso--sucesso">{mensagemConfirmacao}</p>}
```

Inside the `.map((vaga) => ...)` block, replace the closing:

```jsx
            <Selo variante="acento">{vaga.area || 'Geral'}</Selo>
          </div>
        ))}
```

with:

```jsx
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Selo variante="acento">{vaga.area || 'Geral'}</Selo>
              {candidatadas.has(vaga.id) ? (
                <Selo variante="sucesso">
                  <CheckCircle2 size={13} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                  Candidatura enviada
                </Selo>
              ) : (
                <Botao
                  variante="primario"
                  onClick={() => candidatar(vaga)}
                  disabled={enviando === vaga.id}
                >
                  {enviando === vaga.id ? 'Enviando...' : 'Enviar meu currículo'}
                </Botao>
              )}
            </div>
          </div>
        ))}
```

Import `Botao` at the top if not already present:

```jsx
import Botao from '../componentes/Botao'
```

- [ ] **Step 3: Build and manually verify**

Run: `npm run build`
Expected: succeeds.

Then `npm run dev`, log in as the candidato, go to "Vagas Disponíveis", click "Enviar meu currículo" on a vaga, confirm the green confirmation banner appears and the button on that row changes to "Candidatura enviada". Refresh the page and click it again on the same vaga — confirm you get the red error "Você já se candidatou a esta vaga" (since the state resets on reload but the back-end still blocks the duplicate).

- [ ] **Step 4: Commit**

```bash
git add src/paginas/VagasDisponiveis.jsx
git commit -m "$(cat <<'EOF'
Adiciona botao "Enviar meu curriculo" nas vagas disponiveis

Candidato agora consegue se candidatar direto numa vaga, com aviso de
confirmacao e bloqueio de candidatura duplicada.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 12: Front-end — aba "Candidaturas Recebidas" na empresa

**Files:**
- Create: `front-end/src/paginas/empresa/AbaCandidaturasRecebidas.jsx`
- Modify: `front-end/src/paginas/PainelEmpresa.jsx`

**Interfaces:**
- Consumes: `GET /empresas/me/candidaturas` (Task 10).

- [ ] **Step 1: Create the tab component (mirrors `AbaInteressesEnviados.jsx`)**

```jsx
// front-end/src/paginas/empresa/AbaCandidaturasRecebidas.jsx
import { useEffect, useState } from 'react'
import cliente from '../../api/cliente'
import Selo from '../../componentes/Selo'

const ROTULOS_STATUS = {
  pendente: { texto: 'Novo', variante: 'sucesso' },
  visualizado: { texto: 'Visualizado', variante: 'acento' },
  aceito: { texto: 'Aceito', variante: 'sucesso' },
  recusado: { texto: 'Recusado', variante: 'navy' },
}

export default function AbaCandidaturasRecebidas() {
  const [candidaturas, setCandidaturas] = useState([])
  const [erro, setErro] = useState('')

  useEffect(() => {
    cliente
      .get('/empresas/me/candidaturas')
      .then((resposta) => setCandidaturas(resposta.data))
      .catch(() => setErro('Não foi possível carregar as candidaturas'))
  }, [])

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Candidaturas recebidas</h2>
      {erro && <p className="aviso aviso--erro">{erro}</p>}
      {candidaturas.length === 0 && !erro && (
        <p className="texto-suave">Ninguém se candidatou diretamente às suas vagas ainda.</p>
      )}
      <div className="lista-candidatos">
        {candidaturas.map((candidatura) => (
          <div key={candidatura.id} className="linha-candidato">
            <div>
              <p className="linha-candidato__nome">{candidatura.candidato.usuario.nome}</p>
              <p className="linha-candidato__info">{candidatura.mensagem || 'Candidatura direta pela vaga'}</p>
            </div>
            <Selo variante={ROTULOS_STATUS[candidatura.status].variante}>
              {ROTULOS_STATUS[candidatura.status].texto}
            </Selo>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Wire the new tab into `PainelEmpresa.jsx`**

Add the import:

```jsx
import AbaCandidaturasRecebidas from './empresa/AbaCandidaturasRecebidas'
```

Add `UserCheck` to the `lucide-react` import:

```jsx
import { Building2, Search, Folder, Bell, BarChart2, LogOut, UserCheck } from 'lucide-react'
```

Add the tab entry to `ABAS`, right after `interesses`:

```jsx
const ABAS = [
  { chave: 'buscar', rotulo: 'Buscar Candidatos', icone: Search },
  { chave: 'vagas', rotulo: 'Minhas Vagas', icone: Folder },
  { chave: 'interesses', rotulo: 'Interesses Enviados', icone: Bell },
  { chave: 'candidaturas', rotulo: 'Candidaturas Recebidas', icone: UserCheck },
  { chave: 'cota', rotulo: 'Relatório de Cota', icone: BarChart2 },
]
```

Add the render branch right after the `interesses` one:

```jsx
        {abaAtiva === 'candidaturas' && <AbaCandidaturasRecebidas />}
```

- [ ] **Step 3: Build and manually verify**

Run: `npm run build`
Expected: succeeds.

Then `npm run dev`, log in as the empresa that received the candidatura from Task 11's test, open "Candidaturas Recebidas" and confirm the candidate row shows up with the "Novo" badge.

- [ ] **Step 4: Commit**

```bash
git add src/paginas/empresa/AbaCandidaturasRecebidas.jsx src/paginas/PainelEmpresa.jsx
git commit -m "$(cat <<'EOF'
Adiciona aba "Candidaturas Recebidas" no painel da empresa

Separada de "Interesses Enviados" -- mostra quem se candidatou direto
numa vaga da empresa.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase D — Orientação

### Task 13: Front-end — página de Orientação

**Files:**
- Create: `front-end/src/dados/conteudoOrientacao.js`
- Create: `front-end/src/paginas/Orientacao.jsx`
- Modify: `front-end/src/App.jsx`
- Modify: `front-end/src/paginas/PainelCandidato.jsx`

**Interfaces:**
- Consumes: `perfil.tipos_vinculo` (CSV string, from `GET /candidatos/me`, Task 2/4) to decide whether to show the entry point.
- Produces: static content array `CONTEUDO_ORIENTACAO`.

- [ ] **Step 1: Create the content data file**

```js
// front-end/src/dados/conteudoOrientacao.js
// Links reais do YouTube (com legenda) entram aqui depois -- por enquanto é só a estrutura.
export const CONTEUDO_ORIENTACAO = [
  {
    categoria: 'Entrevista',
    titulo: 'Dicas para uma boa entrevista',
    descricao: 'Como se preparar e o que levar no dia.',
    url: '',
  },
  {
    categoria: 'Currículo',
    titulo: 'Como montar um currículo simples',
    descricao: 'Passo a passo, sem enrolação.',
    url: '',
  },
  {
    categoria: 'Direitos',
    titulo: 'Seus direitos como pessoa com deficiência',
    descricao: 'O que a lei garante no ambiente de trabalho.',
    url: '',
  },
  {
    categoria: 'Lei de Cotas',
    titulo: 'Lei de Cotas explicada de um jeito simples',
    descricao: 'O que é e quem ela protege.',
    url: '',
  },
  {
    categoria: 'Adaptações',
    titulo: 'Adaptações razoáveis: o que pedir',
    descricao: 'Exemplos práticos de pedidos comuns.',
    url: '',
  },
  {
    categoria: 'Primeiro emprego',
    titulo: 'Preparando-se para o primeiro emprego',
    descricao: 'O que esperar da primeira semana.',
    url: '',
  },
]
```

- [ ] **Step 2: Create the page**

```jsx
// front-end/src/paginas/Orientacao.jsx
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, PlayCircle } from 'lucide-react'
import Layout from '../componentes/Layout'
import Botao from '../componentes/Botao'
import { CONTEUDO_ORIENTACAO } from '../dados/conteudoOrientacao'

export default function Orientacao() {
  const navegar = useNavigate()

  return (
    <Layout largura="largo">
      <Botao variante="contorno" icone={ArrowLeft} onClick={() => navegar('/candidato')} style={{ marginBottom: 16 }}>
        Voltar ao início
      </Botao>
      <h2 style={{ marginBottom: 16 }}>Orientação</h2>
      <div className="grade-orientacao">
        {CONTEUDO_ORIENTACAO.map((item) => (
          <div className="card-video" key={item.titulo}>
            <a
              className="card-video__thumb"
              href={item.url || undefined}
              target="_blank"
              rel="noreferrer"
              aria-disabled={!item.url}
              onClick={(e) => !item.url && e.preventDefault()}
            >
              <span className="card-video__play">
                <PlayCircle size={22} color="#fff" />
              </span>
            </a>
            <div className="card-video__corpo">
              <span className="card-video__categoria">{item.categoria}</span>
              <span className="card-video__titulo">{item.titulo}</span>
              <span className="card-video__desc">{item.descricao}</span>
            </div>
          </div>
        ))}
      </div>
    </Layout>
  )
}
```

- [ ] **Step 3: Add the `.grade-orientacao` / `.card-video` CSS**

Append to `front-end/src/App.css`:

```css
.grade-orientacao {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.card-video {
  border: 1px solid var(--borda-sutil);
  border-radius: 12px;
  overflow: hidden;
  background: var(--cartao);
  display: flex;
  flex-direction: column;
}

.card-video__thumb {
  aspect-ratio: 16 / 9;
  background: linear-gradient(135deg, var(--acento-claro), var(--fundo-2));
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-video__play {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(58, 54, 48, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-video__corpo {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-video__categoria {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--acento-escuro);
  font-weight: 700;
}

.card-video__titulo {
  font-size: 14.5px;
  font-weight: 700;
  color: var(--titulo);
}

.card-video__desc {
  font-size: 12.5px;
  color: var(--texto-suave);
}
```

- [ ] **Step 4: Wire the route and the conditional entry point**

In `front-end/src/App.jsx`, add the import:

```jsx
import Orientacao from './paginas/Orientacao'
```

Add the route after `/candidato/privacidade`:

```jsx
          <Route
            path="/candidato/orientacao"
            element={
              <RotaProtegida perfilExigido="candidato">
                <Orientacao />
              </RotaProtegida>
            }
          />
```

In `front-end/src/paginas/PainelCandidato.jsx`, add `GraduationCap` to the `lucide-react` import, then add a conditional card right after the "Privacidade" card added in Task 7 (only rendered when the candidate marked estágio or menor_aprendiz):

```jsx
            {(perfil.tipos_vinculo || '').split(',').some((t) => t === 'estagio' || t === 'menor_aprendiz') && (
              <div className="cartao-funcionalidade">
                <span className="cartao-funcionalidade__icone">
                  <GraduationCap size={20} />
                </span>
                <div className="cartao-funcionalidade__texto">
                  <strong>Orientação</strong>
                  <p>Dicas de currículo, entrevista e seus direitos</p>
                </div>
                <Botao variante="contorno" onClick={() => navegar('/candidato/orientacao')}>
                  Ver conteúdos
                </Botao>
              </div>
            )}
```

- [ ] **Step 5: Build and manually verify**

Run: `npm run build`
Expected: succeeds.

Then `npm run dev`: with the candidato account NOT marked for estágio/menor_aprendiz, confirm the "Orientação" card is absent from the dashboard. Go check the "Interesse em" checkboxes on Dados Pessoais, mark "Estágio", save, go back to the dashboard and confirm the "Orientação" card now appears; click it and confirm the 6 cards render.

- [ ] **Step 6: Commit**

```bash
git add src/dados/conteudoOrientacao.js src/paginas/Orientacao.jsx src/App.jsx src/paginas/PainelCandidato.jsx src/App.css
git commit -m "$(cat <<'EOF'
Adiciona pagina de Orientacao pro candidato

Conteudo estatico (titulo/categoria/link) com 6 topicos de exemplo --
links reais do YouTube entram depois. Aparece no painel so pra quem
marcou estagio ou menor aprendiz.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase E — Verificação de CNPJ na aprovação de empresa

### Task 14: Back-end — serviço de consulta à BrasilAPI

**Files:**
- Modify: `back-end/requirements.txt`
- Create: `back-end/servicos_externos.py`

**Interfaces:**
- Produces: `consultar_cnpj_receita(cnpj: str) -> dict | None`.

- [ ] **Step 1: Add the `requests` dependency**

In `back-end/requirements.txt`, add a new line at the end:

```
requests==2.32.3
```

- [ ] **Step 2: Write the service function**

```python
# servicos_externos.py - Integrações com APIs públicas de terceiros

import re
import requests


def consultar_cnpj_receita(cnpj: str) -> dict | None:
    """Consulta dados oficiais do CNPJ na BrasilAPI (gratuita, sem chave).
    Retorna None se o CNPJ não existir ou a API estiver fora do ar -- nunca
    lança exceção, pra não travar a tela de aprovação do Admin."""
    cnpj_limpo = re.sub(r"\D", "", cnpj or "")
    if len(cnpj_limpo) != 14:
        return None

    try:
        resposta = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}", timeout=6)
        if resposta.status_code != 200:
            return None
        dados = resposta.json()
        return {
            "razao_social": dados.get("razao_social"),
            "nome_fantasia": dados.get("nome_fantasia"),
            "situacao_cadastral": dados.get("descricao_situacao_cadastral"),
            "data_abertura": dados.get("data_inicio_atividade"),
        }
    except requests.RequestException:
        return None
```

- [ ] **Step 3: Install and verify**

Run: `pip install -r requirements.txt` then `python -c "from servicos_externos import consultar_cnpj_receita; print(consultar_cnpj_receita('19131243000197'))"` (that's the Nubank CNPJ, a known-good public example).
Expected: a dict with `razao_social`, `situacao_cadastral` etc. filled in (not `None`). Also test `print(consultar_cnpj_receita('00000000000000'))` and expect `None`.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt servicos_externos.py
git commit -m "$(cat <<'EOF'
Adiciona consulta de CNPJ via BrasilAPI

Funcao consultar_cnpj_receita, publica e sem chave, nunca lanca
excecao (retorna None em qualquer falha) pra nao travar telas que a
usam.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 15: Rota admin — dados da Receita pra uma empresa pendente

**Files:**
- Modify: `back-end/rotas/admin.py`
- Modify: `back-end/schemas.py`

**Interfaces:**
- Consumes: `consultar_cnpj_receita` (Task 14).
- Produces: `GET /admin/empresas/{empresa_id}/cnpj-receita` → `CnpjReceita`.

- [ ] **Step 1: Add the response schema**

In `back-end/schemas.py`, add after the `EmpresaAdmin` class:

```python
class CnpjReceita(BaseModel):
    encontrado: bool
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    situacao_cadastral: Optional[str] = None
    data_abertura: Optional[str] = None
```

- [ ] **Step 2: Add the route**

In `back-end/rotas/admin.py`, add the import:

```python
from servicos_externos import consultar_cnpj_receita
```

Add `CnpjReceita` to the `schemas` import block. Append the route after `aprovar_empresa`:

```python
@roteador.get("/empresas/{empresa_id}/cnpj-receita", response_model=CnpjReceita)
def consultar_cnpj_da_empresa(
    empresa_id: int,
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    empresa = sessao.query(Empresa).filter(Empresa.id == empresa_id).first()
    if empresa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")

    dados = consultar_cnpj_receita(empresa.cnpj)
    if dados is None:
        return CnpjReceita(encontrado=False)
    return CnpjReceita(encontrado=True, **dados)
```

- [ ] **Step 3: Test manually**

Start `python -m uvicorn main:app --port 8123` in the background. Using the admin test account's token and a pending empresa id from your dev database:

```bash
TOKEN_ADMIN="<token do admin>"
curl -s http://localhost:8123/admin/empresas/1/cnpj-receita -H "Authorization: Bearer $TOKEN_ADMIN" -w "\nSTATUS:%{http_code}\n"
```
Expected: `200` with `"encontrado":false` if that empresa's test CNPJ isn't real (expected for seed/test data), or `"encontrado":true` with Receita fields if it is a real CNPJ. Stop the local server afterward.

- [ ] **Step 4: Commit**

```bash
git add rotas/admin.py schemas.py
git commit -m "$(cat <<'EOF'
Adiciona rota admin de consulta de CNPJ na Receita

GET /admin/empresas/{id}/cnpj-receita busca dados oficiais via
BrasilAPI pro Admin comparar na hora de aprovar.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 16: Front-end — comparação na tela de aprovação de empresa

**Files:**
- Modify: `front-end/src/paginas/PainelAdmin.jsx`

**Interfaces:**
- Consumes: `GET /admin/empresas/{empresa_id}/cnpj-receita` (Task 15).

**Grounding:** `PainelAdmin.jsx` builds one merged `pendentes` array (candidatos + empresas
together, distinguished by `item.tipo`) inside `carregarTudo()`, and renders it in a single
`.map((item) => ...)` with a generic "Aprovar" button. The empresa branch of that mapping
currently only keeps `{ tipo: 'empresa', id: e.id, nome: ..., subtitulo: ... }` — `cnpj` isn't
carried over, so it must be added.

- [ ] **Step 1: Carry the CNPJ into the pending-list items**

In `carregarTudo()`, change the empresa mapping:

```jsx
        ...empresasResp.data.map((e) => ({
          tipo: 'empresa',
          id: e.id,
          nome: e.razao_social || e.usuario.nome,
          subtitulo: 'Aguardando aprovação',
        })),
```

to:

```jsx
        ...empresasResp.data.map((e) => ({
          tipo: 'empresa',
          id: e.id,
          nome: e.razao_social || e.usuario.nome,
          subtitulo: 'Aguardando aprovação',
          cnpj: e.cnpj,
        })),
```

- [ ] **Step 2: Add state and the consulta handler**

Add below the existing `useState` declarations:

```jsx
  const [dadosReceita, setDadosReceita] = useState({})

  async function consultarReceita(empresaId) {
    const resposta = await cliente.get(`/admin/empresas/${empresaId}/cnpj-receita`)
    setDadosReceita((atual) => ({ ...atual, [empresaId]: resposta.data }))
  }
```

- [ ] **Step 3: Render the button and comparison block for empresa items**

Inside the `pendentes.map((item) => ( ... ))` block, change:

```jsx
              <div key={`${item.tipo}-${item.id}`} className="linha-aprovacao">
                <div className="linha-aprovacao__texto">
                  <strong>
                    {item.nome} {item.tipo === 'candidato' ? '(candidato)' : ''}
                  </strong>
                  <p>{item.subtitulo}</p>
                </div>
                <Botao variante="sucesso" icone={Check} onClick={() => aprovar(item)}>
                  Aprovar
                </Botao>
              </div>
```

to:

```jsx
              <div key={`${item.tipo}-${item.id}`} className="linha-aprovacao" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                  <div className="linha-aprovacao__texto">
                    <strong>
                      {item.nome} {item.tipo === 'candidato' ? '(candidato)' : ''}
                    </strong>
                    <p>{item.subtitulo}</p>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {item.tipo === 'empresa' && !dadosReceita[item.id] && (
                      <Botao variante="contorno" onClick={() => consultarReceita(item.id)}>
                        Consultar Receita
                      </Botao>
                    )}
                    <Botao variante="sucesso" icone={Check} onClick={() => aprovar(item)}>
                      Aprovar
                    </Botao>
                  </div>
                </div>
                {item.tipo === 'empresa' && dadosReceita[item.id] && (
                  <div className="comparacao">
                    <div className="comparacao-bloco">
                      <h3>Informado pela empresa</h3>
                      <div className="comparacao-linha">
                        <span className="comparacao-linha__chave">Razão social</span>
                        <span className="comparacao-linha__valor">{item.nome}</span>
                      </div>
                      <div className="comparacao-linha">
                        <span className="comparacao-linha__chave">CNPJ</span>
                        <span className="comparacao-linha__valor">{item.cnpj || 'Não informado'}</span>
                      </div>
                    </div>
                    <div className="comparacao-bloco comparacao-bloco--receita">
                      <h3>Dados oficiais (Receita Federal)</h3>
                      {dadosReceita[item.id].encontrado ? (
                        <>
                          <div className="comparacao-linha">
                            <span className="comparacao-linha__chave">Razão social</span>
                            <span className="comparacao-linha__valor">{dadosReceita[item.id].razao_social}</span>
                          </div>
                          <div className="comparacao-linha">
                            <span className="comparacao-linha__chave">Situação</span>
                            <span className="comparacao-linha__valor">{dadosReceita[item.id].situacao_cadastral}</span>
                          </div>
                          <div className="comparacao-linha">
                            <span className="comparacao-linha__chave">Nome fantasia</span>
                            <span className="comparacao-linha__valor">{dadosReceita[item.id].nome_fantasia || '—'}</span>
                          </div>
                        </>
                      ) : (
                        <p className="texto-suave">CNPJ não encontrado na Receita — confira manualmente antes de aprovar.</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
```

- [ ] **Step 4: Add the `.comparacao` CSS**

Append to `front-end/src/App.css`:

```css
.comparacao {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  margin-top: 12px;
}

.comparacao-bloco {
  border: 1px solid var(--borda-sutil);
  border-radius: 10px;
  padding: 16px;
}

.comparacao-bloco h3 {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--texto-suave);
  margin-bottom: 12px;
}

.comparacao-linha {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 7px 0;
  border-bottom: 1px dashed var(--borda-sutil);
  font-size: 13.5px;
}

.comparacao-linha:last-child {
  border-bottom: none;
}

.comparacao-linha__chave {
  color: var(--texto-suave);
}

.comparacao-linha__valor {
  color: var(--titulo);
  font-weight: 600;
  text-align: right;
}

.comparacao-bloco--receita {
  background: var(--sucesso-claro);
  border-color: transparent;
}

@media (max-width: 640px) {
  .comparacao {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 5: Build and manually verify**

Run: `npm run build`
Expected: succeeds.

Then `npm run dev`, log in as admin, go to the pending-empresas approval section, click "Consultar Receita" on a real test empresa and confirm the comparison block appears with the two columns.

- [ ] **Step 6: Commit**

```bash
git add src/paginas/PainelAdmin.jsx src/App.css
git commit -m "$(cat <<'EOF'
Mostra comparacao com dados da Receita na aprovacao de empresa

Admin consulta o CNPJ real via BrasilAPI e compara lado a lado com o
que a empresa preencheu antes de aprovar -- decisao continua manual.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase F — Notificação por e-mail

### Task 17: Back-end — utilitário de envio de e-mail (Resend)

**Files:**
- Modify: `back-end/requirements.txt`
- Modify: `back-end/.env.example`
- Create: `back-end/notificacoes.py`

**Interfaces:**
- Produces: `enviar_email(destinatario: str, assunto: str, corpo_html: str) -> None`.

- [ ] **Step 1: Add the `resend` dependency**

In `back-end/requirements.txt`, add:

```
resend==2.5.1
```

- [ ] **Step 2: Document the new env var**

In `back-end/.env.example`, add at the end:

```
# Opcional: sem isso, o sistema so' loga a tentativa de e-mail e segue normal.
# Criar em resend.com (plano gratuito, 3000 e-mails/mes) e verificar um dominio remetente.
RESEND_API_KEY=
```

- [ ] **Step 3: Write the notification utility**

```python
# notificacoes.py - Envio de e-mail transacional (Resend). Nunca deve quebrar o fluxo
# principal do usuario: se a chave nao estiver configurada ou o envio falhar, so' loga.

import logging
import os

import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("notificacoes")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> None:
    if not RESEND_API_KEY:
        logger.info("RESEND_API_KEY não configurada — e-mail não enviado (assunto: %s)", assunto)
        return

    try:
        resend.Emails.send(
            {
                "from": "CadaUm <contato@cadaum.com>",
                "to": [destinatario],
                "subject": assunto,
                "html": corpo_html,
            }
        )
    except Exception:
        logger.exception("Falha ao enviar e-mail pra %s", destinatario)
```

- [ ] **Step 4: Install and verify**

Run: `pip install -r requirements.txt` then `python -c "
from notificacoes import enviar_email
enviar_email('teste@example.com', 'Assunto de teste', '<p>Corpo de teste</p>')
print('chamado sem excecao')
"`
Expected: with `RESEND_API_KEY` unset in the local `.env`, prints an INFO log line "RESEND_API_KEY não configurada..." followed by `chamado sem excecao` — confirms the no-key path never raises.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example notificacoes.py
git commit -m "$(cat <<'EOF'
Adiciona utilitario de envio de e-mail via Resend

enviar_email nunca lanca excecao -- sem RESEND_API_KEY configurada,
so' loga e segue, pra nunca quebrar uma acao do usuario por causa de
e-mail.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 18: Disparar e-mail quando a empresa demonstra interesse

**Files:**
- Modify: `back-end/rotas/empresas.py`

**Interfaces:**
- Consumes: `enviar_email` (Task 17).

- [ ] **Step 1: Wire the call into `enviar_interesse`**

In `back-end/rotas/empresas.py`, add the import:

```python
from notificacoes import enviar_email
```

In `enviar_interesse`, right after `sessao.refresh(interesse)` and before `return interesse`, add:

```python
    enviar_email(
        destinatario=candidato.usuario.email,
        assunto="Uma empresa se interessou pelo seu perfil — CadaUm",
        corpo_html=(
            f"<p>Olá, {candidato.usuario.nome.split(' ')[0]}!</p>"
            f"<p>A empresa <b>{empresa.razao_social or empresa.usuario.nome}</b> demonstrou interesse "
            "no seu perfil. Entre na plataforma pra ver os detalhes e responder.</p>"
        ),
    )
```

- [ ] **Step 2: Test manually**

Start `python -m uvicorn main:app --port 8123` in the background (with `RESEND_API_KEY` still unset locally). Log in as an approved empresa and send an interesse to a candidato:

```bash
TOKEN_EMPRESA="<token da empresa>"
curl -s -X POST http://localhost:8123/empresas/me/interesses -H "Authorization: Bearer $TOKEN_EMPRESA" -H "Content-Type: application/json" -d '{"candidato_id": 1}' -w "\nSTATUS:%{http_code}\n"
```
Expected: `201` as before, plus an INFO log line in the server output ("RESEND_API_KEY não configurada...") showing the email call happened without breaking the request. Stop the local server afterward.

- [ ] **Step 3: Commit**

```bash
git add rotas/empresas.py
git commit -m "$(cat <<'EOF'
Envia e-mail ao candidato quando uma empresa demonstra interesse

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase G — Deploy e verificação final em produção

### Task 19: Rodar a migração em produção e validar o fluxo completo

**Files:** none (operational task).

- [ ] **Step 1: Push both repos**

```bash
cd back-end && git push origin main
cd ../front-end && git push origin main
```
Expected: both push cleanly (Render and Vercel auto-deploy from `main`).

- [ ] **Step 2: Run the migration against the production Supabase database**

Temporarily point `back-end/.env`'s `DATABASE_URL` at the same production Supabase connection string already configured on Render (it's the same database used throughout this project — there's no separate staging DB), then:

```bash
python migrar_perfil_v2.py
```
Expected: same six `OK: ...` lines as Task 1's local run.

- [ ] **Step 3: Wait for Render/Vercel deploys to finish, then smoke-test in production**

Check `https://cada-um-back-end.onrender.com/saude` returns `{"status":"ok"}`. Open `https://cadaum.vercel.app`, log in as the real candidato account, and walk through: fill the new profile fields and save, toggle Privacidade off and on, open a vaga and click "Enviar meu currículo", then log in as an empresa and confirm the candidatura shows up under "Candidaturas Recebidas".

- [ ] **Step 4: No commit for this task** (operational verification only).

---

## Self-Review Notes

- **Spec coverage:** every section of `2026-08-04-perfil-candidatura-lgpd-design.md` maps to a phase — perfil expandido (A), privacidade (B), candidatura direta (C), orientação (D), CNPJ (E), e-mail (F). The out-of-scope "só agências de emprego" item is intentionally not implemented.
- **Deviation from spec documented:** the spec suggested a join table for `tipos_vinculo`; this plan uses a CSV `String` column instead (Task 2), justified in the Architecture section above.
- **Type consistency checked:** `tipos_vinculo` is consistently a comma-separated string at the API boundary in every task that touches it (schemas, route, both front-end pages); `origem` is consistently a plain string (`"empresa"`/`"candidato"`), never a DB-level enum, avoiding the raw-migration enum-type problem.
- **Task 16 was re-grounded against the real file** after an initial draft that asked the implementer to read `PainelAdmin.jsx` first — that file has since been read during planning, and the task now cites its exact current structure (the merged `pendentes` array, the `carregarTudo` mapping) and gives fully written diffs instead of a placeholder step.
