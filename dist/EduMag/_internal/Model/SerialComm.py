import serial
import serial.tools.list_ports
import time
import numpy as np

class Serial:
    def __init__(self):
        self.port = None
        self.baudrate = None
        self.timeout = None
        self.ser =  None

    def open(self, port, baudrate=115200, timeout=0.1):
        """Open the serial port."""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            return "Serial Port Connected"

        except serial.SerialException as e:
            self.ser = None
            return (f"Error opening serial port {self.port}: {e}")

    def close(self):
        """Close the serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.__init__()
        
        return "Serial Closed"

    def send(self, I):
        """Send data over the serial port."""
        I_String = str(I[0]) + ' ' + str(I[1]) + ' ' + str(I[2]) + ' ' + str(I[3]) + ' ' + str(0.00) + '\n'
        
        if np.prod(np.abs(I) < 4):              
            self.ser.write(I_String.encode())
            #print(I_String.encode())
            
        else:
            print("Warning: High Currents!")

    def receive(self):
        """Receive data from the serial port."""
        if self.ser and self.ser.is_open:
            try:
                data = self.ser.read_until().decode('utf-8').strip()
                print(f"Received data: {data}")
                return data
            except serial.SerialException as e:
                print(f"Error reading from serial port {self.port}: {e}")
                return None
        return None


    def list_ports(self):
        """List all available serial ports."""
        ports = serial.tools.list_ports.comports()
        available_ports = [port.device for port in ports]
        print(f"Available serial ports: {available_ports}")
        return available_ports

    def __enter__(self):
        """Support for with-statement context manager."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Support for with-statement context manager."""
        self.close()

