#!/bin/bash
# Script de diagnóstico para teleop_keyboard do TurtleBot3
# Uso: ./check_teleop.sh
# Execute em um terminal enquanto o teleop_keyboard está rodando em outro.

source /opt/ros/humble/setup.bash 2>/dev/null || true

echo "=========================================="
echo "  Diagnóstico do TurtleBot3 Teleop"
echo "=========================================="
echo ""

# 1. Variável TURTLEBOT3_MODEL
echo "1. Variável TURTLEBOT3_MODEL:"
if [ -z "$TURTLEBOT3_MODEL" ]; then
    echo "   [FALTA] TURTLEBOT3_MODEL não está definida!"
    echo "   Solução: export TURTLEBOT3_MODEL=burger   (ou waffle / waffle_pi)"
else
    echo "   [OK] TURTLEBOT3_MODEL=$TURTLEBOT3_MODEL"
fi
echo ""

# 2. Tópicos existentes
echo "2. Tópicos disponíveis (procurando cmd_vel):"
ros2 topic list | grep -E "cmd_vel|velocity" || echo "   Nenhum tópico cmd_vel ou velocity encontrado."
echo ""

# 3. Quem publica em cmd_vel
echo "3. Publicadores do tópico /cmd_vel:"
ros2 topic info /cmd_vel --verbose 2>/dev/null || echo "   O tópico /cmd_vel não existe (nenhum nó publicando ainda)."
echo ""

# 4. Quem assina cmd_vel (quem comanda o robô)
echo "4. Inscritos no tópico /cmd_vel (quem recebe os comandos):"
ros2 topic info /cmd_vel 2>/dev/null | grep -A 20 "Subscription" || echo "   Não foi possível listar inscritos."
echo ""

echo "=========================================="
echo "  Resumo"
echo "=========================================="
echo "- O teleop_keyboard PUBLICA em /cmd_vel quando você aperta WASD."
echo "- O robô (bringup, Gazebo ou seu nó) precisa ASSINAR /cmd_vel para se mover."
echo "- Se não houver assinante, os comandos são publicados mas ninguém os usa."
echo ""
