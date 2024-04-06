from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def create_diploma(name, title):
    img = Image.open('static/diploma.png')
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('static/Caveat.ttf', 120)
    w, h= img.size
    draw.text((w / 2 - 150, h / 2 - 180), name, font=font, fill=(0, 0, 128), align='center')
    draw.text((w / 3 - 150, h / 2 + 120), title, font=font, fill=(0, 0, 128), align='center')
    img.show()
    img.save("static/user_diploma.png")