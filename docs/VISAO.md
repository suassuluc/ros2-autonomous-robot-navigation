# Visão computacional — Seguimento de cor

O nó **vision_node** do robot_sim faz detecção de cor (HSV) na imagem e pode publicar o centroide do alvo e/ou comandos de velocidade (`cmd_vel`) para o robô seguir o alvo (ex.: bola vermelha).

---

## 1. Pré-requisitos

- Fonte de imagem publicando `sensor_msgs/msg/Image` (câmera no simulador ou USB).
- OpenCV e cv_bridge:

```bash
sudo apt install ros-humble-cv-bridge
pip install opencv-python
# ou: sudo apt install python3-opencv
```

No TurtleBot3 **burger** o mundo padrão do Gazebo não inclui câmera. Opções:

- **TurtleBot3 waffle_pi:** use um launch do Gazebo que inclua o modelo waffle_pi com câmera (se disponível no seu ambiente).
- **Câmera USB:** use o pacote `usb_cam` ou similar para publicar `/camera/image_raw`.
- **Bag ou nó de teste:** publique imagens em um tópico para testar o vision_node.

---

## 2. Parâmetros do vision_node

| Parâmetro           | Padrão              | Descrição |
|---------------------|---------------------|-----------|
| `image_topic`       | `camera/image_raw`  | Tópico da imagem. |
| `cmd_vel_topic`     | `cmd_vel`           | Tópico para publicar Twist (seguir alvo). |
| `publish_cmd_vel`   | `true`              | Se true, publica cmd_vel para seguir o alvo. |
| `target_hue_center`  | `0.0`               | Hue HSV do alvo (0 = vermelho em OpenCV). |
| `target_hue_range`  | `15.0`              | ± intervalo em hue. |
| `min_saturation`    | `80`                | Mínimo de saturação HSV. |
| `min_value`         | `80`                | Mínimo de value (brilho). |
| `min_area`          | `500`               | Área mínima do blob (pixels). |
| `max_linear`        | `0.2`               | Velocidade linear máxima ao seguir. |
| `max_angular`       | `0.8`               | Velocidade angular máxima. |

Para **verde**, use por exemplo `target_hue_center:=120` (e ajuste `target_hue_range` se necessário).

---

## 3. Como rodar

**Terminal 1 — Simulação (ou câmera):**  
Subir o mundo com câmera ou o nó que publica imagens.

**Terminal 2 — Vision node:**

```bash
source /opt/ros/humble/setup.bash
source /home/shini/ros2_ws/install/setup.bash
ros2 launch robot_sim vision.launch.py
```

Com tópico customizado:

```bash
ros2 launch robot_sim vision.launch.py image_topic:=/my_camera/image_raw
```

Apenas centroide (sem cmd_vel):

```bash
ros2 launch robot_sim vision.launch.py publish_cmd_vel:=false
```

---

## 4. Tópicos

| Tópico             | Tipo                | Descrição |
|--------------------|---------------------|-----------|
| `camera/image_raw` | `sensor_msgs/Image` | Entrada (ou o configurado em `image_topic`). |
| `vision/centroid`   | `std_msgs/Float32MultiArray` | Centroide normalizado [x, y] do maior blob. |
| `cmd_vel`          | `geometry_msgs/Twist` | Saída para seguir o alvo (se `publish_cmd_vel` true). |

---

## 5. Integração

- Com **teleop:** o vision_node e o teleop publicam no mesmo `cmd_vel`; use um mixer ou desative um deles por vez.
- Com **navegação:** pode desativar `publish_cmd_vel` e usar apenas `vision/centroid` para outro nó decidir o movimento.

---

*Última atualização: mar. 2025 — vision_node, seguimento de cor.*
