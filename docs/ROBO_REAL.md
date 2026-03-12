# Rodar a programação em um robô real

Este documento descreve como usar os mesmos nós do **robot_sim** (desvio de obstáculos, navegação A*+PID, teleop+avoider, SLAM, Nav2, visão) em um **robô real**, em vez da simulação no Gazebo.

## O que a programação espera

Os nós do `robot_sim` assumem que o robô expõe a mesma **interface** que a simulação:

| Tópico / TF        | Tipo / frame     | Quem fornece na simulação | No robô real                    |
|--------------------|------------------|---------------------------|----------------------------------|
| `/scan`            | `sensor_msgs/LaserScan` | Gazebo (plugin lidar)   | Driver do laser (LDS, RPLidar, etc.) |
| `/odom`            | `nav_msgs/Odometry`     | Gazebo (plugin diff_drive) | Driver que lê encoders / odometria |
| `/cmd_vel`         | `geometry_msgs/Twist`   | — (nós publicam aqui)   | Driver que **assina** e comanda as rodas |
| TF `odom` → `base_footprint` | —              | Plugin diff_drive         | Driver do robô                   |
| TF `base_footprint` → `base_link` | —           | static_transform_publisher | Driver ou seu launch             |
| TF `base_link` → `base_scan`      | —           | static_transform_publisher | Driver (pose do laser no chassi) |

Ou seja: no robô real você precisa de um **bringup** (driver) que:

- **Publique** `/scan` e `/odom`
- **Assine** `/cmd_vel` e envie os comandos para os motores
- **Publique** a árvore de TF (odom → base_footprint → base_link → base_scan)

Se isso estiver correto, você **não precisa mudar o código** do robot_sim: os mesmos launches e nós funcionam.

---

## Opção 1: TurtleBot3 real (Burger / Waffle / Waffle Pi)

O TurtleBot3 oficial usa ROS 2 e já expõe `/scan`, `/odom`, `/cmd_vel` e a TF no mesmo padrão.

### No robô (Raspberry Pi ou SBC)

1. Instale ROS 2 Humble e os pacotes do TurtleBot3 no robô (conforme [TurtleBot3 Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/overview/)).
2. Configure o modelo, por exemplo:
   ```bash
   export TURTLEBOT3_MODEL=burger
   ```
3. Suba o **bringup** do robô (OpenCR + LDS + base):
   ```bash
   ros2 launch turtlebot3_bringup robot.launch.py
   ```
   Isso sobe os nós que publicam `/scan`, `/odom` e que assinam `/cmd_vel`, além da TF.

### No seu computador (ou no próprio robô)

Com o bringup do TurtleBot3 rodando, use os **mesmos** launches do robot_sim que você usa na simulação:

```bash
source /opt/ros/humble/setup.bash
source /home/shini/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger

# Desvio automático
ros2 launch robot_sim avoider.launch.py

# Navegação A* + PID (objetivo em x,y)
ros2 launch robot_sim navigation.launch.py

# Teleop + desvio (teleop em outro terminal com remap)
ros2 launch robot_sim teleop_with_avoider.launch.py
# Em outro terminal:
ros2 run turtlebot3_teleop teleop_keyboard --ros-args -r cmd_vel:=cmd_vel_teleop

# SLAM (mapear o ambiente real)
ros2 launch robot_sim slam.launch.py

# Nav2 (com mapa já salvo)
ros2 launch robot_sim nav2.launch.py map:=/path/to/map.yaml
```

Ou seja: em vez de subir o Gazebo, você sobe o **bringup** do TurtleBot3; o resto da “programação” (robot_sim) é igual.

---

## Opção 2: Outro robô (não TurtleBot3)

Se o robô tiver:

- **Laser** que publica em algum tópico (ex.: `/laser_scan`)
- **Odometria** em outro tópico (ex.: `/wheel_odom`)
- **Controle** por velocidade em outro tópico (ex.: `/motor_cmd`)

você tem duas abordagens:

### A) O driver do robô usa os mesmos nomes

Se o fabricante ou seu driver já publicar `/scan`, `/odom` e assinar `/cmd_vel`, e publicar a TF `odom` → `base_footprint` → `base_link` → `base_scan`, pode usar os launches do robot_sim **sem alteração**.

### B) Usar remapeamento de tópicos

Se os nomes forem diferentes, crie um **launch de bringup** que sobe o driver do robô e nós que fazem **bridge** (republish/remap) para os nomes que o robot_sim espera, por exemplo:

- `/laser_scan` → `/scan`
- `/wheel_odom` → `/odom`
- `/cmd_vel` → `/motor_cmd` (ou o que o robô usar)

No ROS 2 isso pode ser feito com `topic_tools` (relay) ou com um launch que inicia os nós do driver com `--ros-args -r ...`. Assim, para o robot_sim continua existindo `/scan`, `/odom` e `/cmd_vel`.

---

## Onde rodar os nós (robô vs laptop)

- **Tudo no robô:** instale o workspace no SBC do robô, suba o bringup e os launches do robot_sim no mesmo máquina. Funciona com um único computador.
- **Bringup no robô, robot_sim no laptop:** no robô rode só o bringup (scan, odom, cmd_vel, TF). No laptop, na mesma rede, dê `source` do workspace e rode os launches do robot_sim. Desde que o ROS 2 (DDS) esteja na mesma rede e domínio, os tópicos e a TF serão compartilhados e o robô se moverá com os comandos do laptop.

Em ambos os casos, a “programação” que você sobe é a mesma; o que muda é só **quem** fornece `/scan`, `/odom` e quem consome `/cmd_vel` (simulação vs bringup real).

---

## Resumo

| Objetivo              | O que fazer |
|-----------------------|-------------|
| TurtleBot3 real       | No robô: `ros2 launch turtlebot3_bringup robot.launch.py`. No PC ou no robô: os mesmos `robot_sim` launches (avoider, navigation, slam, nav2, etc.). |
| Outro robô            | Garantir que existam `/scan`, `/odom`, assinante de `/cmd_vel` e TF; usar remapeamento/bridge se os nomes forem diferentes. |
| Onde rodar            | Bringup no robô; robot_sim pode rodar no robô ou no laptop, desde que na mesma rede ROS 2. |

Assim você “sobe” a mesma programação para o robô real: em vez de Gazebo, sobe o bringup do robô e continua usando os mesmos launches e nós do robot_sim.
