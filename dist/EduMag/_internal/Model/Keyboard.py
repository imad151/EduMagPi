import keyboard

class ArrowKeyAngle:
    def __init__(self):
        self.angle_map = {
            ('up',): 90,
            ('down',): 270,
            ('left',): 180,
            ('right',): 0,
            ('up', 'right'): 45,
            ('up', 'left'): 135,
            ('down', 'right'): 315,
            ('down', 'left'): 225,
        }

    def get_angle(self):
        pressed = tuple(key for key in ['up', 'down', 'left', 'right'] if keyboard.is_pressed(key))
        if len(pressed) !=0:
            angle = self.angle_map.get(pressed, None)



