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
import traceback
import re
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog  # For directory selection
from tkinter import font
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
    'Port 1': {
        "LeftPoke": 17,
        "RightPoke": 27,
        "Pellet": 22,
    },
    'Port 2': {
        "LeftPoke": 10,
        "RightPoke": 9,
        "Pellet": 11,
    },
    'Port 3': {
        "LeftPoke": 0,
        "RightPoke": 5,
        "Pellet": 6,
    },
    'Port 4': {
        "LeftPoke": 13,
        "RightPoke": 19,
        "Pellet": 26,
    },
}

# Set all pins as output and initially set them to LOW
for device_pins in gpio_pins_per_device.values():
    for pin in device_pins.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

# Create a lock for thread-safe access to shared variables
pellet_lock = threading.Lock()

# Track the state of Pellet in Well per port_identifier
pellet_in_well = {}

# Global event to signal threads to stop
stop_event = threading.Event()

# Define the column headers for CSV
column_headers = [
    "Timestamp", "Temp", "Humidity", "Library_Version", "Session_type",
    "Device_Number", "Battery_Voltage", "Motor_Turns", "FR", "Event", "Active_Poke",
    "Left_Poke_Count", "Right_Poke_Count", "Pellet_Count", "Block_Pellet_Count",
    "Retrieval_Time", "InterPelletInterval", "Poke_Time"
]

# Function to send TTL pulse for regular poke events
def send_ttl_signal(pin):
    logging.debug(f"Sending TTL signal to pin {pin}")
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(pin, GPIO.LOW)

# Function to handle the PelletInWell/PelletTaken logic
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

# Function to process each event and send TTLs accordingly
def process_event(event_type, port_identifier, gpio_pins, q):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    message = f"[{timestamp}] {port_identifier} - Event: {event_type}"
    q.put(message)

    if event_type == "Left":
        send_ttl_signal(gpio_pins["LeftPoke"])
        q.put(f"{port_identifier} - Left poke event triggered.")
    elif event_type == "Right":
        send_ttl_signal(gpio_pins["RightPoke"])
        q.put(f"{port_identifier} - Right poke event triggered.")
    elif event_type == "LeftWithPellet":
        send_ttl_signal(gpio_pins["LeftPoke"])
        q.put(f"{port_identifier} - Left poke with pellet, signal triggered.")
    elif event_type == "RightWithPellet":
        send_ttl_signal(gpio_pins["RightPoke"])
        q.put(f"{port_identifier} - Right poke with pellet, signal triggered.")
    elif event_type in ["Pellet", "PelletInWell"]:
        handle_pellet_event(event_type, port_identifier, gpio_pins, q)

# Function to get device mappings based on physical USB ports
def get_device_mappings_by_usb_port():
    device_mappings = []
    usb_port_mapping = {
        'usb-0:1.1': 'Port 1',
        'usb-0:1.2': 'Port 2',
        'usb-0:1.3': 'Port 3',
        'usb-0:1.4': 'Port 4',
    }
    for symlink in os.listdir('/dev/serial/by-path/'):
        symlink_path = os.path.join('/dev/serial/by-path/', symlink)
        serial_port = os.path.realpath(symlink_path)
        if 'ttyACM' in serial_port or 'ttyUSB' in serial_port:
            usb_port_path = get_usb_port_path_from_symlink(symlink)
            if not usb_port_path:
                continue
            port_identifier = usb_port_mapping.get(usb_port_path)
            if port_identifier:
                device_mappings.append({
                    'serial_port': serial_port,
                    'port_identifier': port_identifier,
                })
    return device_mappings

def get_usb_port_path_from_symlink(symlink):
    match = re.search(r'usb-\d+:\d+(\.\d+)*', symlink)
    return match.group() if match else None

# Function to read from serial port (FED3 devices)
def read_from_fed(serial_port, port_identifier, gpio_pins, q):
    try:
        ser = serial.Serial(serial_port, 115200, timeout=1)
        logging.info(f"Opened serial port {serial_port} for {port_identifier}")
        q.put("Ready")
    except serial.SerialException as e:
        q.put(f"Error opening serial port: {e}")
        return
    try:
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
    finally:
        ser.close()

# Splash screen class
class SplashScreen:
    def __init__(self, root, duration=3000):
        self.root = root
        self.root.overrideredirect(True)  # Remove window decorations (title bar, etc.)
        self.root.attributes("-alpha", 1)  # Initially transparent

        # Get the screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Set the window to be centered
        width = 1300
        height = 450
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")


        self.root.configure(bg="black")
        self.root.wm_attributes("-alpha",1)

        # Create a label for the logo text
        self.label = tk.Label(self.root, text="McCutcheonlab Technologies", font=("Helvetica", 62, "bold"), bg= "black", fg= "orange")
        self.label.pack(expand=True)

        # Store the after job ID
        self.after_job = None

        # Start the fade in/out process
        self.fade_in_out(duration)

    def fade_in_out(self, duration):
        fade_in_time = 1000  # 3 seconds to fade in
        fade_out_time = 2000  # 3 seconds to fade out

        self.fade_in(fade_in_time, lambda: self.fade_out(fade_out_time, self.close_splash))

    def fade_in(self, time_ms, callback):
        alpha = 0.0
        increment = 1 / (time_ms // 50)
        def fade():
            nonlocal alpha
            if alpha < 1.0:
                alpha += increment
                self.root.attributes("-alpha", alpha)
                self.after_job = self.root.after(50, fade)
            else:
                callback()
        fade()

    def fade_out(self, time_ms, callback):
        alpha = 1.0
        decrement = 1 / (time_ms // 50)
        def fade():
            nonlocal alpha
            if alpha > 0.0:
                alpha -= decrement
                self.root.attributes("-alpha", alpha)
                self.after_job = self.root.after(50, fade)
            else:
                callback()
        fade()

    def close_splash(self):
        if self.after_job is not None:
            self.root.after_cancel(self.after_job)  # Cancel any pending after jobs
        self.root.destroy()  # Close the splash screen

# Main GUI Application Class
class FED3MonitorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("HPFED DATA MONITOR V.01")
        
        self.port_widgets = {}
        self.port_queues = {}
        self.experimenter_name = tk.StringVar()
        self.experiment_name = tk.StringVar()
        self.save_path = ""

        # To store data during the session
        self.data_to_save = {}

        # Set up the mainframe
        self.mainframe = ttk.Frame(self.root, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)
        
        # Copyright message at the bottom of the window
        self.copyright_label = tk.Label(self.root, text="© McCutcheonlab 2024", fg="blue")
        self.copyright_label.grid(column=0, row=1, sticky=(tk.S), pady=5)

        # Create GUI for each port
        self.setup_ports()

        # Add fields for experimenter and experiment name
        self.create_controls()

        # Add a canvas for the recording indicator
        self.canvas = tk.Canvas(self.mainframe, width=200, height=200)
        self.canvas.grid(column=1, row=4, columnspan=2, padx=5, pady=5)
        self.recording_circle = None
        self.recording_label = None

        # Check for connected devices immediately
        self.check_connected_devices()

        # Start the periodic GUI update function
        self.root.after(100, self.update_gui)

    def setup_ports(self):
        port_names = ['Port 1', 'Port 2', 'Port 3', 'Port 4']
        for idx, port_name in enumerate(port_names):
            frame = ttk.LabelFrame(self.mainframe, text=port_name)
            frame.grid(column=idx, row=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
            status_label = ttk.Label(frame, text="Not Ready", font=("Helvetica", 14, "italic"), foreground="red")
            status_label.grid(column=0, row=0, sticky=tk.W)
            text_widget = tk.Text(frame, width=40, height=20)
            text_widget.grid(column=0, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))

            self.port_widgets[port_name] = {
                'frame': frame,
                'status_label': status_label,
                'text_widget': text_widget
            }
            self.port_queues[port_name] = queue.Queue()

        for idx in range(len(port_names)):
            self.mainframe.columnconfigure(idx, weight=1)

    def create_controls(self):
        # Experimenter name
        tk.Label(self.mainframe, text="Your Name:", font=("Helvetica", 10, "bold")).grid(column=0, row=2, sticky=tk.E, padx=2, pady=2)
        self.experimenter_entry = ttk.Entry(self.mainframe, textvariable=self.experimenter_name)
        self.experimenter_entry.grid(column=1, row=2, sticky=tk.W, padx=2, pady=2)
    
        # Experiment name
        tk.Label(self.mainframe, text="Experiment Name:", font=("Helvetica", 10, "bold")).grid(column=2, row=2, sticky=tk.E, padx=2, pady=2)
        self.experiment_entry = ttk.Entry(self.mainframe, textvariable=self.experiment_name)
        self.experiment_entry.grid(column=3, row=2, sticky=tk.W, padx=2, pady=2)

        # Start button
        self.start_button = tk.Button(self.mainframe, text="START", font=("Helvetica", 15, "bold"), bg="green", fg="white", command=self.start_experiment)
        self.start_button.grid(column=1, row=3, padx=5, pady=10)

        # Stop button
        self.stop_button = tk.Button(self.mainframe, text="STOP(SAVE & QUIT)", font=("Helvetica", 15, "bold"), bg="red", fg="white", command=self.stop_experiment)
        self.stop_button.grid(column=2, row=3, padx=5, pady=10)

        # Browse button for selecting data folder path
        self.browse_button = tk.Button(self.mainframe, text="Browse Data Folder", font=("Helvetica", 15, "bold"), command=self.browse_folder, bg="gold", fg="blue")
        self.browse_button.grid(column=0, row=3, padx=5, pady=10)

    def browse_folder(self):
        # Allow the user to select a directory to save files
        self.save_path = filedialog.askdirectory(title="Select Folder to Save Data")

    def check_connected_devices(self):
        # Check which devices are connected and update status immediately
        self.device_mappings = get_device_mappings_by_usb_port()

        for mapping in self.device_mappings:
            port_identifier = mapping['port_identifier']
            self.port_widgets[port_identifier]['status_label'].config(text="Ready", font=("Helvetica", 15, "bold"), foreground="green")

    def start_experiment(self):
        # Get the current date and time for the folder name and filenames
        current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        
        # Convert experimenter and experiment names to lowercase for case-insensitivity
        experimenter_name = self.experimenter_name.get().lower().strip()
        experiment_name = self.experiment_name.get().lower().strip()
    
        # Create a single folder for the experiment
        experimenter_folder = f"./{experimenter_name}"
        experiment_folder = f"{experimenter_folder}/{experiment_name}_{current_time}"
        os.makedirs(experiment_folder, exist_ok=True)
    
        # Store experiment folder path to use in save_to_csv
        self.experiment_folder = experiment_folder
    
        # Initialize the in-memory data storage for each port
        self.data_to_save = {port_identifier: [] for port_identifier in self.port_widgets.keys()}
    
        # Start reading from the devices
        self.threads = []
        for mapping in self.device_mappings:
            serial_port = mapping['serial_port']
            port_identifier = mapping['port_identifier']
            gpio_pins = gpio_pins_per_device.get(port_identifier)
            if not gpio_pins:
                continue
            q = self.port_queues[port_identifier]
            t = threading.Thread(target=read_from_fed, args=(serial_port, port_identifier, gpio_pins, q))
            t.daemon = True
            t.start()
            self.threads.append(t)

        # Display the green circle and "RECORDING STARTED"
        self.display_recording_indicator()

    def display_recording_indicator(self):
        # Draw a green circle to indicate recording started
        if self.recording_circle is None:
            self.recording_circle = self.canvas.create_oval(50, 50, 150, 150, fill="red")
        if self.recording_label is None:
            self.recording_label = self.canvas.create_text(100, 175, text="RECORDING STARTED", font=("Helvetica", 12, "bold"))

    def hide_recording_indicator(self):
        # Remove the green circle and the label when the recording stops
        if self.recording_circle is not None:
            self.canvas.delete(self.recording_circle)
            self.recording_circle = None
        if self.recording_label is not None:
            self.canvas.delete(self.recording_label)
            self.recording_label = None

    def update_gui(self):
        for port_identifier, q in self.port_queues.items():
            try:
                while True:
                    message = q.get_nowait()
                    if isinstance(message, list):
                        # This is a data list from the FED3 device, accumulate it for logging later
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
        # Clean up threads and save the data
        for t in self.threads:
            t.join()  # Ensure all threads are properly stopped
        GPIO.cleanup()

        # Save all accumulated data at once when the experiment is stopped
        self.save_all_data()

        # Hide the recording indicator
        self.hide_recording_indicator()

        # Close the GUI window properly
        self.root.quit()
        self.root.destroy()

    def save_all_data(self):
        # Save the accumulated data from each port
        current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        # Save to the experiment folder (user-defined structure)
        for port_identifier, data_rows in self.data_to_save.items():
            filename_user = f"{self.experiment_folder}/{port_identifier}.csv"
            with open(filename_user, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(column_headers)  # Write header
                writer.writerows(data_rows)  # Write all accumulated data

        # Save to the user-selected folder (flat structure with date and time)
        if self.save_path:
            for port_identifier, data_rows in self.data_to_save.items():
                filename_selected = f"{self.save_path}/{current_time}_{port_identifier}.csv"
                with open(filename_selected, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(column_headers)  # Write header
                    writer.writerows(data_rows)  # Write all accumulated data


# Main execution
if __name__ == "__main__":
    # Initialize the splash screen first
    splash_root = tk.Tk()
    splash_screen = SplashScreen(splash_root)
    splash_root.after(3000, splash_screen.close_splash)  # Quit splash after 3 seconds (1sec in, 2sec out)
    splash_root.mainloop()  # Display the splash screen

    # After splash screen ends, initialize the main GUI
    root = tk.Tk()
    app = FED3MonitorApp(root)
    root.mainloop()


# In[ ]:




