#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python3

import os
import sys
import RPi.GPIO as GPIO
import serial
import threading
import datetime
import time
import logging
import re
import tkinter as tk
from tkinter import ttk, filedialog
import queue
import csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)

# Setup GPIO pins on the Raspberry Pi (BCM mode)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define GPIO pins for each device 
gpio_pins_per_device = {
    'Port 1': {"LeftPoke": 17, "RightPoke": 27, "Pellet": 22},
    'Port 2': {"LeftPoke": 10, "RightPoke": 9, "Pellet": 11},
    'Port 3': {"LeftPoke": 0, "RightPoke": 5, "Pellet": 6},
    'Port 4': {"LeftPoke": 13, "RightPoke": 19, "Pellet": 26},
}

# Set all pins as output and initially set them to LOW
for device_pins in gpio_pins_per_device.values():
    for pin in device_pins.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

# Define global threading and data storage variables
pellet_lock = threading.Lock()
pellet_in_well = {}
stop_event = threading.Event()
column_headers = [
    "Timestamp", "Temp", "Humidity", "Library_Version", "Session_type",
    "Device_Number", "Battery_Voltage", "Motor_Turns", "FR", "Event", "Active_Poke",
    "Left_Poke_Count", "Right_Poke_Count", "Pellet_Count", "Block_Pellet_Count",
    "Retrieval_Time", "InterPelletInterval", "Poke_Time"
]

def send_ttl_signal(pin):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(pin, GPIO.LOW)

# Handle pellet events
def handle_pellet_event(event_type, port_identifier, gpio_pins, q):
    global pellet_in_well
    with pellet_lock:
        if port_identifier not in pellet_in_well:
            pellet_in_well[port_identifier] = False
        if event_type == "Pellet":
            if pellet_in_well[port_identifier]:
                GPIO.output(gpio_pins["Pellet"], GPIO.LOW)
                q.put(f"Pellet taken, signal turned OFF.")
                pellet_in_well[port_identifier] = False
                send_ttl_signal(gpio_pins["Pellet"])
            else:
                q.put(f"No pellet was in the well, no signal for pellet taken.")
        elif event_type == "PelletInWell":
            GPIO.output(gpio_pins["Pellet"], GPIO.HIGH)
            pellet_in_well[port_identifier] = True
            q.put(f"Pellet dispensed in well, signal ON.")

def process_event(event_type, port_identifier, gpio_pins, q):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    message = f"[{timestamp}] {port_identifier} - Event: {event_type}"
    q.put(message)
    if event_type == "Left":
        send_ttl_signal(gpio_pins["LeftPoke"])
    elif event_type == "Right":
        send_ttl_signal(gpio_pins["RightPoke"])
    elif event_type == "LeftWithPellet":
        send_ttl_signal(gpio_pins["LeftPoke"])
    elif event_type == "RightWithPellet":
        send_ttl_signal(gpio_pins["RightPoke"])
    elif event_type in ["Pellet", "PelletInWell"]:
        handle_pellet_event(event_type, port_identifier, gpio_pins, q)

def get_device_mappings_by_usb_port():
    device_mappings = []
    usb_port_mapping = {'usb-0:1.1': 'Port 1', 'usb-0:1.2': 'Port 2', 'usb-0:1.3': 'Port 3', 'usb-0:1.4': 'Port 4'}
    for symlink in os.listdir('/dev/serial/by-path/'):
        symlink_path = os.path.join('/dev/serial/by-path/', symlink)
        serial_port = os.path.realpath(symlink_path)
        if 'ttyACM' in serial_port or 'ttyUSB' in serial_port:
            usb_port_path = get_usb_port_path_from_symlink(symlink)
            if usb_port_path in usb_port_mapping:
                device_mappings.append({'serial_port': serial_port, 'port_identifier': usb_port_mapping[usb_port_path]})
    return device_mappings

def get_usb_port_path_from_symlink(symlink):
    match = re.search(r'usb-\d+:\d+(\.\d+)*', symlink)
    return match.group() if match else None

def read_from_fed(serial_port, port_identifier, gpio_pins, q):
    try:
        ser = serial.Serial(serial_port, 115200, timeout=1)
        q.put("Ready")
        while not stop_event.is_set():
            line = ser.readline().decode('utf-8').strip()
            if line:
                data_list = line.split(",")
                q.put(f"{port_identifier} raw data: {data_list}")
                if len(data_list) >= 10:
                    event_type = data_list[9]
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    data_list[0] = timestamp
                    process_event(event_type, port_identifier, gpio_pins, q)
                    q.put(data_list)
    except serial.SerialException:
        q.put(f"Error opening serial port: {serial_port}")
    finally:
        ser.close()

class SplashScreen:
    def __init__(self, root, duration=3000):
        self.root = root
        self.root.overrideredirect(True)
        self.root.geometry("800x480")
        self.root.attributes("-fullscreen", True)

        self.root.configure(bg="black")
        self.label = tk.Label(self.root, text="McCutcheonlab Technologies", font=("Cascadia Code", 28, "bold"), bg="black", fg="lavender")
        self.label.pack(expand=True)
        self.root.after(duration, self.close_splash)

    def close_splash(self):
        self.root.destroy()

class FED3MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HPFED TTL Monitor")
        self.root.geometry("800x480")
        self.root.attributes("-fullscreen", True)

        self.port_widgets = {}
        self.port_queues = {}
        self.experimenter_name = tk.StringVar()
        self.experiment_name = tk.StringVar()
        self.save_path = ""
        self.data_to_save = {}
        self.threads = []  # Initialize threads list

        # Mainframe layout
        self.mainframe = ttk.Frame(self.root)
        self.mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Layout Setup
        self.create_layout()
        self.check_connected_devices()
        self.root.after(100, self.update_gui)

    def create_layout(self):
        # Left side: Port 1 and Port 2
        left_ports = ttk.Frame(self.mainframe)
        left_ports.grid(column=0, row=0, sticky=(tk.N, tk.S, tk.W))

        self.setup_port(left_ports, 'Port 1', 0)
        self.setup_port(left_ports, 'Port 2', 1)

        # Right side: Port 3 and Port 4
        right_ports = ttk.Frame(self.mainframe)
        right_ports.grid(column=2, row=0, sticky=(tk.N, tk.S, tk.E))

        self.setup_port(right_ports, 'Port 3', 0)
        self.setup_port(right_ports, 'Port 4', 1)

        # Center controls
        controls_frame = ttk.Frame(self.mainframe)
        controls_frame.grid(column=1, row=0, padx=10, sticky=(tk.N, tk.S))

        tk.Label(controls_frame, text="Your Name:", font=("Cascadia Code", 8)).grid(column=0, row=0, sticky=tk.W)
        self.experimenter_entry = ttk.Entry(controls_frame, textvariable=self.experimenter_name, width=20)
        self.experimenter_entry.grid(column=1, row=0, sticky=tk.W)

        tk.Label(controls_frame, text="Experiment Name:", font=("Cascadia Code", 8)).grid(column=0, row=1, sticky=tk.W)
        self.experiment_entry = ttk.Entry(controls_frame, textvariable=self.experiment_name, width=20)
        self.experiment_entry.grid(column=1, row=1, sticky=tk.W)

        # Start and Stop buttons
        self.start_button = tk.Button(controls_frame, text="START", font=("Cascadia Code", 9, "bold"), bg="green", fg="white", command=self.start_experiment)
        self.start_button.grid(column=0, row=2, columnspan=2, sticky="we", pady=5)

        self.stop_button = tk.Button(controls_frame, text="STOP & SAVE", font=("Cascadia Code", 9, "bold"), bg="red", fg="white", command=self.stop_experiment)
        self.stop_button.grid(column=0, row=3, columnspan=2, sticky="we", pady=5)

        # Browse button
        self.browse_button = tk.Button(controls_frame, text="Browse Data Folder", font=("Cascadia Code", 9), command=self.browse_folder)
        self.browse_button.grid(column=0, row=4, columnspan=2, sticky="we", pady=5)

        # Recording Indicator
        self.canvas = tk.Canvas(controls_frame, width=120, height=100)
        self.canvas.grid(column=0, row=5, columnspan=2, pady=8)
        self.recording_circle = None  # Initialize as None
        self.recording_label = None   # Initialize as None

        # Footer copyright message
        self.mainframe.grid_rowconfigure(1, weight=1)
        copyright_label = tk.Label(self.mainframe, text="© 2024 McCutcheonlab | UiT | Norway", font=("Cascadia Code", 8), fg="black")
        copyright_label.grid(column=0, row=2, columnspan=3, sticky="s", pady=5)

    def setup_port(self, parent, port_name, row):
        frame = ttk.LabelFrame(parent, text=port_name, padding="3")
        frame.grid(column=0, row=row, padx=5, pady=5, sticky=(tk.N, tk.S, tk.W, tk.E))
        status_label = ttk.Label(frame, text="Not Ready", font=("Cascadia Code", 10), foreground="red")
        status_label.grid(column=0, row=0, sticky=tk.W)
        text_widget = tk.Text(frame, width=28, height=6, wrap=tk.WORD)
        text_widget.grid(column=0, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.port_widgets[port_name] = {'status_label': status_label, 'text_widget': text_widget}
        self.port_queues[port_name] = queue.Queue()

    def browse_folder(self):
        self.save_path = filedialog.askdirectory(title="Select Folder to Save Data")

    def check_connected_devices(self):
        device_mappings = get_device_mappings_by_usb_port()
        for mapping in device_mappings:
            port_identifier = mapping['port_identifier']
            self.port_widgets[port_identifier]['status_label'].config(text="Ready", foreground="green")

    def display_recording_indicator(self):
        if self.recording_circle is None:
            self.recording_circle = self.canvas.create_oval(10, 10, 50, 50, fill="red")
        if self.recording_label is None:
            self.recording_label = self.canvas.create_text(39, 60, text="RECORDING", font=("Cascadia Code", 10),anchor= "n")

    def hide_recording_indicator(self):
        if self.recording_circle is not None:
            self.canvas.delete(self.recording_circle)
            self.recording_circle = None
        if self.recording_label is not None:
            self.canvas.delete(self.recording_label)
            self.recording_label = None

    def start_experiment(self):
        self.experimenter_entry.config(state='disabled')
        self.experiment_entry.config(state='disabled')
        
        self.experimenter_name.set(self.experimenter_name.get().strip().lower())
        self.experiment_name.set(self.experiment_name.get().strip().lower())
        self.data_to_save = {port_identifier: [] for port_identifier in self.port_widgets.keys()}
        self.threads = []  # Initialize threads list
        for mapping in get_device_mappings_by_usb_port():
            serial_port = mapping['serial_port']
            port_identifier = mapping['port_identifier']
            gpio_pins = gpio_pins_per_device.get(port_identifier)
            q = self.port_queues[port_identifier]
            t = threading.Thread(target=read_from_fed, args=(serial_port, port_identifier, gpio_pins, q))
            t.daemon = True
            t.start()
            self.threads.append(t)  # Store thread in self.threads
        self.display_recording_indicator()

    def update_gui(self):
        for port_identifier, q in self.port_queues.items():
            try:
                while True:
                    message = q.get_nowait()
                    if isinstance(message, list):
                        self.data_to_save[port_identifier].append(message)
                    elif message == "Ready":
                        self.port_widgets[port_identifier]['status_label'].config(text="Ready", foreground="green")
                    else:
                        text_widget = self.port_widgets[port_identifier]['text_widget']
                        text_widget.insert(tk.END, message + "\n")
                        text_widget.see(tk.END)
            except queue.Empty:
                pass
        self.root.after(100, self.update_gui)

    def stop_experiment(self):
        stop_event.set()
        for t in self.threads:
            t.join()
        GPIO.cleanup()
        self.save_all_data()
        self.hide_recording_indicator()
        self.root.quit()
        self.root.destroy()

    def save_all_data(self):
        current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        experimenter_folder = os.path.join(self.save_path, self.experimenter_name.get().strip())
        experiment_folder = os.path.join(experimenter_folder, f"{self.experiment_name.get().strip()}_{current_time}")
        os.makedirs(experiment_folder, exist_ok=True)
        for port_identifier, data_rows in self.data_to_save.items():
            # Save data in the experiment folder with folder structures
            filename_user = os.path.join(experiment_folder, f"{port_identifier}_{current_time}.csv")
            with open(filename_user, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(column_headers)
                writer.writerows(data_rows)

            # Save data directly into save_path without folder structures
            filename_main = os.path.join(self.save_path, f"{current_time}_{port_identifier}.csv")
            with open(filename_main, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(column_headers)
                writer.writerows(data_rows)

if __name__ == "__main__":
    splash_root = tk.Tk()
    splash_screen = SplashScreen(splash_root)
    splash_root.mainloop()

    root = tk.Tk()
    app = FED3MonitorApp(root)
    root.mainloop()


# In[ ]:




