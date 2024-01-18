import os

from PIL import Image, ImageDraw, ImageFont, ImageOps


class Drawer:
    def __init__(self, width, height, orientation, inverted, fontdir):
        self.height = width
        self.width = height
        self.orientation = orientation
        self.inverted = inverted
        self.fontdir = fontdir

        self.initialize()

    def _change_size(self, width, height):
        self.height = width
        self.width = height
        self.initialize()

    def buildFont(self, font_name, font_size):
        google_fontdir = os.path.join(self.fontdir, "googlefonts")
        if os.path.exists(os.path.join(self.fontdir, font_name)):
            return ImageFont.truetype(os.path.join(self.fontdir, font_name), font_size)
        elif os.path.exists(os.path.join(self.fontdir, font_name + ".ttf")):
            return ImageFont.truetype(
                os.path.join(self.fontdir, font_name + ".ttf"), font_size
            )
        elif os.path.exists(os.path.join(google_fontdir, font_name)):
            return ImageFont.truetype(
                os.path.join(google_fontdir, font_name), font_size
            )
        elif os.path.exists(os.path.join(google_fontdir, font_name + ".ttf")):
            return ImageFont.truetype(
                os.path.join(google_fontdir, font_name + ".ttf"), font_size
            )
        else:
            raise Exception(f"Could not find {font_name} in {self.fontdir}")

    def textsize(self, text, font):
        _, _, width, height = self.draw.textbbox((0, 0), text=text, font=font)
        return width, height

    def drawText(self, x, y, text, font, anchor="la"):
        w, h = self.textsize(text, font=font)
        self.draw.text((x, y), text, font=font, fill=0, anchor=anchor)
        return w, h

    def calc_font_size(
        self, max_w, max_h, text, font_name, start_font_size=15, anchor="la"
    ):
        font_size = start_font_size - 1
        h = 0
        w = 0
        while h < max_h and w < max_w:
            font_size += 1
            font = self.buildFont(font_name, font_size)
            start_x, start_y, end_x, end_y = self.draw.textbbox(
                (0, 0), text, font=font, anchor=anchor
            )
            w = end_x - start_x
            h = end_y - start_y
        font_size -= 1
        return font_size

    def draw_text(self, x, y, font_size, text, font_name, anchor="la"):
        font = self.buildFont(font_name, font_size)
        w, h = self.textsize(text, font=font)
        self.draw.text((x, y), text, font=font, fill=0, anchor=anchor)
        return w, h

    def initialize(self):
        self.image = Image.new(
            'L', (self.width, self.height), 255
        )  # 255: clear the image with white
        self.draw = ImageDraw.Draw(self.image)

    def finalize(self, mirror=True):
        if self.orientation != 0:
            self.image = self.image.rotate(self.orientation, expand=True)
        if mirror:
            self.image = ImageOps.mirror(self.image)
        #   If the display is inverted, invert the image usinng ImageOps
        if self.inverted:
            self.image = ImageOps.invert(self.image)

    def paste(self, im, box=None, mask=None):
        self.image.paste(im, box=box, mask=mask)

    def show(self):

        self.image.show()
