# Ciclo de exploração (autonomia aparente)

O **obstacle_avoider** sozinho desvia de obstáculos mas não tem noção de “ir para outro lugar”; em sessões longas o robô tende a repetir a mesma rota. O **exploration_goal_node** publica um novo objetivo em `/goal` a cada N minutos. Com o avoider em modo **use_goal:=true**, o robô tende a ir em direção a esse objetivo e desvia de obstáculos; quando o tempo acaba, recebe outro objetivo e muda de rota. Assim, em cerca de **20 minutos** o robô percorre várias regiões do mapa em vez de ficar 40+ min na mesma rota.

---

## 1. Como usar

Com a simulação já rodando (TurtleBot3):

```bash
source /opt/ros/humble/setup.bash
source /home/shini/ros2_ws/install/setup.bash
ros2 launch robot_sim avoider_exploration.launch.py
```

O launch sobe:

- **obstacle_avoider** com `use_goal:=true` (usa `/goal` para escolher a direção).
- **exploration_goal** (publica um novo `/goal` a cada intervalo).

O robô continua desviando de obstáculos e “aprendendo” onde há obstáculos pelo laser; a diferença é que a **meta** muda de tempos em tempos, gerando um ciclo de movimento e mais cobertura do mapa.

---

## 2. Parâmetros principais

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `goal_interval_sec` | 120 | Intervalo em segundos entre novos objetivos (120 = 2 min → ~10 rotas em 20 min). |
| `use_relative_goals` | true | **true**: objetivo = posição atual + distância aleatória em direção aleatória (exploração contínua). **false**: objetivo = ponto aleatório no retângulo (goal_x_min/max, goal_y_min/max). |
| `relative_min_dist` | 1.5 | Distância mínima (m) para objetivo relativo. |
| `relative_max_dist` | 4.0 | Distância máxima (m) para objetivo relativo. |
| `goal_x_min`, `goal_x_max` | -2.5, 2.5 | Limites do retângulo (modo absoluto ou limite para modo relativo). |
| `goal_y_min`, `goal_y_max` | -2.5, 2.5 | Idem em y. |

**Exemplos:**

- Novo objetivo a cada **3 min** (≈ 6–7 rotas em 20 min):  
  `ros2 launch robot_sim avoider_exploration.launch.py goal_interval_sec:=180`
- Objetivos mais longe (5–8 m):  
  `ros2 launch robot_sim avoider_exploration.launch.py relative_min_dist:=5.0 relative_max_dist:=8.0`
- Objetivos absolutos no retângulo (ex.: turtlebot3_world):  
  `ros2 launch robot_sim avoider_exploration.launch.py use_relative_goals:=false`

---

## 3. Ideia do “percorrer o mapa em ~20 min”

- Com **goal_interval_sec:=120** (2 min), em 20 min o robô recebe **10 objetivos** diferentes.
- Com **use_relative_goals:=true**, cada objetivo fica à frente em direção aleatória (entre 1,5 e 4 m), limitado ao retângulo; o robô tende a explorar em várias direções.
- O avoider não “vai em linha reta” até o goal: ele desvia de obstáculos e tende na direção do goal. Assim o trajeto varia e, ao longo de 20 min, várias regiões do mapa são visitadas, mantendo desvio e a sensação de autonomia.

---

## 4. Tópicos

| Tópico | Tipo | Uso |
|--------|------|-----|
| `/goal` | geometry_msgs/Point | Objetivo atual (publicado pelo exploration_goal; lido pelo obstacle_avoider). |
| `/odom` | nav_msgs/Odometry | Posição atual (usada pelo exploration_goal para objetivos relativos). |
| `/cmd_vel` | geometry_msgs/Twist | Saída do avoider (comando do robô). |

---

*Última atualização: mar. 2025.*
