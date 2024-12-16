import pygame
import math


class JoystickHandler:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        
        self.joystick = None
        self.button_prev_state = {'a': False, 'b': False, 'start': False}  # Store previous states of buttons
        
    def initialize_joystick(self):
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        joy_count = pygame.joystick.get_count()
        if joy_count >= 1:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            return True
            
        else: return False

    def get_angle(self, threshold: float=0.1) -> float:
        """Returns the angle in degrees of the left joystick of an Xbox 360 controller"""
        if self.joystick is not None:

            left_x = self.joystick.get_axis(0)
            left_y = self.joystick.get_axis(1)

            if abs(left_x) > threshold or abs(left_y) > threshold:
                angle = int(math.degrees(math.atan2(-left_y, left_x)))
                if angle < 0:
                    angle += 360
                return angle

            else:
                return None

    def get_triggers(self, threshold: float=0.1, max_increase: float=0.5) -> float:
        """Returns trigger value: +1 for right trigger fully pressed, -1 for left, 0 if both fully pressed"""
        if self.joystick is None:
            return None

        right_trigger = (self.joystick.get_axis(5) + 1) / 2
        left_trigger = (self.joystick.get_axis(2) + 1) / 2

        if abs(right_trigger) > threshold or abs(left_trigger) > threshold:
            return (right_trigger - left_trigger) * max_increase
        
        else: return 0.0

    def MapRightStick(self, threshold: float=0.1) -> float:
        """
        Use for colorwheel of paint game
        Returns right joystick angle
        :param threshold:
        :return:
        """
        if self.joystick is not None:
            right_x = self.joystick.get_axis(3)
            right_y = self.joystick.get_axis(4)

            if abs(right_x) > threshold or abs(right_y) > threshold:
                angle = int(math.degrees(math.atan2(-right_y, right_x)))
                if angle < 0:
                    angle += 360
                return angle

            else:
                return None

    def GetJoystickButtons(self):
        if self.joystick is None:
            return None
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                # Detect button press (rising edge)
                if event.button == 0 and not self.button_prev_state['a']:  # A button
                    self.button_prev_state['a'] = True
                    return 'a'
                elif event.button == 1 and not self.button_prev_state['b']:  # B button
                    self.button_prev_state['b'] = True
                    return 'b'
                elif event.button == 7 and not self.button_prev_state['start']:  # Start button
                    self.button_prev_state['start'] = True
                    return 'start'

            elif event.type == pygame.JOYBUTTONUP:
                # Reset the button state when the button is released
                if event.button == 0:
                    self.button_prev_state['a'] = False
                elif event.button == 1:
                    self.button_prev_state['b'] = False
                elif event.button == 7:
                    self.button_prev_state['start'] = False

        return None  # Return None if no rising edge is detected
            
    
    def ProcessEvents(self):
        if self.joystick is not None:
            pygame.event.pump()

    def QuitPygame(self):
        self.joystick = None
        if pygame.joystick.get_init():
            pygame.joystick.quit()
