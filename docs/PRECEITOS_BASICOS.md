# Preceitos Básicos — Robótica e este Projeto

Este documento é uma **segunda documentação** do projeto: explica conceitos básicos de robótica móvel e mostra **o que cada trecho importante de código faz**, usando exemplos deste repositório. Serve para aprender a base que sustenta a navegação autônoma (sensores, controle PID, planejamento A*, integração no ROS 2).

Para instalar, configurar e rodar a simulação, use o [Guia de início](GETTING_STARTED.md).

---

## 1. Introdução

Em robótica móvel autônoma, o robô precisa:

1. **Saber onde está** (odometria, sensores).
2. **Saber o que há ao redor** (obstáculos, mapa).
3. **Decidir por onde ir** (planejamento de caminho).
4. **Executar o movimento** (controle de velocidade).

Neste projeto, o TurtleBot3 em simulação (Gazebo) usa **odometria** e **LaserScan**; o pacote `robot_sim` implementa **A*** para planejar e **PID** para seguir waypoints, publicando comandos em `/cmd_vel`. Os conceitos abaixo aparecem diretamente no código.

---

## 2. Coordenadas e referencial

O robô e o mundo são descritos em **referenciais** (frames). Dois importantes:

- **map / odom:** referencial fixo do mundo (ou da odometria). A pose do robô é dada em relação a ele.
- **base_link (robô):** referencial preso ao robô; a frente do robô é normalmente o eixo **x**, e o eixo **y** aponta para a esquerda.

A **pose** do robô é \((x, y, \theta)\): posição no plano e ângulo de orientação (yaw). No ROS 2, a odometria em `/odom` traz `pose.pose.position` (x, y, z) e `pose.pose.orientation` (quaternion); para navegação 2D usamos x, y e o ângulo \(\theta\) derivado do quaternion.

**Por que importa:** o planejamento (A*) e o controle (PID) precisam de posição e ângulo atuais e do objetivo no mesmo referencial (por exemplo, odom). O LaserScan vem no frame do robô; para montar um grid no mundo, transformamos os pontos com a pose atual.

---

## 3. Robô diferencial

O TurtleBot3 é um **robô diferencial**: duas rodas motorizadas e um castor. Ele não anda de lado; o movimento é controlado por:

- **Velocidade linear** (para frente/trás): `linear.x` em m/s.
- **Velocidade angular** (giro no lugar): `angular.z` em rad/s.

No ROS 2 isso é enviado na mensagem **`geometry_msgs/msg/Twist`** no tópico **`/cmd_vel`**. Quem “obedece” é o plugin do Gazebo (ou o firmware no robô real): ele lê Twist e aplica às rodas.

**Exemplo no projeto:** o script `scripts/cmd_vel_relay.py` só repassa Twist de um nó para outro (por exemplo, para compatibilizar QoS). O trecho que realmente “fala” com o robô é a criação do publisher de Twist:

```python
# scripts/cmd_vel_relay.py (trecho)
from geometry_msgs.msg import Twist

pub = node.create_publisher(Twist, 'cmd_vel', qos)
# ...
# Quando outro nó publica em cmd_vel, o lambda repassa:
sub = node.create_subscription(
    Twist,
    'cmd_vel',
    lambda msg: pub.publish(msg),
    qos,
)
```

- **Twist:** mensagem com `linear` (x, y, z) e `angular` (x, y, z). No diferencial usamos só `linear.x` e `angular.z`.
- **Publisher/Subscriber:** padrão ROS 2: um nó publica mensagens em um tópico; outro assina e reage. Aqui, o relay assina `cmd_vel` e republica no mesmo tópico (com outro perfil QoS), e o Gazebo assina e move o robô.

---

## 4. Sensores no projeto

### 4.1 Odometria (`/odom`)

A **odometria** estima a pose do robô a partir das rodas (ou, na simulação, da física). O tópico `/odom` publica `nav_msgs/msg/Odometry`:

- **pose.pose:** posição (x, y, z) e orientação (quaternion).
- **twist.twist:** velocidades lineares e angulares.

No código do navigator, extraímos x, y e o ângulo \(\theta\) assim:

```python
# robot_sim/nodes/navigator.py (conceito)
p = self._odom.pose.pose.position   # x, y, z
q = self._odom.pose.pose.orientation  # quaternion
theta = math.atan2(
    2.0 * (q.w * q.z + q.x * q.y),
    1.0 - 2.0 * (q.y * q.y + q.z * q.z),
)
# (x, y, theta) é a pose 2D usada pelo PID e pelo planejamento
```

O **quaternion** representa a rotação 3D; para robô no plano, a fórmula acima obtém o yaw (\(\theta\)) em radianos. Com a pose atual e o waypoint (em metros no mesmo frame), o controlador PID calcula o Twist.

### 4.2 LaserScan (`/scan`)

O **LiDAR 2D** (ou sensor simulado) varre um plano e devolve distâncias em várias direções. A mensagem é `sensor_msgs/msg/LaserScan`:

- **angle_min, angle_max, angle_increment:** ângulos em radianos (em relação ao eixo x do robô).
- **range_min, range_max:** limites válidos da distância (m).
- **ranges:** lista de distâncias; o índice `i` corresponde ao ângulo `angle_min + i * angle_increment`.

Valores `nan` ou `inf` indicam “sem retorno” (céu, vidro, etc.). Para detectar obstáculos, usamos apenas leituras dentro de `[range_min, range_max]` e finitas.

**Exemplo no projeto:** o `obstacle_detector` usa só o setor frontal (por exemplo, ±60°) e publica a menor distância e um booleano “obstáculo próximo”:

```python
# robot_sim/nodes/obstacle_detector.py (trecho)
half_rad = math.radians(self._front_angle_deg)  # ex.: 60° em rad
min_dist = float('inf')
for i, r in enumerate(ranges):
    angle = angle_min + i * angle_increment
    if angle < -half_rad or angle > half_rad:
        continue
    if not (range_min <= r <= range_max):
        continue
    if math.isfinite(r):
        min_dist = min(min_dist, r)
# ...
self._pub_obstacle.publish(Bool(data=min_dist < self._min_distance))
```

Conceito: **setor frontal** = ângulos próximos de 0 (frente do robô). Filtrar por ângulo e por range evita usar ruído ou leituras inválidas. O limiar `min_distance` define “obstáculo próximo” para o navegador parar ou replanejar.

---

## 5. Controle

O **controle em malha fechada** compara o estado atual com o desejado (setpoint) e corrige o atuador (velocidade) para reduzir o **erro**.

### 5.1 O que é PID

**PID** = Proporcional + Integral + Derivativo:

- **P:** ação proporcional ao erro (quanto maior o erro, maior a correção).
- **I:** soma do erro no tempo (elimina erro residual constante).
- **D:** reação à taxa de variação do erro (amortece oscilações).

Fórmula típica:  
\( u = K_p\,e + K_i\int e\,dt + K_d\,\frac{de}{dt} \).

No nosso controlador temos dois “PIDs”: um para a **distância** ao waypoint (saída = velocidade linear) e outro para o **ângulo** até o waypoint (saída = velocidade angular). Assim o robô primeiro alinha a direção e depois avança.

### 5.2 Trecho do PID no projeto

O erro angular é o ângulo até o objetivo no plano, normalizado em \([-\pi,\pi]\):

```python
# robot_sim/pid_controller.py (trecho)
dx = goal_x - x
dy = goal_y - y
distance = math.hypot(dx, dy)
target_angle = math.atan2(dy, dx)
error_angular = self._normalize_angle(target_angle - theta)
```

- **target_angle:** direção do vetor (goal - posição atual).
- **error_angular:** diferença entre essa direção e a orientação atual do robô. O PID angular produz `angular.z` para reduzir esse erro.

O erro linear é a própria distância; o PID linear (com saturação e limite máximo) produz `linear.x`. Se o robô estiver muito desalinhado, a velocidade linear é reduzida para evitar curvas muito fechadas:

```python
if abs(error_angular) > 0.5:
    cmd_linear *= 0.3
cmd_linear = max(0.0, min(self.max_linear, cmd_linear))
```

Assim, o **conceito** é: **entrada** = pose (x, y, θ) + waypoint (gx, gy); **saída** = (linear.x, angular.z) limitados; o restante do nó só publica esse Twist em `/cmd_vel`.

---

## 6. Planejamento de caminho (A*)

O **grid de ocupação** divide o ambiente em células; cada célula é **livre** (0) ou **ocupada** (1). Obstáculos vêm do LaserScan (ou de um mapa) e são marcados como ocupados; opcionalmente “inflamos” obstáculos (marcamos vizinhas como ocupadas) para dar margem ao robô.

O **A*** é um algoritmo de busca em grafo que encontra um caminho de custo mínimo entre célula inicial e final:

- Mantém uma **fila de prioridade** (heap) ordenada por \(f = g + h\).
- **g:** custo real desde o início até o nó atual.
- **h:** **heurística** (estimativa do custo até o objetivo); usamos distância Euclidiana (admissível).
- Expande o nó com menor \(f\); quando o nó expandido é o objetivo, o caminho é reconstruído com `came_from`.

**Trecho do A* no projeto:**

```python
# robot_sim/astar.py (trecho)
# open_set: heap por f = g + h
heapq.heappush(open_set, (f_start, g_score[start], start))
# ...
while open_set:
    _, g_cur, current = heapq.heappop(open_set)
    if current == goal:
        # Reconstrói caminho com came_from
        path = []
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path
    for dr, dc in neighbors_deltas:
        nr, nc = current[0] + dr, current[1] + dc
        if not is_free(nr, nc):
            continue
        tentative_g = g_cur + step_cost
        if neighbor not in g_score or tentative_g < g_score[neighbor]:
            came_from[neighbor] = current
            g_score[neighbor] = tentative_g
            f_val = tentative_g + heuristic(neighbor, goal)
            heapq.heappush(open_set, (f_val, tentative_g, neighbor))
```

Conceito: **vizinhos** = 4 ou 8 células adjacentes; **step_cost** = 1 (cardeais) ou \(\sqrt{2}\) (diagonais). O grid é construído a partir do LaserScan no módulo `grid_builder` (scan → células ocupadas → inflação); o navigator converte pose e objetivo em células, chama A* e transforma o caminho de células de volta em waypoints em metros.

---

## 7. Navegação de ponta a ponta

O fluxo no **navigator** une sensores, planejamento e controle:

1. **Objetivo:** recebido por parâmetro (goal_x, goal_y) ou pelo tópico `/goal` (Point).
2. **Pose atual:** de `/odom`.
3. **Grid:** construído a partir de `/scan` (frame do robô), com origem no centro do robô; inflação de obstáculos.
4. **Células:** início = centro do grid; objetivo = (goal_x, goal_y) transformado para o frame do robô e depois para índice de célula.
5. **A*:** retorna lista de células (caminho).
6. **Waypoints:** células convertidas para coordenadas no mundo (odom) usando a pose no momento do planejamento.
7. **Execução:** para cada waypoint, o PID recebe (x, y, θ) e o waypoint (wx, wy), produz (linear.x, angular.z) e publica em `/cmd_vel`; quando o waypoint é atingido (tolerância), passa ao próximo.
8. **Obstáculos:** se `obstacle_detected` for true ou a distância mínima frontal (calculada do `/scan`) for menor que um limiar, o robô para (Twist zero).

Assim, **sensores** (odom + scan) → **grid** → **A*** → **waypoints** → **PID** → **cmd_vel**. O documento de início rápido e o README explicam como subir a simulação e o launch de navegação.

**Desvio automático (obstacle_avoider):** em vez de só parar e replanejar, o nó **obstacle_avoider** usa **setores** do laser (esquerda, centro, direita). Se o centro está livre além de uma distância segura, o robô avança (e opcionalmente corrige em direção a um objetivo em `/goal`). Se o centro está bloqueado, o robô gira para o lado mais livre (esquerda ou direita) e avança devagar. O comando é publicado em `/cmd_vel` ou em `cmd_vel_avoider` quando usado com o **cmd_vel_mixer** (teleop + desvio). Ver [ARQUITETURA.md](ARQUITETURA.md).

---

## 8. Trechos de código do projeto — resumo

| Arquivo / conceito | O que faz |
|-------------------|-----------|
| **scripts/cmd_vel_relay.py** | Publisher e subscriber de `Twist` em `cmd_vel`; repassa mensagens (ex.: para compatibilizar QoS com o Gazebo). Mostra o padrão pub/sub e o uso da mensagem Twist. |
| **robot_sim/nodes/obstacle_detector.py** | Assina `/scan`, filtra por ângulo (setor frontal) e range, calcula distância mínima e publica `min_obstacle_distance` e `obstacle_detected`. Ilustra leitura de LaserScan e decisão binária “obstáculo próximo”. |
| **robot_sim/pid_controller.py** | Dada pose (x, y, θ) e waypoint (gx, gy), calcula erro de distância e de ângulo, aplica PID (com integrais e derivadas limitadas) e retorna (linear.x, angular.z). Ilustra controle em malha fechada e normalização de ângulo. |
| **robot_sim/astar.py** | A* em grid 2D com heap, heurística Euclidiana e 4/8 vizinhos. Retorna lista de células do caminho. Ilustra busca em grafo e conversão mundo ↔ grid. |
| **robot_sim/grid_builder.py** | Converte `ranges` do LaserScan (ângulos e distâncias) em células ocupadas no frame do robô e aplica inflação. Ilustra sensores → representação espacial (grid). |
| **robot_sim/nodes/navigator.py** | Orquestra: lê odom e scan, monta grid, chama A*, converte path em waypoints em odom, usa PID para seguir waypoints e publica `/cmd_vel`; para se houver obstáculo. Ilustra o pipeline completo de navegação. |
| **robot_sim/nodes/obstacle_avoider.py** | Assina `/scan`, divide em setores (L/C/R), calcula distância mínima por setor; se centro livre avança (opcionalmente tendendo a `/goal`), senão gira para o lado mais livre e avança devagar. Publica `cmd_vel` ou `cmd_vel_avoider`. Ilustra controle reativo por setores. |
| **robot_sim/nodes/cmd_vel_mixer.py** | Assina `cmd_vel_teleop`, `cmd_vel_avoider` e `obstacle_detected`; republica avoider ou teleop em `/cmd_vel` conforme obstáculo. Ilustra prioridade de fontes de comando. |
| **robot_sim/nodes/vision_node.py** | Assina tópico de imagem, aplica máscara HSV para uma cor, encontra maior blob e publica centroide e opcionalmente `cmd_vel` para seguir o alvo. Ilustra visão → comando (seguimento de cor). |

**SLAM e Nav2:** o projeto inclui configs e launches para **slam_toolbox** (mapear) e **Nav2** (navegar com mapa); ver [SLAM.md](SLAM.md) e [NAV2.md](NAV2.md).

---

## 9. Referências

- [ROS 2 Humble Documentation](https://docs.ros.org/en/humble/)
- [TurtleBot3 Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/overview/)
- Livros de robótica móvel (ex.: *Introduction to Autonomous Mobile Robots*, Siegwart et al.) para teoria de odometria, planejamento e controle.

---

*Última atualização: mar. 2025 — Inclui obstacle_avoider, cmd_vel_mixer, vision_node, SLAM e Nav2.*
