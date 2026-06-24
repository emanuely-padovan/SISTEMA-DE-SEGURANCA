import time

class LcdApi:
    
    # Implementa a API de controle para comunicação com displays LCD
    # compatíveis com o controlador HD44780.
    #
    # Essa classe sabe quais comandos enviar para o LCD, mas não como fisicamente
    # enviá-los. Isso é responsabilidade das funções "hal_" que devem ser
    # implementadas por uma subclasse (ex: I2cLcd).
    #
    # Os nomes das constantes abaixo foram baseados na biblioteca "avrlib lcd.h",
    # adaptando os bits para máscaras.

    # Conjunto de comandos do controlador HD44780
    LCD_CLR             = 0x01  # Limpar o display
    LCD_HOME            = 0x02  # Retornar o cursor para a posição inicial (canto superior esquerdo)

    LCD_ENTRY_MODE      = 0x04  # Configura o modo de escrita
    LCD_ENTRY_INC       = 0x02  # Move o cursor para a direita após escrever
    LCD_ENTRY_SHIFT     = 0x01  # Move o display ao invés do cursor

    LCD_ON_CTRL         = 0x08  # Controle da exibição (ligar/desligar)
    LCD_ON_DISPLAY      = 0x04  # Liga o display
    LCD_ON_CURSOR       = 0x02  # Exibe o cursor
    LCD_ON_BLINK        = 0x01  # Faz o cursor piscar

    LCD_MOVE            = 0x10  # Comando de movimentação
    LCD_MOVE_DISP       = 0x08  # Move o conteúdo do display (0 -> move o cursor)
    LCD_MOVE_RIGHT      = 0x04  # Move para a direita (0 -> esquerda)

    LCD_FUNCTION        = 0x20  # Define o modo de operação
    LCD_FUNCTION_8BIT   = 0x10  # Usa o modo de 8 bits (0 -> modo de 4 bits)
    LCD_FUNCTION_2LINES = 0x08  # Usa duas linhas no display (0 -> uma linha)
    LCD_FUNCTION_10DOTS = 0x04  # Usa fonte de 5x10 pixels (0 -> 5x7)
    LCD_FUNCTION_RESET  = 0x30  # Reset do LCD por instrução (modo compatível)

    LCD_CGRAM           = 0x40  # Endereço da memória CGRAM (caracteres personalizados)
    LCD_DDRAM           = 0x80  # Endereço da memória de exibição (DDRAM)

    LCD_RS_CMD          = 0  # Modo comando (RS=0)
    LCD_RS_DATA         = 1  # Modo dados (RS=1)

    LCD_RW_WRITE        = 0  # Operação de escrita (RW=0)
    LCD_RW_READ         = 1  # Operação de leitura (RW=1)

    def __init__(self, num_lines, num_columns):
        # Inicializa o display com o número de linhas e colunas definidos
        self.num_lines = num_lines
        if self.num_lines > 4:
            self.num_lines = 4  # Limita a 4 linhas (máximo do HD44780)
        self.num_columns = num_columns
        if self.num_columns > 40:
            self.num_columns = 40  # Limita a 40 colunas (máximo do HD44780)
        self.cursor_x = 0
        self.cursor_y = 0
        self.implied_newline = False  # Controla quebras de linha automáticas
        self.backlight = True

        self.display_off()       # Começa com o display desligado
        self.backlight_on()      # Liga o backlight
        self.clear()             # Limpa a tela
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)  # Configura entrada
        self.hide_cursor()       # Esconde o cursor
        self.display_on()        # Liga o display

    def clear(self):
        # Limpa o conteúdo do display e reposiciona o cursor no canto superior esquerdo
        self.hal_write_command(self.LCD_CLR)
        self.hal_write_command(self.LCD_HOME)
        self.cursor_x = 0
        self.cursor_y = 0

    def show_cursor(self):
        # Exibe o cursor na tela
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR)

    def hide_cursor(self):
        # Esconde o cursor da tela
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def blink_cursor_on(self):
        # Exibe o cursor e faz ele piscar
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                               self.LCD_ON_CURSOR | self.LCD_ON_BLINK)

    def blink_cursor_off(self):
        # Exibe o cursor, mas sem piscar
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                               self.LCD_ON_CURSOR)

    def display_on(self):
        # Liga (desbloqueia) o conteúdo do display
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def display_off(self):
        # Desliga (oculta) todo o conteúdo do display
        self.hal_write_command(self.LCD_ON_CTRL)

    def backlight_on(self):
        # Liga o backlight (luz de fundo) do display
        # Não é um comando oficial do LCD, mas muitos módulos I2C suportam
        self.backlight = True
        self.hal_backlight_on()

    def backlight_off(self):
        # Desliga o backlight do display
        self.backlight = False
        self.hal_backlight_off()

    def move_to(self, cursor_x, cursor_y):
        # Move o cursor para a posição (coluna, linha) especificada
        # A contagem começa do zero (linha 0, coluna 0)
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        addr = cursor_x & 0x3f
        if cursor_y & 1:
            addr += 0x40    # Linhas 1 e 3 adicionam 0x40 ao endereço base
        if cursor_y & 2:
            addr += self.num_columns  # Linhas 2 e 3 adicionam a largura da linha
        self.hal_write_command(self.LCD_DDRAM | addr)

    def putchar(self, char):
        # Escreve um caractere no display e move o cursor uma posição para frente
        if char == '\n':
            if self.implied_newline:
                pass  # Ignora quebras duplicadas geradas por wrap automático
            else:
                self.cursor_x = self.num_columns  # Força quebra de linha
        else:
            self.hal_write_data(ord(char))  # Envia o caractere
            self.cursor_x += 1
        if self.cursor_x >= self.num_columns:
            self.cursor_x = 0
            self.cursor_y += 1
            self.implied_newline = (char != '\n')
        if self.cursor_y >= self.num_lines:
            self.cursor_y = 0
        self.move_to(self.cursor_x, self.cursor_y)

    def putstr(self, string):
        # Escreve uma string inteira no display, caractere por caractere
        for char in string:
            self.putchar(char)

    def custom_char(self, location, charmap):
        # Cria um caractere personalizado em uma das 8 posições da CGRAM
        # Os caracteres podem ser acessados por chr(0) até chr(7)
        location &= 0x7  # Garante que o endereço esteja entre 0 e 7
        self.hal_write_command(self.LCD_CGRAM | (location << 3))
        self.hal_sleep_us(40)
        for i in range(8):
            self.hal_write_data(charmap[i])
            self.hal_sleep_us(40)
        self.move_to(self.cursor_x, self.cursor_y)

    # As funções abaixo devem ser implementadas por uma subclasse (ex: I2cLcd)

    def hal_backlight_on(self):
        # Liga o backlight — a subclasse deve implementar isso se necessário
        pass

    def hal_backlight_off(self):
        # Desliga o backlight — a subclasse deve implementar isso se necessário
        pass

    def hal_write_command(self, cmd):
        # Envia um comando para o display — a subclasse deve implementar
        raise NotImplementedError

    def hal_write_data(self, data):
        # Envia dados (caracteres) para o display — a subclasse deve implementar
        raise NotImplementedError

    def hal_sleep_us(self, usecs):
        # Aguarda por um tempo em microssegundos
        time.sleep_us(usecs)

