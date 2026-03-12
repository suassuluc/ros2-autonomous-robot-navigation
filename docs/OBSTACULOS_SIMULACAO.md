# Onde estão os obstáculos na simulação (turtlebot3_world)

O mundo **turtlebot3_world** do TurtleBot3 Gazebo tem obstáculos fixos. As coordenadas abaixo estão no **frame do mundo** (odom): **x** = frente, **y** = esquerda, em **metros**. O robô costuma iniciar perto de **(0, 0)**.

---

## 1. Coordenadas no arquivo do mundo (turtlebot3_world)

O mundo é definido em:

`/opt/ros/humble/share/turtlebot3_gazebo/models/turtlebot3_world/model.sdf`

Cada `<pose>` é **x y z roll pitch yaw** (z, roll, pitch, yaw não importam para navegação 2D). A tabela abaixo lista **(x, y)** no plano.

### Hexagonos (obstáculos cilíndricos)

| Nome no modelo | x (m) | y (m) | Observação        |
|----------------|-------|-------|-------------------|
| one_one        | -1.1  | -1.1  |                   |
| one_two        | -1.1  | 0     |                   |
| one_three      | -1.1  | 1.1   |                   |
| two_one        | 0     | -1.1  |                   |
| two_two        | 0     | 0     | **Centro** (onde o robô pode spawnar) |
| two_three      | 0     | 1.1   |                   |
| three_one      | 1.1   | -1.1  |                   |
| three_two      | 1.1   | 0     |                   |
| three_three    | 1.1   | 1.1   |                   |

### Outros obstáculos (mãos, pés, cabeça, corpo)

| Nome      | x (m) | y (m) |
|-----------|-------|-------|
| head      | 3.5   | 0     |
| left_hand | 1.8   | 2.7   |
| right_hand| 1.8   | -2.7  |
| left_foot | -1.8 | 2.7   |
| right_foot| -1.8 | -2.7  |

O **body** é uma parede/corpo alongado centrado em (0, 0) com rotação; ocupa parte do centro.

---

## 2. Resumo para escolher objetivos

- **Evite** objetivos exatamente em: **(0, 0)**, **(±1.1, ±1.1)**, **(±1.1, 0)**, **(0, ±1.1)**, **(1.8, ±2.7)**, **(-1.8, ±2.7)**, **(3.5, 0)** — são centros dos obstáculos.
- **Regiões mais livres** (entre os hexagonos): por exemplo **(0.5, 0.5)**, **(-0.5, -0.5)**, **(2, 0.5)**, **(2, 1)** (cuidado com a “cabeça” em 3.5).

---

## 3. Como ver obstáculos em tempo de execução (pelo robô)

Com a **simulação rodando**, o tópico **`/scan`** (LaserScan) dá as distâncias ao redor do robô. Você não vê “coordenadas do mundo” diretamente, mas vê **ângulo e distância**; a partir da **pose do robô** (`/odom`) dá para converter para (x, y) no mundo.

### Ver distâncias mínimas (obstáculos à frente)

```bash
# Distância mínima publicada pelo obstacle_detector (quando o nó está rodando)
ros2 topic echo /min_obstacle_distance

# Ou inspecionar o scan bruto (ângulos e ranges em metros)
ros2 topic echo /scan
```

### Ver pose do robô (para saber onde ele está no mundo)

```bash
ros2 topic echo /odom
# use pose.pose.position.x e .y (e orientação em pose.pose.orientation)
```

Assim você sabe em quais **(x, y)** o robô está; os obstáculos estão nas coordenadas listadas acima. O navegador usa o próprio `/scan` para montar o grid e o A*; não é obrigatório consultar este documento em tempo de execução.

---

## 4. Outros mundos

- **empty_world**: sem obstáculos; coordenadas livres.
- **turtlebot3_house**: ambiente em forma de casa; obstáculos definidos no modelo `turtlebot3_house` (outro arquivo .sdf).

Para ver as poses de qualquer mundo, abra o `.world` ou o `model.sdf` do modelo incluído (em `share/turtlebot3_gazebo/worlds/` e `models/`) e procure por `<pose>`.
