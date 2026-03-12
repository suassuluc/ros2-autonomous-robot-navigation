# ros2_ws — Projeto de robótica (portfólio)

Workspace ROS 2 com o robô **TurtleBot3** em simulação (Gazebo): controle por teclado (teleop), **desvio automático de obstáculos**, **navegação autônoma** (A* + PID e Nav2), **SLAM** (slam_toolbox), **visão computacional** (seguimento de cor) e documentação de uso.

## Stack / tecnologias

- **ROS 2 Humble** — middlewares, tópicos, launch
- **Gazebo** — simulação do TurtleBot3
- **Python (rclpy)** — nós: obstacle_detector, navigator, obstacle_avoider, cmd_vel_mixer, vision_node
- **slam_toolbox** — mapeamento 2D em tempo real
- **Nav2** — navegação autônoma com mapa (AMCL, planner, controller, costmaps)
- **OpenCV / cv_bridge** — processamento de imagem (visão)

## Documentação

| Doc | Conteúdo |
|-----|----------|
| [Como começar](docs/GETTING_STARTED.md) | Instalação, ambiente, simulação, teleop, navegação, SLAM, Nav2, visão |
| [Preceitos básicos](docs/PRECEITOS_BASICOS.md) | Conceitos (coordenadas, diferencial, sensores, PID, A*) e explicação do código |
| [Problemas comuns (teleop)](docs/TELEOP_TURTLEBOT3.md) | Teleop não inicia, robô parado, QoS, diagnóstico |
| *[Como começar](docs/GETTING_STARTED.md#14-se-o-robô-cair-na-simulação-turtlebot3-de-2-rodas)* | **Robô caiu e não se mexe** — reiniciar simulação |
| [Obstáculos na simulação](docs/OBSTACULOS_SIMULACAO.md) | Coordenadas no turtlebot3_world, /scan e /odom |
| [SLAM](docs/SLAM.md) | Mapear ambiente com slam_toolbox e salvar mapa |
| [Nav2](docs/NAV2.md) | Navegação autônoma com mapa (goal no RViz, AMCL) |
| [Visão](docs/VISAO.md) | Seguimento de cor (vision_node), tópicos e parâmetros |
| [Arquitetura](docs/ARQUITETURA.md) | Nós, tópicos e fluxo do sistema |
| [Exploração (ciclo de movimento)](docs/EXPLORACAO.md) | Objetivos aleatórios a cada N min para variar a rota em ~20 min |
| [Robô real](docs/ROBO_REAL.md) | Como rodar a mesma programação em um TurtleBot3 ou outro robô real |

## Funcionalidades

| Funcionalidade | Descrição | Como rodar |
|----------------|-----------|------------|
| Teleop | Controle por teclado (WASD) | `ros2 run turtlebot3_teleop teleop_keyboard` |
| Detecção de obstáculos | LaserScan → min_obstacle_distance, obstacle_detected | Incluído em `navigation.launch.py` e `teleop_with_avoider` |
| Desvio automático | Nó que desvia ativamente (setores L/C/R) | `ros2 launch robot_sim avoider.launch.py` |
| **Desvio + exploração (ciclo)** | Novos objetivos a cada N min; robô varia a rota e percorre mais o mapa em ~20 min | `ros2 launch robot_sim avoider_exploration.launch.py` |
| Teleop + desvio | Mixer: teleop ou avoider conforme obstáculo | `ros2 launch robot_sim teleop_with_avoider.launch.py` + teleop com remap |
| Navegação A* + PID | Objetivo em (x,y), planeja e segue waypoints | `ros2 launch robot_sim navigation.launch.py` |
| SLAM | Mapear ambiente em tempo real | `ros2 launch robot_sim slam.launch.py` + teleop |
| Nav2 | Navegação com mapa (goal no RViz) | `ros2 launch robot_sim nav2.launch.py map:=<path>` |
| Visão (seguimento de cor) | Detecção HSV e cmd_vel para seguir alvo | `ros2 launch robot_sim vision.launch.py` (requer câmera) |
| **Simulação com casa (opcional)** | Mundo TurtleBot3 + modelo da casa (spawn opcional) | `ros2 launch robot_sim turtlebot3_world_delayed.launch.py spawn_house:=true` |

## Estrutura

| Pasta / arquivo | Descrição |
|-----------------|-----------|
| `src/robot_sim/` | Pacote: nós, configs (SLAM, Nav2), launches |
| `docs/` | Documentação (getting started, preceitos, SLAM, Nav2, visão, arquitetura) |
| `scripts/` | Scripts auxiliares (`check_teleop.sh`, `cmd_vel_relay.py`) |
| `maps/` | (Criar e salvar mapas aqui com map_saver_cli) |

## Início rápido

**Importante:** `export TURTLEBOT3_MODEL=burger` no terminal (ou no `~/.bashrc`) antes de qualquer launch.

```bash
# Terminal 1: simulação
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# Terminal 2: teleop
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard
# WASD = mover; S ou Espaço = parar
```

**Navegação autônoma (A* + PID):**

```bash
# Com simulação já rodando:
source /opt/ros/humble/setup.bash
source /home/shini/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch robot_sim navigation.launch.py
# Objetivo padrão (2, 0); ou goal_x:=1.5 goal_y:=0.5
```

**Desvio automático (só avoider):**

```bash
ros2 launch robot_sim avoider.launch.py
```

**SLAM (mapear):** ver [docs/SLAM.md](docs/SLAM.md).  
**Nav2 (navegar com mapa):** ver [docs/NAV2.md](docs/NAV2.md).  
**Visão:** ver [docs/VISAO.md](docs/VISAO.md).

**Simulação com casa (opcional):** use o launch com spawn atrasado e, se quiser o modelo da casa no mundo:
```bash
ros2 launch robot_sim turtlebot3_world_delayed.launch.py spawn_house:=true
```

---

