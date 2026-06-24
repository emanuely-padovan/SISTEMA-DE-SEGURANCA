import utime
import gc

from lcd_api import LcdApi
from machine import I2C

# Máscaras de bits para os pinos do chip PCF8574, que converte I2C para paralelo
MASK_RS = 0x01       # Pino RS (Registro de seleção: comando ou dado)
MASK_RW = 0x02       # Pino RW (Leitura ou escrita - quase sempre em escrita)
MASK_E  = 0x04       # Pino E (Enable - usado para acionar leitura/escrita)

# Deslocamentos para manipular bits do backlight e dos dados
SHIFT_BACKLIGHT = 3  # Pino P3 do PCF8574 controla o backlight
SHIFT_DATA      = 4  # Pinos P4 a P7 usados para enviar dados (modo 4 bits)

class I2cLcd(LcdApi):
    
    # Classe que implementa um display LCD (HD44780) conectado via I2C usando PCF8574

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        # Inicializa o display com o barramento I2C e configurações de linhas/colunas
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.i2c.writeto(self.i2c_addr, bytes([0]))  # Garante que o barramento está zerado
        utime.sleep_ms(20)   # Aguarda o display ligar completamente (recomendado)

        # Envia comando de reset 3 vezes, conforme especificação do HD44780
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(5)    # Espera mínima exigida após o reset
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(1)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(1)

        # Coloca o LCD em modo de comunicação de 4 bits
        self.hal_write_init_nibble(self.LCD_FUNCTION)
        utime.sleep_ms(1)

        # Inicializa a API base com número de linhas e colunas
        LcdApi.__init__(self, num_lines, num_columns)

        # Prepara comando de configuração
        cmd = self.LCD_FUNCTION
        if num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES  # Ativa modo de 2 linhas (se aplicável)
        self.hal_write_command(cmd)  # Envia comando de configuração para o LCD

        gc.collect()  # Limpa a memória (garbage collector)

    def hal_write_init_nibble(self, nibble):
        # Envia um nibble (4 bits) de inicialização para o display
        # Essa função é usada apenas durante o processo de inicialização

        byte = ((nibble >> 4) & 0x0f) << SHIFT_DATA  # Prepara os bits de dados
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))  # Envia pulso de ativação
        self.i2c.writeto(self.i2c_addr, bytes([byte]))           # Finaliza o pulso

        gc.collect()  # Limpa a memória

    def hal_backlight_on(self):
        # Liga o backlight (luz de fundo) do display
        self.i2c.writeto(self.i2c_addr, bytes([1 << SHIFT_BACKLIGHT]))
        gc.collect()

    def hal_backlight_off(self):
        # Desliga o backlight do display
        self.i2c.writeto(self.i2c_addr, bytes([0]))
        gc.collect()

    def hal_write_command(self, cmd):
        # Envia um comando para o display LCD (como limpar tela, mover cursor, etc.)
        # Os dados são enviados em dois nibbles de 4 bits

        # Envia parte alta do comando
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                (((cmd >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))  # Pulso de ativação
        self.i2c.writeto(self.i2c_addr, bytes([byte]))           # Finaliza o pulso

        # Envia parte baixa do comando
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                ((cmd & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))

        if cmd <= 3:
            # Comandos como "home" e "clear" precisam de mais tempo para executar
            utime.sleep_ms(5)

        gc.collect()

    def hal_write_data(self, data):
        # Envia dados (caracteres) para o LCD
        # O LCD aceita 4 bits por vez, por isso dividimos em duas partes

        # Envia parte alta do dado
        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                (((data >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))  # Pulso
        self.i2c.writeto(self.i2c_addr, bytes([byte]))           # Fim do pulso

        # Envia parte baixa do dado
        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                ((data & 0x0f) << SHIFT_DATA))      
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))

        gc.collect()


