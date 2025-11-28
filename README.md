# Esteira-APS_LogComp

Esteira é uma linguagem para descrever treinos de esteira e rotinas genéricas que depois são traduzidas para uma VM com registradores, memória indexada e sensores de leitura. 

Um programa começa com esteira "Nome" { … } e, dentro do bloco, é possível declarar variáveis (var x:int = 0), fazer atribuições, usar condicionais (se … senao …) e laços (enquanto …). 

A linguagem expõe sensores como sensor.nome (por exemplo sensor.frequencia_cardiaca), leitura de registradores por reg(R0..R3) e acesso à memória por mem[expr]. 

O controle do equipamento ocorre por ações simples (ligar, desligar, iniciar, parar) e os parâmetros de treino são definidos de forma declarativa, como definir velocidade = 10 km/h ou definir inclinacao = 3 %.

Tempo e In/Out são cobertos por esperar (com unidades ms, s, min), mostrar(…) e bip. 

As expressões aritméticas e lógicas seguem a precedência usual, permitindo combinar valores, sensores, registradores e memória, e aceitar unidades oficiais ao final do valor (km/h, m/s, %, graus, bpm, km, m, min, s). 

A proposta é oferecer sintaxe para scripts de treino e também para algoritmos gerais, mantendo o conjunto mínimo exigido (variáveis, condicionais e loops) para posterior compilação ao assembly da VM.

---
## Relatório

### Código da minha linguagem

```est
esteira "teste" {
    var tempo:int = 5;
    var potencia:int = 60;

    ligar;

    enquanto (tempo > 0) {
        mostrar(tempo);
        tempo = tempo - 1;
    }

    desligar;
    parar;
}
```

---

### Código mwasm gerado

```
; Codigo gerado pela linguagem ESTEIRA para MicrowaveVM
SET TIME 5
SET POWER 60
SET POWER 60
L0:
DECJZ TIME L1
PRINT
DECJZ TIME L2
L2:
GOTO L0
L1:
SET POWER 0
HALT
; Programa "teste"
HALT
```

---

### Rodando um código exemplo gerado na minha linguagem utilizando a VM do microwave:

```
Loaded program from: programas/programa.mwasm
TIME: 4
TIME: 2
TIME: 0
BEEEEEEP!
Final state: {'TIME': 0, 'POWER': 0}
Final readonly state: {'TEMP': 70, 'WEIGHT': 100}
Final stack: []
```
---
### Rodando outros programas testes

#### Teste 01 -> Básico

```
Loaded program from: programas/test01_basico.mwasm
TIME: 3
BEEEEEEP!
Final state: {'TIME': 3, 'POWER': 0}
Final readonly state: {'TEMP': 15, 'WEIGHT': 100}
Final stack: []
```

#### Teste 02 -> Loop

```
Loaded program from: programas/test02_loop_tempo.mwasm
TIME: 4
TIME: 2
TIME: 0
BEEEEEEP!
Final state: {'TIME': 0, 'POWER': 0}
Final readonly state: {'TEMP': 70, 'WEIGHT': 100}
Final stack: []
```

#### Teste 03 -> Esperar

```
Loaded program from: programas/test03_esperar.mwasm
TIME: 0
TIME: 0
TIME: 0
BEEEEEEP!
Final state: {'TIME': 0, 'POWER': 0}
Final readonly state: {'TEMP': 246, 'WEIGHT': 100}
Final stack: []
```