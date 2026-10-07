# utils/lcd_utils.py

from RPLCD.i2c import CharLCD

# Use the address you detected (0x27)
LCD_ADDR = 0x27

# Initialize the LCD (16 columns, 2 rows)
lcd = CharLCD('PCF8574', LCD_ADDR, cols=16, rows=2)

def lcd_message(line1, line2=''):
    """
    Display up to 2 lines on the 16x2 LCD.
    Usage: lcd_message("Hello", "World")
    """
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string(line1.ljust(16)[:16])
    if line2:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line2.ljust(16)[:16])
