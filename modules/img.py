import cv2
import io
import os
import numpy as np
import base64
from PIL import Image, ImageDraw, ImageFont

def hex_to_rgb(hex_color):
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return color

class Img:
    def __init__(self,arg:str or bytes) -> None:
        if os.path.isfile(arg):
            self.file_path = arg
            with open(self.file_path,'rb') as f:
                self.image_data = f.read()
        else:
            self.file_path = None
            self.image_data = arg

    def get_point_location(self,hex_color):
        # Convert hex color to RGB format

        color = hex_to_rgb(hex_color)

        # Load image and convert to HSV format
        np_array = np.frombuffer(self.image_data, dtype=np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # lower_color = np.array([140, 100, 100])
        # upper_color = np.array([180, 255, 255])

        # Define color threshold range based on RGB color
        rgb_color = np.uint8([[color]])
        hsv_color = cv2.cvtColor(rgb_color, cv2.COLOR_RGB2HSV)
        hue = hsv_color[0][0][0]
        lower_color = np.array([hue-10, 100, 100])
        upper_color = np.array([hue+10, 255, 255])

        # Threshold image for specified color
        mask = cv2.inRange(hsv_image, lower_color, upper_color)

        # Find contours in region
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            return False
        moment = cv2.moments(contours[0])
        cx = int(moment['m10'] / moment['m00'])
        cy = int(moment['m01'] / moment['m00'])
        location = {
            'x': cx,
            'y': cy
        }
        return location
    
    def write_text_on_image(self, text, text_location, font_path, font_size, font_hex_color, transparent=True):
        if self.file_path:
            source_image = Image.open(self.file_path)
        else:
            # Load the image from the buffer
            np_array = np.frombuffer(self.image_data, np.uint8)
            source_image = Image.fromarray(cv2.imdecode(np_array, cv2.IMREAD_COLOR))

        # Get the dimensions of the source image
        width, height = source_image.size

        if transparent:
            # Create a new transparent image with the same dimensions
            new_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        else:
            new_image = source_image

        # Create a drawing context for the new image
        draw = ImageDraw.Draw(new_image)

        # Set the font and size for the text
        font = ImageFont.truetype(font_path, font_size)

        # Get the size of the text
        text_width, text_height = draw.textsize(text, font=font)

        # Calculate the position to center the text on the image
        x = text_location['x']
        y = text_location['y']

        # Get color as rbg
        color = hex_to_rgb(font_hex_color)
        # Draw the text on the image
        draw.text((x, y), text, font=font, fill=color, language='ar',anchor='ms')
        # draw.text((x, y), text, font=font, fill=color,anchor='ms')

        # Save the new image as a buffer
        output_buffer = io.BytesIO()
        new_image.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        output_data = output_buffer.getvalue()
        return output_data
    
    def to_greyscale(self):
        '''returns greyscale image buffer'''
        np_array = np.frombuffer(self.image_data, dtype=np.uint8)
        image = cv2.imdecode(np_array,cv2.IMREAD_COLOR) #? reading image
        grey_image = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        return_value,buffer = cv2.imencode('.jpg',grey_image)
        return buffer
    
    def to_base64(self):
        '''returns base64 string'''
        base64_image = base64.b64encode(self.image_data).decode('utf-8')
        return base64_image


if __name__ == '__main__':
    with open('./designs/design_1.png' , 'rb') as f:
        image = f.read()
    image_data = Img(image).to_greyscale()
    with open('./image.png','wb') as f :
        f.write(image_data)