# Esteira-APS_LogComp

Esteira é uma linguagem para descrever treinos de esteira e rotinas genéricas que depois são traduzidas para uma VM com registradores, memória indexada e sensores de leitura. 

Um programa começa com esteira "Nome" { … } e, dentro do bloco, é possível declarar variáveis (var x:int = 0), fazer atribuições, usar condicionais (se … senao …) e laços (enquanto …). 

A linguagem expõe sensores como sensor.nome (por exemplo sensor.frequencia_cardiaca), leitura de registradores por reg(R0..R3) e acesso à memória por mem[expr]. 

O controle do equipamento ocorre por ações simples (ligar, desligar, iniciar, parar) e os parâmetros de treino são definidos de forma declarativa, como definir velocidade = 10 km/h ou definir inclinacao = 3 %.

Tempo e In/Out são cobertos por esperar (com unidades ms, s, min), mostrar(…) e bip. 

As expressões aritméticas e lógicas seguem a precedência usual, permitindo combinar valores, sensores, registradores e memória, e aceitar unidades oficiais ao final do valor (km/h, m/s, %, graus, bpm, km, m, min, s). 

A proposta é oferecer sintaxe para scripts de treino e também para algoritmos gerais, mantendo o conjunto mínimo exigido (variáveis, condicionais e loops) para posterior compilação ao assembly da VM.