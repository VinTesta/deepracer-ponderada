# AWS DeepRacer - Análise da função de recompensa

## 1. Contexto da atividade
As alterações realizadas ficaram restritas às funções de recompensa presentes na pasta `rewards/`. Foram comparadas duas estratégias principais:

- `reward_v1_centralista.py`: recompensa baseada em permanência próxima ao centro da pista.
- `reward_v2_velocista.py`: recompensa composta por velocidade, suavidade da direção e progresso.

O vídeo final da execução está disponível em:

https://drive.google.com/file/d/1WgO6M982Tllq4yvLaZLH5sFWVh4-Gt0a/view?usp=sharing

## 2. Análise Individual

### 2.1 Função de recompensa proposta

A função de recompensa final foi a versão `reward_v2_velocista.py`. Ela foi pensada para incentivar um comportamento mais rápido, mas sem ignorar completamente a estabilidade do agente na pista.

A lógica principal da função é:

```python
def reward_function(params):
    if not params['all_wheels_on_track']:
        return 1e-3

    speed = params['speed']
    abs_steering = abs(params['steering_angle'])
    progress = params['progress']

    speed_reward = speed / 4.0
    smoothness = max(0.0, 1.0 - (abs_steering / 30.0))
    progress_bonus = progress / 100.0

    reward = 0.5 * speed_reward + 0.3 * smoothness + 0.2 * progress_bonus
    return float(max(reward, 1e-3))
```

A recompensa foi dividida em três componentes:

- `speed_reward`: normaliza a velocidade em relação a um limite de referência de `4.0`. Esse termo tem peso `0.5`, sendo o principal critério da política.
- `smoothness`: penaliza ângulos de direção muito altos. Quanto maior o módulo de `steering_angle`, menor a recompensa de suavidade. Esse termo tem peso `0.3`.
- `progress_bonus`: adiciona uma recompensa proporcional ao percentual de pista concluído. Esse termo tem peso `0.2`.

Também foi incluída uma penalização forte quando o agente sai da pista. Se `all_wheels_on_track` for falso, a função retorna `1e-3`, que é uma recompensa mínima. Isso evita que trajetórias fora da pista tenham retorno relevante durante o treinamento.

### 2.2 Justificativa das escolhas

A primeira versão da reward era mais conservadora. Ela privilegiava a distância em relação ao centro da pista:

```python
reward = 1.0 - (distance_from_center / marker) ** 2
```

Esse formato tende a produzir uma política mais estável, porque o agente recebe maior retorno quando permanece perto do centro. Porém, esse critério sozinho não ensina diretamente o agente a ser mais rápido, nem diferencia bem uma volta lenta de uma volta eficiente. Em termos de RL, o sinal de recompensa fica muito associado à segurança da trajetória, mas pouco associado ao desempenho temporal.

Na segunda versão, a intenção foi alterar o objetivo da política. O agente deveria continuar evitando sair da pista, mas passaria a receber mais incentivo por velocidade e por avanço na volta. Por isso, a reward final ficou com maior peso para velocidade (`0.5`), peso intermediário para suavidade (`0.3`) e peso menor para progresso (`0.2`).

A suavidade foi mantida porque aumentar apenas a velocidade pode gerar um comportamento instável. Em curvas, o agente pode tentar manter aceleração alta e usar ângulos de direção agressivos, aumentando a chance de sair da pista. O termo de `smoothness` funciona como uma regularização simples da política, favorecendo ações menos bruscas.

O bônus de progresso foi usado para aproximar a recompensa do objetivo real da tarefa: completar a pista. Sem esse termo, o agente poderia maximizar velocidade localmente sem necessariamente aprender uma trajetória que avance de forma consistente.

### 2.3 Comportamento observado do agente

Durante a execução demonstrada no vídeo, o carrinho conseguiu completar uma volta, mas saiu da pista algumas vezes durante o teste e precisou reiniciar. Isso indica que a política aprendeu uma sequência de ações capaz de percorrer a pista inteira, mas ainda não convergiu para um comportamento totalmente robusto.

O comportamento observado é coerente com a reward final. Como a velocidade tem o maior peso, o agente tende a escolher ações mais agressivas. Esse tipo de política pode reduzir o tempo de volta quando funciona, mas aumenta a variância do desempenho, principalmente em trechos de curva. Quando o agente entra em uma curva com velocidade alta, pequenas decisões ruins de direção podem levar à perda de controle e saída da pista.

Mesmo com essas falhas, o fato de completar uma volta mostra que a função de recompensa não gerou apenas um comportamento aleatório ou degenerado. O agente conseguiu associar progresso e permanência na pista a maior retorno acumulado. A principal limitação observada foi a falta de estabilidade em todos os trechos da pista.

### 2.4 Comparação entre as duas variações de reward

A comparação foi feita entre a versão centralista (`v1`) e a versão velocista (`v2`).

Na `v1`, a recompensa depende basicamente da distância até o centro da pista. Se o agente fica mais centralizado, recebe mais recompensa; se se afasta do centro, recebe menos. Essa abordagem é simples e gera um sinal denso, pois praticamente todo passo dentro da pista recebe algum valor útil. A desvantagem é que ela não considera explicitamente velocidade, progresso ou eficiência da volta.

Na `v2`, a recompensa passa a combinar múltiplos critérios. O agente é incentivado a andar mais rápido, manter direção suave e aumentar o progresso na pista. Essa formulação é mais alinhada com o objetivo final de completar a volta com bom desempenho, mas também torna o comportamento mais arriscado.

Pelos logs, a `v1` registrou 160 episódios, reward média de `66.64` e média de `88.6` passos por episódio quando calculado o delta dos passos acumulados. Nos últimos 20 episódios, a reward média subiu para `138.73`, com média de `166.8` passos por episódio. O melhor episódio teve reward `327.34`.

Na `v2`, foram registrados 162 episódios, reward média de `13.58` e média de `67.8` passos por episódio. Nos últimos 20 episódios, a reward média foi `28.10`, com média de `119.7` passos por episódio. O melhor episódio teve reward `69.93`.

Esses valores não devem ser comparados apenas de forma absoluta, porque as escalas das funções de recompensa são diferentes. A `v1` gera valores maiores naturalmente por causa da forma da equação, enquanto a `v2` combina termos normalizados. Mesmo assim, os logs sugerem que a `v1` produziu episódios mais longos e mais estáveis durante o treinamento, enquanto a `v2` foi mais agressiva e menos consistente.

Na prática, a `v2` foi interessante por direcionar melhor o agente para performance, mas o vídeo mostra que ainda existe um compromisso entre velocidade e estabilidade. O carrinho completa a volta, porém com saídas de pista durante a execução.

### 2.5 Reflexão sobre possíveis melhorias

Uma melhoria seria adaptar a recompensa de velocidade de acordo com o trecho da pista. Em retas, o agente poderia receber incentivo maior para acelerar. Em curvas, a recompensa poderia reduzir o peso da velocidade e aumentar a penalização para direções bruscas. Isso deixaria a política menos agressiva em regiões de maior risco.

Outra possibilidade seria usar os `waypoints` para estimar a curvatura local da pista. Com isso, a função poderia calcular se o agente está se aproximando de uma curva e ajustar a recompensa antes da saída da pista acontecer. Essa abordagem tornaria o sinal de recompensa mais informativo, pois o agente receberia feedback preventivo, não apenas uma penalização depois do erro.

Também seria válido incluir um termo relacionado a `steps` e `progress`, como progresso por passo. Esse critério poderia incentivar eficiência real, premiando o agente quando ele avança bastante usando menos passos, sem depender apenas da velocidade instantânea.

Por fim, a reward poderia equilibrar melhor centralização e velocidade. A versão final priorizou velocidade, mas os resultados indicam que algum componente de distância em relação ao centro ainda seria útil para reduzir saídas de pista. Uma versão futura poderia combinar a estabilidade da `v1` com o objetivo de desempenho da `v2`, gerando uma política mais consistente ao longo de vários episódios.
