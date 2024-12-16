import serial
from serial.tools import list_ports
import numpy as np
import time
class ArduinoController:
    def __init__(self):
        self.ser = None
        self.port = 'COM4'
        self.baudrate = 115200
        self.timeout = 0.03
        self.attempts = 1  # Default max attempts for command echo check


    def get_serial_ports_list(self):
        ports = list_ports.comports()  # Get list of available ports
        available_ports = [port.device for port in ports]
        print(f"Available serial ports: {available_ports}")
        return available_ports

    def set_port(self, port):
        """Set the port for the serial connection."""
        self.port = port

    def set_baudrate(self, baudrate):
        """Set the baud rate for the serial connection."""
        self.baudrate = baudrate

    def set_timeout(self, timeout):
        """Set the timeout for the serial connection."""
        self.timeout = timeout

    def set_attempts(self, attempts):
        """Set the number of attempts for command echo verification."""
        self.attempts = attempts

    def connect(self):
        """Establish a connection to the Arduino and return True if successful, False otherwise."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            #time.sleep(0.2)
            return True
        except serial.SerialException:
            self.ser = None
            return False

    def disconnect(self):
        """Close the connection to the Arduino and return True if disconnected successfully, False otherwise."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
            return True
        return False

    def send_command_with_echo(self, command):
        """Send command to Arduino, check for echo, and return response or False if unsuccessful."""
        if not self.ser or not self.ser.is_open:
            return False  # Not connected

        for attempt in range(self.attempts):
            # Flush the input buffer to clear any stale data
            self.ser.reset_output_buffer()

            # Write the command to the serial port
            self.ser.write((command + '\n').encode())
            
            #time.sleep(0.1)  # Small delay after sending command to allow Arduino to process it

            # Read the echo response with a delay to wait for Arduino response
            response = self.ser.readline().decode().strip()
            if response == command:
                response_data = ""
                while True:
                    line = self.ser.readline().decode().strip()
                    if not line:
                        break
                    response_data += line + '\n'
                return response_data.strip()

            if attempt < self.attempts - 1:
                self.ser.flushInput()

                #time.sleep(3)  # Slightly longer delay between attempts for better syncing
                pass

        return False  # Return False if echo check fails after max attempts
        

    def set_percent_outputs(self, percent_outputs):
        command = "SET PERCENT OUTPUTS:" + ','.join(f"{output:.2f}" for output in percent_outputs)
        return self.send_command_with_echo(command) is not False

    def get_percent_outputs(self):
        command = "GET PERCENT OUTPUTS:"
        response = self.send_command_with_echo(command)
        return np.array([float(value) for value in response.split('=')[1].strip().split(',')]) if response else False

    def set_target_currents(self, target_currents):
        # Flatten to ensure a 1D array for formatting
        target_currents = target_currents.flatten()
        command = "SET TARGET CURRENTS:" + ','.join(f"{current:.2f}" for current in target_currents)
        return self.send_command_with_echo(command) is not False

    def get_target_currents(self):
        command = "GET TARGET CURRENTS:"
        response = self.send_command_with_echo(command)
        return np.array([float(value) for value in response.split('=')[1].strip().split(',')]) if response else False

    def get_measured_currents(self):
        command = "GET MEASURED CURRENTS:"
        response = self.send_command_with_echo(command)
        return np.array([float(value) for value in response.split('=')[1].strip().split(',')]) if response else False

    def reset(self):
        command = "RESET:"
        return self.send_command_with_echo(command) is not False



# Main code to test the functions
if __name__ == "__main__":
    arduino = ArduinoController()



