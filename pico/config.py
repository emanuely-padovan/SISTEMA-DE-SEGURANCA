# config.py — Aula 10: MQTT + Dashboard IoT
# SENAI Ítalo Bologna — Curso Técnico em Desenvolvimento de Sistemas
#
# ⚠️ Cada aluno/grupo muda:
#   BROKER_IP  → IP do notebook que roda o Mosquitto (use ipconfig)
#   CLIENT_ID  → nome único do grupo (ex: pico_grupo1)
#   TOPIC_PUB  → tópico de publicação (ex: senai/grupo1/sensores)
#   TOPIC_SUB  → tópico de comandos (ex: senai/grupo1/comandos)

WIFI_SSID   = "WIFI_IOT"
WIFI_PASS   = "Ac1ce2ss5@IOT"

BROKER_IP   = "10.132.112.5"        # ← IP do notebook broker (ipconfig)
BROKER_PORT = 1883                    # TCP direto — para o Pico

CLIENT_ID   = "pico_grupo2"          # ← nome único do grupo
TOPIC_PUB   = "senai/grupo2/sensores" # ← tópico que o Pico publica
TOPIC_SUB   = "senai/grupo2/comandos" # ← tópico que o Pico assina (novo!)
