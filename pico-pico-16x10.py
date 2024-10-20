import array, time, math
import bootsel
import random
from machine import Pin
import rp2

# Configuration
CONFIG = {
    'SCROLL': True,
    'SCROLL_DIRECTION': 'LEFT',  # 'LEFT' or 'RIGHT'
    'SCROLL_SPEED': 0.1,  # Smaller value for faster scrolling
    'TEXT_COLOR': (255, 255, 255),  
    'BACKGROUND_COLOR': (0, 0, 0), 
    'FIRE_EFFECT': True,
    'TIMER_MODE': False,
    'BRIGHTNESS': 0.01,
    'NUM_LEDS': 160,
    'PIN_NUM': 6,
    'DISPLAY_WIDTH': 16,
    'DISPLAY_HEIGHT': 10,
    'ROTATED': True
}

# Configure the number of WS2812 LEDs.
NUM_LEDS = CONFIG['NUM_LEDS']
PIN_NUM = CONFIG['PIN_NUM']

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

class NeoPixel(object):
    def __init__(self,pin=PIN_NUM,num=NUM_LEDS,brightness=0.8):
        self.pin=pin
        self.num=num
        self.brightness = brightness
        
        # Create the StateMachine with the ws2812 program, outputting on pin
        self.sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))

        # Start the StateMachine, it will wait for data on its FIFO.
        self.sm.active(1)

        # Display a pattern on the LEDs via an array of LED RGB values.
        self.ar = array.array("I", [0 for _ in range(self.num)])
        
    def pixels_show(self):
        dimmer_ar = array.array("I", [0 for _ in range(self.num)])
        for i,c in enumerate(self.ar):
            r = int(((c >> 8) & 0xFF) * self.brightness)
            g = int(((c >> 16) & 0xFF) * self.brightness)
            b = int((c & 0xFF) * self.brightness)
            dimmer_ar[i] = (g<<16) + (r<<8) + b
        self.sm.put(dimmer_ar, 8)

    def pixels_set(self, i, color):
        self.ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]

    def pixels_fill(self, color):
        for i in range(len(self.ar)):
            self.pixels_set(i, color)

font_5x7 = {
    'A': ['00100', '01010', '10001', '11111', '10001', '10001', '10001'],
    'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
    'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],
    'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
    'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
    'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
    'G': ['01110', '10001', '10000', '10111', '10001', '10001', '01111'],
    'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
    'I': ['11111', '00100', '00100', '00100', '00100', '00100', '11111'],
    'J': ['00111', '00010', '00010', '00010', '00010', '10010', '01100'],
    'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
    'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
    'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
    'Q': ['01110', '10001', '10001', '10001', '10101', '10010', '01101'],
    'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
    'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],
    'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
    'W': ['10001', '10001', '10001', '10101', '10101', '10101', '01010'],
    'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
    'Y': ['10001', '10001', '10001', '01010', '00100', '00100', '00100'],
    'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
    '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],
    '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'],
    '3': ['11111', '00010', '00100', '00010', '00001', '10001', '01110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
    '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
    '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'],
    '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'],
    '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
    ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000'],
    ':': ['00000', '00100', '00000', '00000', '00000', '00100', '00000'],
    'А': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    'Б': ['11111', '10000', '10000', '11110', '10001', '10001', '11110'],
    'В': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
    'Г': ['11111', '10000', '10000', '10000', '10000', '10000', '10000'],
    'Ґ': ['11111', '10000', '10000', '10000', '10000', '10000', '10000'],
    'Д': ['00110', '01010', '01010', '01010', '01010', '11111', '10001'],
    'Е': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
    'Є': ['01111', '10000', '10000', '11110', '10000', '10000', '01111'],
    'Ж': ['10101', '10101', '01110', '00100', '01110', '10101', '10101'],
    'З': ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
    'И': ['10001', '10001', '10011', '10101', '11001', '10001', '10001'],
    'І': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'],
    'Ї': ['10101', '00000', '01110', '00100', '00100', '00100', '01110'],
    'Й': ['01010', '10001', '10011', '10101', '11001', '10001', '10001'],
    'К': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
    'Л': ['01111', '01001', '01001', '01001', '01001', '01001', '10001'],
    'М': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
    'Н': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
    'О': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'П': ['11111', '10001', '10001', '10001', '10001', '10001', '10001'],
    'Р': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
    'С': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],
    'Т': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'У': ['10001', '10001', '10001', '01111', '00001', '10001', '01110'],
    'Ф': ['00100', '01110', '10101', '10101', '10101', '01110', '00100'],
    'Х': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
    'Ц': ['10010', '10010', '10010', '10010', '10010', '10010', '11111', '00001'],
    'Ч': ['10001', '10001', '10001', '01111', '00001', '00001', '00001'],
    'Ш': ['10001', '10001', '10001', '10101', '10101', '10101', '11111'],
    'Щ': ['10001', '10001', '10001', '10101', '10101', '10101', '11111', '00001'],
    'Ь': ['10000', '10000', '10000', '11110', '10001', '10001', '11110'],
    'Ю': ['10010', '10101', '10101', '11101', '10101', '10101', '10010'],
    'Я': ['01111', '10001', '10001', '01111', '00101', '01001', '10001'],
}

def rgb_to_int(r, g, b):
    return (g << 16) + (r << 8) + b

def int_to_rgb(c):
    r = int((c >> 8) & 0xFF)
    g = int((c >> 16) & 0xFF)
    b = int(c & 0xFF)
    return (r, g, b)

def mul_rgb(mul, rgb):
    (r, g, b) = rgb
    return (int(r * mul), int(g * mul), int(b * mul))

def create_scrolling_display_mask(text, width=CONFIG['DISPLAY_WIDTH'], height=CONFIG['DISPLAY_HEIGHT']):
    display_mask = [''] * height
    text = text.upper() 
    
    for char in text + ' ': 
        char_pattern = font_5x7.get(char, font_5x7[' '])
        for i, row in enumerate(char_pattern):
            display_mask[i] += row + '0' 
    
    for i in range(height):
        if len(display_mask[i]) < width:
            display_mask[i] += '0' * (width - len(display_mask[i]))
    
    return display_mask

def update_fire_effect(fireTempAr, lastLine):
    for i in range(16):
        lastLine[i] = random.randrange(0, 1024)
    fireTempAr = fireTempAr[16:] + lastLine

    fireTempAr2 = fireTempAr
    for i in range(16, CONFIG['NUM_LEDS']):
        fireTempAr2[i] = int((fireTempAr[i - 16] + fireTempAr[i - 1] + fireTempAr[i + 1] + fireTempAr[i + 16] + fireTempAr[i]) / 5.25)
    return fireTempAr2

def get_color(fVal, mask, fireLookUpPalette, fireLookUpPalette2):
    if CONFIG['FIRE_EFFECT']:
        return fireLookUpPalette2[fVal] if mask == '0' else fireLookUpPalette[fVal]
    else:
        return rgb_to_int(*CONFIG['BACKGROUND_COLOR']) if mask == '0' else rgb_to_int(*CONFIG['TEXT_COLOR'])

def update_timer(time_left):
    minutes, seconds = divmod(time_left, 60)
    return f"{minutes:02d}:{seconds:02d}"

def main():
    strip = NeoPixel(pin=CONFIG['PIN_NUM'], num=CONFIG['NUM_LEDS'], brightness=CONFIG['BRIGHTNESS'])

    fireTempAr = array.array("I", [0] * (CONFIG['NUM_LEDS'] + 16))
    lastLine = fireTempAr[:16]

    fireLookUpPalette = array.array("I", (rgb_to_int(0, i, 0) if i < 256 else rgb_to_int((i - 256), 255, 0) if i < 512 else rgb_to_int(255, 255, (i - 512)) if i < 768 else rgb_to_int(255, 255, 255) for i in range(1024)))
    fireLookUpPalette2 = array.array("I", (rgb_to_int(*mul_rgb(0.2, int_to_rgb(c))) for c in fireLookUpPalette))

    if CONFIG['TIMER_MODE']:
        display_text = input("Enter time in MM:SS format: ")
        try:
            minutes, seconds = map(int, display_text.split(':'))
            time_left = minutes * 60 + seconds
        except:
            print("Invalid input. Using default 5:00")
            time_left = 300
    else:
        display_text = input("Enter the text to display (Latin or Ukrainian): ")

    if display_text == "":
        display_text = "ПРИВІТ FROM KAIMAN"

    display_mask = create_scrolling_display_mask(display_text)
    scroll_position = 0
    mask_width = len(display_mask[0])

    start_time = time.time()

    while True:
        if CONFIG['FIRE_EFFECT']:
            fireTempAr = update_fire_effect(fireTempAr, lastLine)

        if CONFIG['TIMER_MODE']:
            elapsed_time = int(time.time() - start_time)
            time_left = max(0, time_left - elapsed_time)
            display_text = update_timer(time_left)
            display_mask = create_scrolling_display_mask(display_text)
            start_time = time.time()

        for i in range(CONFIG['NUM_LEDS']):
            row = i // CONFIG['DISPLAY_WIDTH']
            col = i % CONFIG['DISPLAY_WIDTH']
            
            if CONFIG['ROTATED']:
                row = CONFIG['DISPLAY_HEIGHT'] - 1 - row
                col = CONFIG['DISPLAY_WIDTH'] - 1 - col
            
            if CONFIG['SCROLL']:
                mask_col = (col + scroll_position) % mask_width if CONFIG['SCROLL_DIRECTION'] == 'LEFT' else (mask_width - 1 - (col + scroll_position) % mask_width)
            else:
                mask_col = col

            if row < len(display_mask) and mask_col < len(display_mask[row]):
                mask = display_mask[row][mask_col]
            else:
                mask = '0'
            
            fVal = fireTempAr[i] if CONFIG['FIRE_EFFECT'] else 0
            
            if CONFIG['ROTATED']:
                rotated_index = (CONFIG['DISPLAY_HEIGHT'] - 1 - row) * CONFIG['DISPLAY_WIDTH'] + (CONFIG['DISPLAY_WIDTH'] - 1 - col)
                strip.ar[rotated_index] = get_color(fVal, mask, fireLookUpPalette, fireLookUpPalette2)
            else:
                strip.ar[i] = get_color(fVal, mask, fireLookUpPalette, fireLookUpPalette2)

        strip.pixels_show()

        if CONFIG['SCROLL']:
            scroll_position = (scroll_position + 1) % mask_width

        if bootsel.pressed():
            strip.brightness += 0.1
            if strip.brightness > 1.0:
                strip.brightness = 0.1
            while bootsel.pressed():
                time.sleep(0.1)

        time.sleep(CONFIG['SCROLL_SPEED'])

        if CONFIG['TIMER_MODE'] and time_left <= 0:
            break

    if CONFIG['TIMER_MODE']:
        end_mask = create_scrolling_display_mask("END")
        while True:
            for i in range(CONFIG['NUM_LEDS']):
                row = i // CONFIG['DISPLAY_WIDTH']
                col = i % CONFIG['DISPLAY_WIDTH']
                if row < len(end_mask) and col < len(end_mask[row]):
                    mask = end_mask[row][col]
                else:
                    mask = '0'
                strip.ar[i] = rgb_to_int(*CONFIG['TEXT_COLOR']) if mask == '1' else rgb_to_int(*CONFIG['BACKGROUND_COLOR'])
            strip.pixels_show()
            time.sleep(0.1)

if __name__ == '__main__':
    main()
