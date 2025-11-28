# DSLs de Exemplo sobre a MicrowaveVM

Este repositório contém **três linguagens de domínio específico (DSLs)** que compilam para o assembly simples `.mwasm` executado por uma pequena VM de dois registradores (TIME e POWER + pilha). Este README descreve **apenas as linguagens** e como usá‑las. (Detalhes da VM ficam no código de `main.py`).

## Visão Geral Rápida

| DSL | Arquivo compilador | Extensão fonte | Domínio | Saída | Uso básico |
|-----|--------------------|----------------|---------|-------|-----------|
| CookScript | `cookscript.py` | `.cs` | Receita de micro-ondas (potência, tempos, beeps) | `.mwasm` | `python3 cookscript.py defrost.cs > defrost.mwasm` |
| MicroSong  | `microsong.py`  | `.ms` | Sequência musical simples (notas, ritmo) | `.mwasm` | `python3 microsong.py song.ms > song.mwasm` |
| MicroWars  | `microwars.py`  | `.mwrs` | Duelo entre duas unidades (ataques e cura) | `.mwasm` | `python3 microwars.py battle.mwrs > battle.mwasm` |

Após gerar o `.mwasm`, execute com:

```bash
python3 main.py arquivo.mwasm
```

---

## 1. CookScript (`.cs`)

DSL para descrever perfis de aquecimento / descongelamento com blocos, repetição e beeps.

### Construções Suportadas

- `power <n>`: ajusta potência (ex.: 30, 70, 100)
- `cook <t>`: tempo de cozimento ativo em segundos
- `rest <t>`: tempo com potência 0
- `beep`: emite sinal sem perder o contador de tempo
- `repeat <n> { ... }`: repete bloco `n` vezes
- `every <k> seconds beep during <t> seconds`: beep a cada `k` segundos durante `t` segundos
- `stage "Nome" { ... }`: bloco apenas organizacional; insere marcador (duplo beep)
- Açúcar sintático:
  - `defrost <t>` ≡ `power 30; cook <t>`
  - `reheat <t>`  ≡ `power 70; cook <t>`
  - `full <t>`    ≡ `power 100; cook <t>`
- Salvamento opcional de registradores (casos avançados): `save_power / restore_power / save_time / restore_time`
- `halt` (opcional; se omitido você pode concatenar programas manualmente)

### Exemplo (trecho)

```text
repeat 3 {
  power 70
  cook 45
  beep
  rest 10
}
halt
```

### Observações de Design

- `repeat` preserva o valor de TIME dentro do corpo (empilha antes de executar o bloco) permitindo aninhar `cook`.
- `every ... beep ...` usa POWER como subcontador; sobrescreve a potência anterior (intencional).
- Beep “não destrutivo” salva e restaura TIME.

---

## 2. MicroSong (`.ms`)

DSL minimalista de partitura: notas com duração relativa, pausas e configuração de tempo.

### Construções (Elementos)

- `tempo <bpm>`: define BPM (padrão 120)
- `tpb <ticks>`: ticks por semínima (padrão 8)
- Notas: `C4/4`, `D#4/8`, `Bb3/2` etc.
  - Formato: `[A-G][#|b]?<oitava>/<den>`
  - Duração em ticks: `(4/den) * tpb` arredondado para inteiro ≥1
- Pausa: `R/<den>`
- Barra opcional: `|` (ignorada)
- Comentários iniciam com `#`

### Como Mapeia

- Cada nota: POWER = frequência aproximada (equal temperament A4=440Hz), laço imprimindo ticks.
- Cada pausa: POWER = 0, laço de espera silencioso.
- Programa termina com `HALT` automático.

### Exemplo

```text
tempo 120
tpb 8
C4/4 C4/4 G4/4 G4/4 | A4/4 A4/4 G4/2
```

### Observações

- Frequência arredondada para inteiro; fácil trocar para escala ou fator se desejar limitar intervalo.
- Não há sustain ou dinâmica (volume); foco é sequência simples de “beeps”.

---

## 3. MicroWars (`.mwrs`)

DSL para simular uma pequena batalha entre exatamente duas unidades.

### Declaração de Unidades

```text
unit "Guerreiro" health 50 attack 7
unit "Mago"     health 30 attack 10
```

(Exatamente duas linhas de unidade são obrigatórias; nomes arbitrários.)

### Script de Batalha

Ordem típica:

```text
start_battle
attack "Guerreiro" -> "Mago" repeat 3
attack "Mago" -> "Guerreiro" repeat 2
special "Mago" heal 5
attack "Guerreiro" -> "Mago" repeat 4
end_battle
```

### Construções

- `start_battle` / `end_battle`: marcam início e final.
- `attack "A" -> "B" repeat N`: A ataca B N vezes (unroll em tempo de compilação). Omita `repeat N` para 1.
- `special "X" heal K`: cura X em K pontos.

### Semântica dos Ataques

- Cada ataque consome até `attack` pontos de vida do defensor, 1 por “tick”; a cada ponto aplicado é feito um `PRINT` (beep de acerto).
- Se a vida do defensor chega a 0 a execução desse ataque interrompe antes de completar os ticks restantes.
- Vida das duas unidades é mantida na pilha em ordem fixa; manipulações usam POP/PUSH e um swap simples.

### Observações de Design (MicroWars)

- O `repeat` foi implementado por *unrolling* para evitar conflito no uso do registrador TIME durante o laço interno de dano.
- Registro POWER guarda a força restante no ataque; TIME guarda a vida atual do defensor durante a resolução daquele ataque.

---

## Fluxo de Trabalho

1. Escreva o arquivo fonte (`.cs`, `.ms` ou `.mwrs`).
2. Compile para `.mwasm`:

```bash
python3 cookscript.py defrost.cs > defrost.mwasm
python3 microsong.py song.ms > song.mwasm
python3 microwars.py battle.mwrs > battle.mwasm
```

3. Execute na VM:

```bash
python3 main.py battle.mwasm
```

---

## Mensagens de Erro Comuns

- CookScript: "Unknown syntax" → linha inválida ou chave de fechamento sem bloco.
- MicroSong: "Bad token" → formato de nota/pausa incorreto.
- MicroWars: "Exactly two units must be declared" ou nomes repetidos.

---

## Extensões Futuras (Ideias)

- CookScript: perfis parametrizados, `if power > x then ...` simples.
- MicroSong: ligaduras (sustain), repetição (`repeat { ... }`), transposição.
- MicroWars: tipos de ataque (crítico, área), condição de vitória explícita.

---

## Licença

Defina aqui a licença (MIT, GPL, etc.).

---

Boa exploração! Ajuste os compiladores conforme quiser experimentar mais padrões de tradução para o mesmo núcleo de VM.
