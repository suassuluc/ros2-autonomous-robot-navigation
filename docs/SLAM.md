# SLAM — Mapeamento do ambiente

Este documento descreve como gerar um mapa 2D do ambiente usando **slam_toolbox** com o TurtleBot3 em simulação (Gazebo). O mapa é usado depois pela navegação Nav2 (ver [NAV2.md](NAV2.md)).

---

## 1. Pré-requisitos

Instale o slam_toolbox e o Nav2 (para salvar o mapa):

```bash
sudo apt update
sudo apt install ros-humble-slam-toolbox ros-humble-nav2-map-server
```

Compile o workspace para instalar o config e o launch do robot_sim:

```bash
cd /home/shini/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select robot_sim
source install/setup.bash
```

---

## 2. Subir a simulação e o SLAM

**Terminal 1 — Simulação (Gazebo com mundo que deseja mapear):**

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Aguarde o Gazebo e o robô estarem visíveis.

**Terminal 2 — SLAM:**

```bash
source /opt/ros/humble/setup.bash
source /home/shini/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch robot_sim slam.launch.py
```

**Terminal 3 — Teleop (para dirigir o robô e mapear):**

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard
```

Use **W A S D** para mover o robô por todo o ambiente. O slam_toolbox publica o mapa no tópico `/map` e a transformada `map -> odom`.

---

## 3. Visualizar o mapa (opcional)

Com RViz2:

```bash
ros2 run rviz2 rviz2
```

- Adicione **Map** e defina o topic para `/map`.
- Adicione **TF** para ver os frames.
- Fixe o frame em `map` ou `odom`.

---

## 4. Salvar o mapa

Quando terminar de mapear, salve o mapa em arquivos PGM e YAML (para uso com Nav2):

```bash
cd /home/shini/ros2_ws
mkdir -p maps
ros2 run nav2_map_server map_saver_cli -f maps/my_map
```

Isso gera `my_map.pgm` e `my_map.yaml` na pasta `maps/`. O arquivo YAML contém a resolução, origem e nome da imagem. Use esse mapa no launch do Nav2 (ver [NAV2.md](NAV2.md)).

---

## 5. Frames e tópicos

| Item        | Valor              |
|------------|--------------------|
| Frame do mapa | `map`           |
| Frame odom  | `odom`             |
| Base do robô | `base_footprint`  |
| Tópico do laser | `/scan`      |
| Tópico do mapa | `/map`        |

O slam_toolbox publica a transformada `map -> odom`; o Gazebo (ou o driver do robô) publica `odom -> base_footprint`. Assim a cadeia completa para navegação fica: `map -> odom -> base_footprint`.

---

*Última atualização: mar. 2025 — slam_toolbox, TurtleBot3 Gazebo.*
