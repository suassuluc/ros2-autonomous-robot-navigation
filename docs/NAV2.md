# Nav2 — Navegação autônoma

Este documento descreve como usar o **Nav2** para navegação autônoma do TurtleBot3 em simulação, com um mapa já construído via SLAM (ver [SLAM.md](SLAM.md)).

---

## 1. Pré-requisitos

- Mapa gerado e salvo (PGM + YAML), por exemplo em `~/ros2_ws/maps/my_map.yaml`.
- Pacotes instalados:

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup
```

Compile o workspace:

```bash
cd /home/shini/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select robot_sim
source install/setup.bash
```

---

## 2. Subir simulação e Nav2

**Terminal 1 — Simulação (Gazebo):**

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

**Terminal 2 — Nav2 (indique o caminho do mapa):**

```bash
source /opt/ros/humble/setup.bash
source /home/shini/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch robot_sim nav2.launch.py map:=/home/shini/ros2_ws/maps/my_map.yaml
```

Ajuste o caminho `map:=` para o seu arquivo YAML do mapa. O Nav2 sobe o map_server, AMCL, controller, planner e behavior server.

---

## 3. Enviar objetivo de navegação

**Opção A — RViz2 (recomendado):**

1. Abra o RViz2:
   ```bash
   ros2 run rviz2 rviz2
   ```
2. Fixe o **Fixed Frame** em `map`.
3. Adicione **Map** (topic `/map`), **RobotModel**, **TF**, **PoseArray** (topic `/particle_cloud` para AMCL).
4. Use **“2D Goal Pose”** para enviar o objetivo: o robô planeja e navega até o ponto.

**Opção B — Linha de comando (goal em coordenadas do mapa):**

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 0.5, z: 0.0}, orientation: {w: 1.0}}}}"
```

---

## 4. Localização inicial (AMCL)

O AMCL precisa de uma pose inicial no mapa. No RViz2 você pode usar **“2D Pose Estimate”** para informar onde o robô está. Se a simulação começa sempre na mesma posição do mundo, uma única definição pode ser suficiente.

---

## 5. Resumo

| Item        | Descrição |
|------------|-----------|
| Mapa       | Gerado com SLAM ([SLAM.md](SLAM.md)); salvo com `map_saver_cli`. |
| Launch     | `ros2 launch robot_sim nav2.launch.py map:=<caminho>.yaml` |
| Goal       | RViz2 “2D Goal Pose” ou action `NavigateToPose`. |
| Frames     | `map`, `odom`, `base_footprint` / `base_link`. |

O navegador custom (A* + PID) do robot_sim continua disponível via `navigation.launch.py`; use o Nav2 quando quiser planejamento global, costmaps e recuperação automática.

---

*Última atualização: mar. 2025 — Nav2, TurtleBot3 Gazebo.*
