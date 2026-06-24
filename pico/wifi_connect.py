# wifi_connect.py — Aula 10: MQTT + Dashboard IoT
# Arquivo reutilizado da Aula 9 — sem alterações
# Responsável pela conexão WiFi do Pico 2W

import network
from utime import sleep

def conectar_wifi(ssid, senha, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print(f"[WiFi] Já conectado. IP: {wlan.ifconfig()[0]}")
        return True

    print(f"[WiFi] Conectando em '{ssid}'", end="")
    wlan.connect(ssid, senha)

    while not wlan.isconnected() and timeout > 0:
        sleep(1)
        timeout -= 1
        print(".", end="")

    print()

    if wlan.isconnected():
        ip, _, gateway, _ = wlan.ifconfig()
        print(f"[WiFi] Conectado! IP do Pico: {ip}")
        return True
    else:
        print("[WiFi] ERRO: não conectou. Verifique SSID e senha.")
        return False
