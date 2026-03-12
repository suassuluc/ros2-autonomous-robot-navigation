# TurtleBot3 no ROS 2 — Guia de início

Documentação do que está configurado até agora: como instalar, configurar o ambiente, iniciar a simulação e fazer o robô se mover com o teleop.

---

## 1. O que instalar

- **ROS 2 Humble** (ou outra distro compatível)
- **Pacotes do TurtleBot3** para simulação e teleop:

```bash
sudo apt update
sudo apt install ros-humble-turtlebot3*
```

Ou apenas os necessários:

```bash
sudo apt install ros-humble-turtlebot3-gazebo
sudo apt install ros-humble-turtlebot3-teleop
```

- **Gazebo** (geralmente já vem com os pacotes acima ou com o ROS 2)

Para conferir se os pacotes estão instalados:

```bash
source /opt/ros/humble/setup.bash
ros2 pkg list | grep turtlebot3
```

---

## 2. Configuração do ambiente

Antes de rodar a simulação ou o teleop, defina o modelo do robô:

```bash
export TURTLEBOT3_MODEL=burger
```

Opções: `burger`, `waffle`, `waffle_pi`. Para uso com o mundo padrão do TurtleBot3, `burger` é o mais comum.

Para não precisar exportar toda vez, adicione ao `~/.bashrc`:

```bash
echo 'export TURTLEBOT3_MODEL=burger' >> ~/.bashrc
source ~/.bashrc
```

---

## 3. Como iniciar a simulação (Gazebo)

O robô só é spawnado se a variável **`TURTLEBOT3_MODEL`** estiver definida **no mesmo terminal** (e antes) do comando de launch. Sem isso, o mundo abre mas o robô não aparece.

Em **um terminal**:

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger

ros2 launch turtlebot3_gazebo empty_world.launch.py
```

Isso sobe o Gazebo com um mundo vazio e spawna o TurtleBot3. Aguarde a janela do Gazebo abrir e o robô aparecer.

**Importante:** na barra inferior do Gazebo, o botão **Play** (triângulo) precisa estar ativo. Se estiver pausado, o robô não se move mesmo recebendo comandos.

### Mundos disponíveis

- **Mundo vazio:** `empty_world.launch.py` — apenas o chão e o robô.
- **Mundo com mapa:** `turtlebot3_world.launch.py` — ambiente com obstáculos e o robô.

Em ambos, use sempre `export TURTLEBOT3_MODEL=burger` antes do launch:

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Se o robô não aparecer, veja a seção **“Problemas: simulação abre sem o robô”** mais abaixo.

---

## 4. Como iniciar o teleop (controle por teclado)

Com a simulação já rodando, abra **outro terminal** e rode:

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger

ros2 run turtlebot3_teleop teleop_keyboard
```

O terminal do teleop deve mostrar as instruções de teclas. **Mantenha esse terminal em foco** quando for usar WASD; as teclas só funcionam na janela ativa.

---

## 5. Como controlar o robô

| Tecla | Ação |
|-------|------|
| **w** | Aumentar velocidade para frente |
| **x** | Aumentar velocidade para trás |
| **a** | Girar para a esquerda |
| **d** | Girar para a direita |
| **s** ou **Espaço** | **Parar** (zera linear e angular) |

O teleop mantém o último comando até você mandar parar. Para o robô parar de girar ou de andar, use **s** ou **Espaço**.

---

## 6. Sequência rápida (resumo)

1. **Terminal 1 — Simulação**
   ```bash
   source /opt/ros/humble/setup.bash
   export TURTLEBOT3_MODEL=burger
   ros2 launch turtlebot3_gazebo empty_world.launch.py
   ```
   Esperar o Gazebo abrir e conferir se o **Play** está ativo.

2. **Terminal 2 — Teleop**
   ```bash
   source /opt/ros/humble/setup.bash
   export TURTLEBOT3_MODEL=burger
   ros2 run turtlebot3_teleop teleop_keyboard
   ```
   Clicar na janela do teleop e usar **W A S D** para mover; **s** ou **Espaço** para parar.

---

## 7. Navegação autônoma (robot_sim)

O pacote **robot_sim** do workspace implementa navegação autônoma: detecção de obstáculos (LaserScan), planejamento de rota (A*) e controle PID até um objetivo.

**Compilar o workspace:**

```bash
cd /home/shini/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select robot_sim
source install/setup.bash
```

**Rodar a navegação autônoma:**

1. **Terminal 1 — Simulação** (mundo com obstáculos é ideal para testar A*):
   ```bash
   source /opt/ros/humble/setup.bash
   export TURTLEBOT3_MODEL=burger
   ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
   ```

2. **Terminal 2 — Navegação** (após o Gazebo e o robô estarem visíveis):
   ```bash
   source /opt/ros/humble/setup.bash
   source /home/shini/ros2_ws/install/setup.bash
   export TURTLEBOT3_MODEL=burger
   ros2 launch robot_sim navigation.launch.py
   ```
   O robô tentará ir até o objetivo padrão (2.0, 0.0) em metros. Para outro objetivo:
   ```bash
   ros2 launch robot_sim navigation.launch.py goal_x:=1.5 goal_y:=0.5
   ```

3. **Enviar objetivo por tópico** (com o navigator já rodando):
   ```bash
   ros2 topic pub --once /goal geometry_msgs/msg/Point "{x: 1.0, y: 0.5, z: 0.0}"
   ```

O navegador usa `/odom`, `/scan` e publica em `/cmd_vel`. O nó `obstacle_detector` publica em `min_obstacle_distance` e `obstacle_detected`. Conceitos (PID, A*, sensores) estão explicados em [PRECEITOS_BASICOS.md](PRECEITOS_BASICOS.md).

---

## 8. Desvio automático de obstáculos (obstacle_avoider)

O nó **obstacle_avoider** desvia ativamente de obstáculos usando setores do laser (esquerda, centro, direita) e publica `cmd_vel`.

**Só desvio (robô “anda sozinho” desviando):**

```bash
# Com simulação rodando
ros2 launch robot_sim avoider.launch.py
```

**Teleop com camada de desvio (mixer):** quando há obstáculo próximo o mixer usa o avoider; senão usa o teleop. O teleop deve publicar em `cmd_vel_teleop`:

```bash
# Terminal 1: simulação
# Terminal 2: mixer + obstacle_detector + avoider
ros2 launch robot_sim teleop_with_avoider.launch.py
# Terminal 3: teleop com remap
ros2 run turtlebot3_teleop teleop_keyboard --ros-args -r cmd_vel:=cmd_vel_teleop
```

**Ciclo de exploração (variar a rota em ~20 min):** para o robô não ficar na mesma rota o tempo todo, use o launch que combina desvio + objetivos aleatórios. A cada 2 min (configurável) o robô recebe um novo objetivo e tende a ir até lá, desviando de obstáculos:

```bash
ros2 launch robot_sim avoider_exploration.launch.py
# Novo objetivo a cada 3 min (mais rotas em 20 min): goal_interval_sec:=180
```

Parâmetros: `goal_interval_sec` (segundos entre objetivos), `use_relative_goals` (true = direção aleatória à frente), `relative_min_dist` / `relative_max_dist` (distância do objetivo em metros).

Detalhes em [README.md](../README.md) e [ARQUITETURA.md](ARQUITETURA.md).

---

## 9. SLAM (mapear o ambiente)

Para construir um mapa 2D com **slam_toolbox** e depois usar com Nav2:

1. Suba a simulação (ex.: `turtlebot3_world`).
2. Suba o SLAM: `ros2 launch robot_sim slam.launch.py`
3. Dirija o robô com o teleop por todo o ambiente.
4. Salve o mapa: `ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/maps/my_map`

Instalação: `sudo apt install ros-humble-slam-toolbox ros-humble-nav2-map-server`. Guia completo em [SLAM.md](SLAM.md).

---

## 10. Nav2 (navegação com mapa)

Com um mapa já salvo (ver seção 9), use o Nav2 para navegação autônoma (goal pelo RViz ou action):

```bash
# Simulação já rodando
ros2 launch robot_sim nav2.launch.py map:=/home/shini/ros2_ws/maps/my_map.yaml
```

No RViz2, use **“2D Goal Pose”** para enviar o objetivo. Instalação: `sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup`. Guia em [NAV2.md](NAV2.md).

---

## 11. Visão computacional (seguimento de cor)

O **vision_node** detecta uma cor (ex.: vermelho) na imagem e pode publicar `cmd_vel` para seguir o alvo. Requer um tópico de imagem (ex.: câmera do waffle_pi ou USB).

```bash
ros2 launch robot_sim vision.launch.py
# Ou com tópico customizado:
ros2 launch robot_sim vision.launch.py image_topic:=/camera/image_raw
```

Parâmetros (cor, ganhos) e dependências em [VISAO.md](VISAO.md).

---

## 12. Scripts e documentação extra no workspace

- **Diagnóstico do teleop**  
  Verifica `TURTLEBOT3_MODEL`, tópico `/cmd_vel` e quem publica/assina:
  ```bash
  /home/shini/ros2_ws/scripts/check_teleop.sh
  ```

- **Relay de cmd_vel** (opcional, para testes de conectividade):
  ```bash
  python3 /home/shini/ros2_ws/scripts/cmd_vel_relay.py
  ```

- **Problemas comuns (teleop não move, robô parado na simulação, etc.):**  
  Ver [TELEOP_TURTLEBOT3.md](TELEOP_TURTLEBOT3.md) neste mesmo diretório.

- **Preceitos básicos de robótica e do projeto:**  
  [PRECEITOS_BASICOS.md](PRECEITOS_BASICOS.md) — conceitos, sensores, PID, A* e explicação dos trechos de código.

- **SLAM, Nav2 e visão:** [SLAM.md](SLAM.md), [NAV2.md](NAV2.md), [VISAO.md](VISAO.md). **Arquitetura:** [ARQUITETURA.md](ARQUITETURA.md).

---

## 13. Se o robô cair na simulação (TurtleBot3 de 2 rodas)

O TurtleBot3 Burger tem só 2 rodas e um castor; em sessões longas ou após um choque ele pode **tombar** e não conseguir se levantar. Quando isso acontecer:

### Opção 1 — Reiniciar a simulação (recomendado)

1. No **terminal onde está rodando o launch do Gazebo** (ex.: `turtlebot3_world.launch.py`), pressione **Ctrl+C** para encerrar.
2. Suba de novo o mesmo launch. O robô volta à posição inicial e a simulação recomeça.

   ```bash
   export TURTLEBOT3_MODEL=burger
   ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
   ```

3. Nos outros terminais (teleop, avoider, etc.): se os nós pararam por perda de conexão, inicie-os de novo. Se continuaram rodando, eles passam a comandar o robô de novo assim que o Gazebo estiver de pé.

### Opção 2 — Resetar só a simulação (se existir o serviço)

Em alguns ambientes o Gazebo expõe um serviço para voltar ao estado inicial **sem fechar o launch**:

```bash
ros2 service call /reset_simulation std_srvs/srv/Empty
```

(O nome exato pode ser `/gzserver/reset_simulation` ou outro, conforme a versão do `gazebo_ros`.) Se o serviço não existir (`Unknown service`), use a Opção 1.

---

## 14. Problemas: simulação abre sem o robô

Se o Gazebo abre (vazio ou com o mapa) mas **o robô não aparece**, a causa mais comum é a variável **`TURTLEBOT3_MODEL`** não estar definida no momento do launch. O script que faz o spawn do robô usa essa variável; sem ela, o spawn falha e só o mundo é carregado.

**Solução:**

1. Defina a variável **no mesmo terminal** em que vai rodar o launch, **antes** do comando:
   ```bash
   export TURTLEBOT3_MODEL=burger
   ros2 launch turtlebot3_gazebo empty_world.launch.py
   ```
   Ou, para o mundo com mapa:
   ```bash
   export TURTLEBOT3_MODEL=burger
   ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
   ```

2. Para não precisar exportar toda vez, coloque no `~/.bashrc`:
   ```bash
   echo 'export TURTLEBOT3_MODEL=burger' >> ~/.bashrc
   source ~/.bashrc
   ```
   Depois disso, qualquer novo terminal já terá a variável definida.

Se mesmo assim o robô não aparecer, confira no terminal se aparece algum erro ao subir o launch (por exemplo relacionado a `spawn_entity` ou ao modelo). Em alguns casos o spawn pode rodar antes do servidor do Gazebo estar pronto; fechar tudo e rodar o launch de novo costuma resolver.

---

## 15. Robô real (fora da simulação)

Se for usar um TurtleBot3 físico:

1. No **próprio robô** (ou no computador que fala com ele), suba o bringup:
   ```bash
   export TURTLEBOT3_MODEL=burger
   ros2 launch turtlebot3_bringup turtlebot3_robot.launch.py
   ```
2. No seu PC (ou em outro terminal), rode o teleop como na seção 4.  
3. Certifique-se de que a rede e o `ROS_DOMAIN_ID` (se usado) estão corretos para os dois lados.

---

*Última atualização: mar. 2025 — ROS 2 Humble, TurtleBot3 em simulação (Gazebo), robot_sim (navegação, desvio, SLAM, Nav2, visão).*
