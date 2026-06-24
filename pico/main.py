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
alarme_manual_ativo = False      
botao_pressionado_anterior = 0  

# TÓPICOS CORRIGIDOS CONFORME SEU CONFIG GLOBAL
TOPICO_PUBLICACAO = "senai/grupo2/sensores"
TOPICO_ASSINATURA = "senai/grupo2/comandos"

print("SISTEMA MONITOR CONECTADO")

# ─── CALLBACK MQTT (PROCESSA COMANDOS DO DASHBOARD) ─────────────────────────
def ao_receber(topico, mensagem):
    global alarme_manual_ativo
    msg = mensagem.decode().strip()

    print(f"[SUB] Comando recebido: {msg}")

    if msg == "teste:verde":
        led_verde.on()
        sleep(1)
        led_verde.off()

    elif msg == "teste:amarelo":
        led_amarelo.on()
        sleep(1)
        led_amarelo.off()

    elif msg == "teste:vermelho":
        led_vermelho.on()
        sleep(1)
        led_vermelho.off()

    elif msg == "teste:speaker":
        speaker.on()
        sleep(1)
        speaker.off()

    elif msg == "alarme:manual":
        alarme_manual_ativo = not alarme_manual_ativo
        print(f"[ALARME] Estado manual alterado via Dashboard para: {alarme_manual_ativo}")

# ─── CONEXÃO WIFI ────────────────────────────────────────────────────────────
if not conectar_wifi(WIFI_SSID, WIFI_PASS):
    print("[MAIN] Sem WiFi. Reinicie o dispositivo.")
else:
    cliente = MQTTClient(
        CLIENT_ID,
        "10.132.112.5", # IP do seu Broker local do SENAI
        port=1883        # Porta padrão MQTT da Pico (O Broker mapeia 9001 para Web e 1883 para TCP)
    )

    cliente.set_callback(ao_receber)

    try:
        cliente.connect()
        print("[MQTT] Conectado ao Broker do SENAI.")
        
        # Inscreve no tópico de comandos que o Dashboard publica
        cliente.subscribe(TOPICO_ASSINATURA)
        print(f"[MQTT] Ouvindo comandos em: {TOPICO_ASSINATURA}")

        # ─── LOOP PRINCIPAL ────────────────────────────────────────────────
        while True:
            # Verifica se há comandos pendentes vindos do Dashboard
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

            # Lógica física do botão (Toggle com Debounce)
            if estado_atual_botao == 1 and botao_pressionado_anterior == 0:
                alarme_manual_ativo = not alarme_manual_ativo
                sleep_ms(50) 

            botao_pressionado_anterior = estado_atual_botao

            # DEFINIÇÃO DO ESTADO DO SISTEMA
            if alarme_manual_ativo:
                estado_atual = "MANUAL"
            elif temp >= 50 or leitura >= 55000:
                estado_atual = "EMERGENCIA"
            elif temp >= 35 or leitura >= 45000:
                estado_atual = "ATENCAO"
            else:
                estado_atual = "SEGURO"

            # ATUALIZAÇÃO DO DISPLAY LCD
            if estado_atual != estado_anterior:
                lcd.clear()
                sleep_ms(20)
                if estado_atual == "MANUAL":
                    lcd.move_to(0, 0); lcd.putstr("ALARME MANUAL")
                    lcd.move_to(0, 1); lcd.putstr("EVACUAR AMBIENTE")
                elif estado_atual == "SEGURO":
                    lcd.move_to(0, 0); lcd.putstr("AMBIENTE")
                    lcd.move_to(0, 1); lcd.putstr("SEGURO")
                elif estado_atual == "ATENCAO":
                    lcd.move_to(0, 0); lcd.putstr("ATENCAO")
                    lcd.move_to(0, 1); lcd.putstr("POSSIVEL RISCO")
                elif estado_atual == "EMERGENCIA":
                    lcd.move_to(0, 0); lcd.putstr("EMERGENCIA!")
                    lcd.move_to(0, 1); lcd.putstr("EVACUAR")
                
                estado_anterior = estado_atual

            # CONTROLE DOS ATUADORES DA PLACA
            if estado_atual in ["MANUAL", "EMERGENCIA"]:
                led_verde.off(); led_amarelo.off(); led_vermelho.on()
                speaker.on()
            elif estado_atual == "ATENCAO":
                led_verde.off(); led_amarelo.on(); led_vermelho.off()
                speaker.off()
            else:
                led_verde.on(); led_amarelo.off(); led_vermelho.off()
                speaker.off()

            # ENVIO DE DADOS FORMATADO (Sem espaços para evitar erros de leitura no JS)
            mensagem = f"Temperatura:{temp:.1f},Umidade:{umid:.1f},Gás:{leitura},Estado:{estado_atual}"
            
            try:
                cliente.publish(TOPICO_PUBLICACAO, mensagem.encode())
                print(f"[PUB] Dados enviados: {mensagem}")
            except Exception as e:
                print(f"[ERRO PUB] Falha ao enviar telemetria: {e}")
            
            sleep(1)

    except Exception as e:
        print(f"[ERRO GLOBAL] {e}")

    finally:
        try:
            cliente.disconnect()
            print("[MQTT] Desconectado de forma segura.")
        except:
            pass