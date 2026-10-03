"""Builds assets/ZabanYar.ico (the .exe icon) from assets/icon.png and data/tray.png."""
from PIL import Image

big = Image.open('assets/icon.png').convert('RGBA')
small = Image.open('data/tray.png').convert('RGBA')     # simpler design, sharper at 16-32 px
sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
frames = [(small if n <= 32 else big).resize((n, n), Image.LANCZOS) for n in sizes]
frames[-1].save('assets/ZabanYar.ico', format='ICO', sizes=[(n, n) for n in sizes],
                append_images=frames[:-1])
print('assets/ZabanYar.ico created')
