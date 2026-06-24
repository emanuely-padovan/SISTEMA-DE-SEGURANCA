# main.py — Aula 10: MQTT + Dashboard IoT
# SENAI Ítalo Bologna — Curso Técnico em Desenvolvimento de Sistemas

from config import *
from wifi_connect import conectar_wifi
from umqtt.simple import MQTTClient

from dht import DHT22
from machine import Pin, ADC, I2C
from utime import sleep, sleep_ms

from pico_i2c_lcd import I2cLcd
from picozero import Speaker

# ─── CONFIGURAÇÃO DO DISPLAY LCD ─────────────────────────────────────────────

i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)
I2C_ADDR = i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

lcd.clear()
lcd.putstr("SecureFlow v1.0")
sleep(1.5)
lcd.clear()

# ─── HARDWARE ────────────────────────────────────────────────────────────────

sensor = DHT22(Pin(15))
sensor_gas = ADC(26)

led_verde = Pin(12, Pin.OUT)
led_amarelo = Pin(8, Pin.OUT)
led_vermelho = Pin(4, Pin.OUT)

speaker = Speaker(14)

botao = Pin(18, Pin.IN, Pin.PULL_DOWN)

estado_anterior = ""

print("--- SISTEMA MONITOR CONECTADO ---")

# ─── CALLBACK MQTT ───────────────────────────────────────────────────────────

def ao_receber(topico, mensagem):
    msg = mensagem.decode()

    print(f"[SUB] {topico.decode()}: {msg}")

    if msg == "led:on":
        led_verde.on()
        print("[LED] Ligado")

    elif msg == "led:off":
        led_verde.off()
        print("[LED] Desligado")


# ─── CONEXÃO WIFI ────────────────────────────────────────────────────────────

if not conectar_wifi(WIFI_SSID, WIFI_PASS):
    print("[MAIN] Sem WiFi. Reinicie o dispositivo.")

else:

    cliente = MQTTClient(
        CLIENT_ID,
        BROKER_IP,
        port=BROKER_PORT
    )

    cliente.set_callback(ao_receber)

    try:

        cliente.connect()

        print(f"[MQTT] Conectado em: {BROKER_IP}")

        cliente.subscribe(TOPIC_SUB)

        print(f"[MQTT] Assinando: {TOPIC_SUB}")
        print(f"[MQTT] Publicando em: {TOPIC_PUB}")

        # ─── LOOP PRINCIPAL ────────────────────────────────────────────────

        while True:

            # Processa mensagens MQTT recebidas
            cliente.check_msg()

            try:
                sensor.measure()
                temp = sensor.temperature()
                umid = sensor.humidity()

            except OSError:

                temp = 24.0
                umid = 50.0

            leitura = sensor_gas.read_u16()
            estado_atual_botao = botao.value()

            print(
                "Temp: {}C | Umid: {}% | Gas: {} | Botao: {}".format(
                    temp,
                    umid,
                    leitura,
                    estado_atual_botao
                )
            )

            # ─── DEFINIÇÃO DO ESTADO ───────────────────────────────────────

            if estado_atual_botao == 1:
                estado_atual = "MANUAL"

            elif temp >= 50 or leitura >= 55000:
                estado_atual = "EMERGENCIA"

            elif temp >= 35 or leitura >= 45000:
                estado_atual = "ATENCAO"

            else:
                estado_atual = "SEGURO"

            # ─── LCD ──────────────────────────────────────────────────────

            if estado_atual != estado_anterior:

                lcd.clear()
                sleep_ms(20)

                if estado_atual == "MANUAL":

                    lcd.move_to(0, 0)
                    lcd.putstr("ALARME MANUAL")

                    lcd.move_to(0, 1)
                    lcd.putstr("EVACUAR AMBIENTE")

                elif estado_atual == "SEGURO":

                    lcd.move_to(0, 0)
                    lcd.putstr("AMBIENTE")

                    lcd.move_to(0, 1)
                    lcd.putstr("SEGURO")

                elif estado_atual == "ATENCAO":

                    lcd.move_to(0, 0)
                    lcd.putstr("ATENCAO")

                    lcd.move_to(0, 1)
                    lcd.putstr("POSSIVEL RISCO")

                elif estado_atual == "EMERGENCIA":

                    lcd.move_to(0, 0)
                    lcd.putstr("EMERGENCIA!")

                    lcd.move_to(0, 1)
                    lcd.putstr("EVACUAR")

                estado_anterior = estado_atual

            # ─── ATUADORES ────────────────────────────────────────────────

            if estado_atual == "MANUAL":

                led_verde.off()
                led_amarelo.off()

                led_vermelho.on()
                speaker.on()

                sleep(0.5)

                led_vermelho.off()
                speaker.off()

                sleep(0.5)

            elif estado_atual == "SEGURO":

                led_verde.on()
                led_amarelo.off()
                led_vermelho.off()

                speaker.off()

                sleep(1)

            elif estado_atual == "ATENCAO":

                led_verde.off()
                led_amarelo.on()
                led_vermelho.off()

                speaker.off()

                sleep(1)

            elif estado_atual == "EMERGENCIA":

                led_verde.off()
                led_amarelo.off()

                led_vermelho.on()
                speaker.on()

                sleep(0.2)

                led_vermelho.off()
                speaker.off()

                sleep(0.2)

            # ─── PUBLICAÇÃO MQTT ──────────────────────────────────────────

            mensagem = (
                f"temp:{temp:.1f},"
                f"umid:{umid:.1f},"
                f"gas:{leitura},"
                f"estado:{estado_atual}"
            )

            cliente.publish(
                TOPIC_PUB,
                mensagem.encode()
            )

            print(f"[PUB] {mensagem}")

            sleep(3)

    except Exception as e:

        print(f"[ERRO] {e}")
        print("[MQTT] Verifique broker, WiFi e configurações.")

    finally:

        try:
            cliente.disconnect()
            print("[MQTT] Desconectado.")

        except:
            pass