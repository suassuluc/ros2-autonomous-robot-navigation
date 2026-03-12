# Por que o teleop_keyboard não move o robô?

**Simulação abre sem o robô (só o mundo/mapa)?** Defina `export TURTLEBOT3_MODEL=burger` no mesmo terminal antes do launch. Ver [GETTING_STARTED.md](GETTING_STARTED.md) — seção “Problemas: simulação abre sem o robô”.

O `ros2 run turtlebot3_teleop teleop_keyboard` publica comandos no tópico **`/cmd_vel`** (tipo `geometry_msgs/msg/Twist`). O robô só se move se **algum nó estiver inscrito nesse tópico** e enviando os comandos para os motores (ou para o simulador).

## Causas comuns

### 1. Variável `TURTLEBOT3_MODEL` não definida

O script do teleop **exige** essa variável. Sem ela, o nó pode falhar ao iniciar.

**Solução:** antes de rodar o teleop, execute:

```bash
export TURTLEBOT3_MODEL=burger
```

(Use `burger`, `waffle` ou `waffle_pi` conforme seu modelo.)

Para deixar permanente, adicione a linha no `~/.bashrc`.

---

### 2. Nenhum nó “comandando” o robô (ninguém assina `/cmd_vel`)

O teleop só **publica** em `/cmd_vel`. Quem faz o robô se mover é outro nó que **assina** `/cmd_vel` e envia velocidade para:

- **Robô real:** firmware/OpenCR (via USB, etc.)
- **Simulação (Gazebo):** plugin `diff_drive` do modelo do TurtleBot3

Se esse nó não estiver rodando, o teleop funciona (WASD publica), mas o robô não se mexe.

**Robô real:** no próprio TurtleBot3 você precisa subir o bringup, por exemplo:

```bash
ros2 launch turtlebot3_bringup turtlebot3_robot.launch.py
```

(Deixe rodando em um terminal; no outro rode o teleop.)

**Simulação Gazebo:** suba o mundo e o spawn do TurtleBot3 com o launch oficial (ex.: `turtlebot3_gazebo`). O modelo do robô no Gazebo já vem com plugin que assina `/cmd_vel`.

**Seu próprio robô/simulação:** é preciso ter um nó (ou plugin) que assine `/cmd_vel` e envie as velocidades para os motores ou para o simulador.

---

### 3. Namespace diferente

Se o seu robô estiver em um namespace (ex.: `/robot1/cmd_vel`), o teleop continua publicando em `/cmd_vel`. Aí ou você:

- Remapeia o tópico ao rodar o teleop, ou  
- Faz um nó “ponte” que assina `/cmd_vel` e republica em `/robot1/cmd_vel`.

---

### 4. Terminal do teleop não em foco

O teleop lê as teclas **apenas** do terminal onde ele está rodando. As teclas WASD só têm efeito quando esse terminal está em foco (janela ativa).

---

## Como conferir

1. **Ver se o teleop está publicando**

   Em outro terminal (com o teleop rodando e o terminal do teleop em foco, apertando W por exemplo):

   ```bash
   ros2 topic echo /cmd_vel
   ```

   Você deve ver mensagens `linear.x` e `angular.z` mudando ao usar WASD.

2. **Ver quem está inscrito em `/cmd_vel`**

   ```bash
   ros2 topic info /cmd_vel -v
   ```

   Na parte “Subscription count” / lista de assinantes: se for 0, nenhum nó está “comandando” o robô com esse tópico.

3. **Script de diagnóstico**

   No workspace há um script que verifica variáveis e tópicos:

   ```bash
   chmod +x /home/shini/ros2_ws/scripts/check_teleop.sh
   /home/shini/ros2_ws/scripts/check_teleop.sh
   ```

---

## Resumo

| O que você quer              | O que fazer |
|-----------------------------|-------------|
| Teleop não inicia / dá erro | Definir `export TURTLEBOT3_MODEL=burger` (ou seu modelo). |
| Teleop roda mas robô parado | Subir bringup (robô real) ou simulação Gazebo com TurtleBot3; ou ter um nó seu que assina `/cmd_vel` e comanda motores/simulação. |
| Robô em namespace           | Remapear tópico ou fazer ponte `/cmd_vel` → `/<namespace>/cmd_vel`. |

Se você disser se está usando **robô real**, **Gazebo** ou **outro simulador/robô**, dá para indicar o comando exato de launch e o nó que deve assinar `/cmd_vel`.

---

## Terminal mostra movimento, mas o robô na simulação não se mexe

Se o teleop está rodando, o terminal mostra as velocidades ao apertar WASD, e mesmo assim o modelo no Gazebo fica parado, confira o seguinte.

### 1. Simulação em execução (não pausada)

No **Gazebo**, a física só roda com a simulação **em play**. Se estiver pausada, o robô não se move mesmo recebendo `/cmd_vel`.

- **Gazebo Classic:** barra inferior da janela do Gazebo — botão **Play** (triângulo). Se estiver pausado (ícone de pause), clique em Play.
- **Gazebo (Ignition/Gz Sim):** no painel de controle do mundo, verifique se a simulação está rodando (não pausada).

### 2. Teste direto no tópico

Com a simulação **rodando** (play), em outro terminal:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

O robô deve andar um pouco para a frente. Se **não se mover** com esse comando, o problema não é o teleop, e sim a simulação ou o plugin `diff_drive`.

### 3. Incompatibilidade de QoS (ROS 2)

Em ROS 2, publicador e assinante precisam ter QoS compatível. O teleop usa **RELIABLE**; alguns plugins do Gazebo usam **BEST_EFFORT**. Se os perfis não baterem, as mensagens não chegam e o robô fica parado.

**Teste com relay (BEST_EFFORT):** use o script de relay no workspace (veja abaixo). Ele assina `/cmd_vel` e republica em `/cmd_vel` com perfil mais permissivo, para testar se o problema é QoS.

### 4. Conferir se o plugin está recebendo

- Ver assinantes: `ros2 topic info /cmd_vel -v` — deve aparecer o nó do plugin (ex.: `turtlebot3_diff_drive`).
- Ver odometria: `ros2 topic echo /odom` — com a simulação em play e você publicando em `/cmd_vel`, os valores de `/odom` devem mudar. Se `/odom` não mudar, o plugin pode não estar recebendo `/cmd_vel` (por exemplo por QoS).

### 5. Relay de cmd_vel (ponte opcional)

O script `scripts/cmd_vel_relay.py` republica `/cmd_vel` (QoS RELIABLE). Pode ser útil como ponte em alguns cenários. Uso:

```bash
source /opt/ros/humble/setup.bash
python3 /home/shini/ros2_ws/scripts/cmd_vel_relay.py
```

Mantenha o teleop rodando no outro terminal.
