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
from tkinter import ttk, filedialog, messagebox
import queue
import csv
import webbrowser

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
    'Port 2': {"LeftPoke": 10, "RightPoke": 9,  "Pellet": 11},
    'Port 3': {"LeftPoke": 0,  "RightPoke": 5,  "Pellet": 6},
    'Port 4': {"LeftPoke": 13, "RightPoke": 19, "Pellet": 26},
    'Port 5': {"LeftPoke": 14, "RightPoke": 15, "Pellet": 18},
    'Port 6': {"LeftPoke": 23, "RightPoke": 24, "Pellet": 25},
    'Port 7': {"LeftPoke": 8,  "RightPoke": 7,  "Pellet": 1},
    'Port 8': {"LeftPoke": 12, "RightPoke": 16, "Pellet": 20},
}

# Set all pins as output and initially set them to LOW
for device_pins in gpio_pins_per_device.values():
    for pin in device_pins.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

# Global threading and data storage variables
pellet_lock = threading.Lock()
pellet_in_well = {}
stop_event = threading.Event()

column_headers = [
    "Timestamp", "Temp", "Humidity", "Library_Version", "Session_type",
    "Device_Number", "Battery_Voltage", "Motor_Turns", "FR", "Event", "Active_Poke",
    "Left_Poke_Count", "Right_Poke_Count", "Pellet_Count", "Block_Pellet_Count",
    "Retrieval_Time", "InterPelletInterval", "Poke_Time"
]

# Global known devices dictionary: {serial_path: "Port X"}
known_devices = {}
port_names = [f"Port {i}" for i in range(1,9)]

def send_ttl_signal(pin):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(pin, GPIO.LOW)

def handle_pellet_event(event_type, port_identifier, gpio_pins, q):
    global pellet_in_well
    with pellet_lock:
        if port_identifier not in pellet_in_well:
            pellet_in_well[port_identifier] = False
        if event_type == "Pellet":
            if pellet_in_well[port_identifier]:
                GPIO.output(gpio_pins["Pellet"], GPIO.LOW)
                q.put("Pellet taken, signal turned OFF.")
                pellet_in_well[port_identifier] = False
                send_ttl_signal(gpio_pins["Pellet"])
                q.put(f"TTL signal sent on {port_identifier} for {event_type}")
            else:
                q.put("No pellet was in the well, no signal for pellet taken.")
        elif event_type == "PelletInWell":
            GPIO.output(gpio_pins["Pellet"], GPIO.HIGH)
            pellet_in_well[port_identifier] = True
            q.put("Pellet dispensed in well, signal ON.")

def process_event(event_type, port_identifier, gpio_pins, q, app):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    message = f"[{timestamp}] {port_identifier} - Event: {event_type}"
    q.put(message)

    event_type = event_type.strip()

    if event_type == "Left":
        send_ttl_signal(gpio_pins["LeftPoke"])
        q.put(f"TTL signal sent on {port_identifier} for {event_type}")
    elif event_type == "Right":
        send_ttl_signal(gpio_pins["RightPoke"])
        q.put(f"TTL signal sent on {port_identifier} for {event_type}")
    elif event_type == "LeftWithPellet":
        send_ttl_signal(gpio_pins["LeftPoke"])
        q.put(f"TTL signal sent on {port_identifier} for {event_type}")
    elif event_type == "RightWithPellet":
        send_ttl_signal(gpio_pins["RightPoke"])
        q.put(f"TTL signal sent on {port_identifier} for {event_type}")
    elif event_type in ["Pellet", "PelletInWell"]:
        handle_pellet_event(event_type, port_identifier, gpio_pins, q)

    if event_type in ["Right", "Left", "Pellet", "PelletInWell", "RightWithPellet", "LeftWithPellet"]:
        app.trigger_indicator(port_identifier)

def get_current_serial_devices():
    by_path_dir = '/dev/serial/by-path/'
    if not os.path.exists(by_path_dir):
        return []
    serial_devices = []
    for symlink in os.listdir(by_path_dir):
        symlink_path = os.path.join(by_path_dir, symlink)
        serial_port = os.path.realpath(symlink_path)
        if 'ttyACM' in serial_port or 'ttyUSB' in serial_port:
            serial_devices.append(serial_port)
    serial_devices.sort()
    return serial_devices

def get_device_mappings_by_usb_port():
    # Return mappings for only known devices that are currently connected.
    device_mappings = []
    serial_devices = get_current_serial_devices()
    for dev in serial_devices:
        if dev in known_devices:
            device_mappings.append({
                'serial_port': dev,
                'port_identifier': known_devices[dev]
            })
    return device_mappings

def read_from_fed(serial_port, port_identifier, gpio_pins, q, status_label, app):
    try:
        ser = serial.Serial(serial_port, 115200, timeout=1)
        q.put("Ready")
        status_label.config(text="Connected", foreground="green")
        while not stop_event.is_set():
            try:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    data_list = line.split(",")
                    q.put(f"{port_identifier} raw data: {data_list}")
                    if len(data_list) >= 10:
                        event_type = data_list[9].strip()
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        data_list[0] = timestamp
                        process_event(event_type, port_identifier, gpio_pins, q, app)
                        q.put(data_list)
            except serial.SerialException:
                q.put(f"Device on {port_identifier} disconnected.")
                status_label.config(text="Not Connected", foreground="red")
                break
    except serial.SerialException:
        q.put(f"Error opening serial port: {serial_port}")
        status_label.config(text="Not Connected", foreground="red")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
        q.put(f"Stopped reading from {port_identifier}")

def identification_thread(serial_port, port_identifier, q, status_label, app, stop_event):
    try:
        ser = serial.Serial(serial_port, 115200, timeout=0.1)
        status_label.config(text="Connected", foreground="violet")
        while not stop_event.is_set():
            try:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    data_list = line.split(",")
                    if len(data_list) >= 10:
                        event_type = data_list[9].strip()
                        if event_type in ["Right","Pellet", "Left"]:
                            app.trigger_indicator(port_identifier)
            except serial.SerialException:
                status_label.config(text="Not Connected", foreground="red")
                break
    except serial.SerialException:
        status_label.config(text="Not Connected", foreground="red")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

class SplashScreen:
    def __init__(self, root, duration=3000):
        self.root = root
        self.root.overrideredirect(True)
        self.root.configure(bg="black")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.label = tk.Label(self.root, text="McCutcheonlab Technologies\n RTFED PiTTL System", font=("Cascadia Code", 32, "bold"), bg="black", fg="lavender")
        self.label.pack(expand=True)
        self.root.after(duration, self.close_splash)

    def close_splash(self):
        self.root.destroy()

class FED3MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RTFED PiTTL")
        self.root.geometry("1200x800")

        self.port_widgets = {}
        self.port_queues = {}
        self.experimenter_name = tk.StringVar()
        self.experiment_name = tk.StringVar()
        self.save_path = ""
        self.flat_data_path = ""
        self.data_to_save = {}
        self.threads = []
        self.connected_ports = []
        self.serial_ports = {}
        self.logging_active = False
        self.last_device_check_time = time.time()

        self.identification_threads = {}
        self.identification_stop_events = {}

        self.stop_event = stop_event

        # Perform initial stable device mapping
        self.perform_initial_device_mapping()

        self.mainframe = ttk.Frame(self.root)
        self.mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.create_layout()
        self.check_connected_devices()
        self.start_identification_threads_for_connected()

        # Show port mapping message shortly after GUI load
        self.root.after(500, self.show_port_mapping_message)

        self.update_gui()
        self.root.after(5000, self.refresh_device_status)  # periodic check
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def perform_initial_device_mapping(self):
        # Discover devices at startup and assign stable ports in alphabetical order.
        serial_devices = get_current_serial_devices()
        # Assign to known_devices if not already assigned, in order
        i = 0
        for dev in serial_devices:
            if dev not in known_devices and i < len(port_names):
                known_devices[dev] = port_names[i]
                i += 1
        # After this initial assignment, no new devices will be assigned to ports.

    def show_port_mapping_message(self):
        message = (
            "1) Make poke or trigger pellet sensor on FED3 units to identify the assigned ports\n2)In case you need to restart a FED3 after pressing START, do it one at a time\n3)Ports are assigned based on the initial detection when this program started.\n4)"
            "The GPIO pin mapping of RTFED PiTTL for Raspberry Pi 4B is as follows:\n\n"
            "Port 1: Left=17, Right=27, Pellet=22\n"
            "Port 2: Left=10, Right=9,  Pellet=11\n"
            "Port 3: Left=0,  Right=5,  Pellet=6\n"
            "Port 4: Left=13, Right=19, Pellet=26\n"
            "Port 5: Left=14, Right=15, Pellet=18\n"
            "Port 6: Left=23, Right=24, Pellet=25\n"
            "Port 7: Left=8,  Right=7,  Pellet=1\n"
            "Port 8: Left=12, Right=16, Pellet=20\n"
        )
        messagebox.showinfo("Port Assignment & GPIO Pins", message)

    def create_layout(self):
        ports_frame = ttk.Frame(self.mainframe)
        ports_frame.grid(column=0, row=0, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
        ports_frame.grid_columnconfigure((0,1), weight=1)
        for i in range(4):
            ports_frame.grid_rowconfigure(i, weight=1)

        # Setup 8 ports always
        self.setup_port(ports_frame, 'Port 1', 0, 0)
        self.setup_port(ports_frame, 'Port 2', 0, 1)
        self.setup_port(ports_frame, 'Port 3', 1, 0)
        self.setup_port(ports_frame, 'Port 4', 1, 1)
        self.setup_port(ports_frame, 'Port 5', 2, 0)
        self.setup_port(ports_frame, 'Port 6', 2, 1)
        self.setup_port(ports_frame, 'Port 7', 3, 0)
        self.setup_port(ports_frame, 'Port 8', 3, 1)

        controls_frame = ttk.Frame(self.mainframe)
        controls_frame.grid(column=1, row=0, padx=10, pady=10, sticky=(tk.N, tk.S))
        tk.Label(controls_frame, text="Your Name:", font=("Cascadia Code", 12, "bold")).grid(column=0, row=0, sticky=tk.W, pady=5)
        self.experimenter_entry = ttk.Entry(controls_frame, textvariable=self.experimenter_name, width=20)
        self.experimenter_entry.grid(column=1, row=0, sticky=tk.W, pady=5)

        tk.Label(controls_frame, text="Experiment Name:", font=("Cascadia Code", 12, "bold")).grid(column=0, row=1, sticky=tk.W, pady=5)
        self.experiment_entry = ttk.Entry(controls_frame, textvariable=self.experiment_name, width=20)
        self.experiment_entry.grid(column=1, row=1, sticky=tk.W, pady=5)

        browse_main_button = tk.Button(controls_frame, text="Browse Experiment Folder", font=("Cascadia Code", 10), command=self.browse_folder, bg="gold")
        browse_main_button.grid(column=0, row=2, columnspan=2, sticky="we", pady=5)

        browse_flat_button = tk.Button(controls_frame, text="Browse Flat Data Folder", font=("Cascadia Code", 10), command=self.browse_flat_folder, bg="lightblue")
        browse_flat_button.grid(column=0, row=3, columnspan=2, sticky="we", pady=5)

        self.start_button = tk.Button(controls_frame, text="START", font=("Cascadia Code", 12, "bold"), bg="green", fg="white", command=self.start_experiment)
        self.start_button.grid(column=0, row=4, columnspan=2, sticky="we", pady=10)

        self.stop_button = tk.Button(controls_frame, text="STOP & SAVE", font=("Cascadia Code", 12, "bold"), bg="red", fg="white", command=self.stop_experiment)
        self.stop_button.grid(column=0, row=5, columnspan=2, sticky="we", pady=10)

        self.canvas = tk.Canvas(controls_frame, width=120, height=120)
        self.canvas.grid(column=0, row=6, columnspan=2, pady=20)
        self.recording_circle = None
        self.recording_label = None

        log_frame = ttk.Frame(self.mainframe)
        log_frame.grid(column=0, row=1, columnspan=2, pady=10, sticky=(tk.N, tk.S, tk.E, tk.W))
        log_frame.grid_columnconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=10, width=130, font=("Cascadia Code", 10))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        bottom_frame = ttk.Frame(self.mainframe)
        bottom_frame.grid(column=0, row=2, columnspan=2, pady=10, sticky=(tk.S, tk.E, tk.W))

        footer_label = tk.Label(bottom_frame, text="© 2024 McCutcheonlab | UiT | Norway", font=("Cascadia Code", 10), fg="black")
        footer_label.pack(pady=5)
        hyperlink_label = tk.Label(bottom_frame, text="Developed by Hamid Taghipourbibalan", font=("Cascadia Code", 10, "italic"), fg="blue", cursor="hand2")
        hyperlink_label.pack(pady=5)
        hyperlink_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.linkedin.com/in/hamid-taghipourbibalan-b7239088/"))

    def setup_port(self, parent, port_name, r, c):
        frame = ttk.LabelFrame(parent, text=port_name, padding="3")
        frame.grid(column=c, row=r, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
        status_label = ttk.Label(frame, text="Not Connected", font=("Cascadia Code", 10), foreground="red")
        status_label.grid(column=0, row=0, sticky=tk.W)

        indicator_canvas = tk.Canvas(frame, width=20, height=20)
        indicator_canvas.grid(column=1, row=0, padx=5)
        indicator_circle = indicator_canvas.create_oval(5, 5, 15, 15, fill="gray")

        text_widget = tk.Text(frame, width=40, height=6, wrap=tk.WORD, font=("Cascadia Code", 9))
        text_widget.grid(column=0, row=1, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W))

        self.port_widgets[port_name] = {
            'status_label': status_label,
            'text_widget': text_widget,
            'indicator_canvas': indicator_canvas,
            'indicator_circle': indicator_circle
        }
        self.port_queues[port_name] = queue.Queue()

    def browse_folder(self):
        self.save_path = filedialog.askdirectory(title="Select Experiment Folder")

    def browse_flat_folder(self):
        self.flat_data_path = filedialog.askdirectory(title="Select Flat Data Folder")

    def check_connected_devices(self):
        device_mappings = get_device_mappings_by_usb_port()
        current_ports = [m['port_identifier'] for m in device_mappings]

        # Update connected_ports based on actual devices present
        for m in device_mappings:
            port_identifier = m['port_identifier']
            if port_identifier not in self.connected_ports:
                self.connected_ports.append(port_identifier)
            self.port_widgets[port_identifier]['status_label'].config(text="Connected", foreground="green")
            
            # If logging is active and the port reappears after disconnection, restart logging if needed
            if self.logging_active and port_identifier not in self.serial_ports:
                # Device reconnected during recording
                logging.info(f"Device {port_identifier} reconnected during experiment, restarting logging thread.")
                self.start_logging_for_port(m['serial_port'], port_identifier)

        # Disconnected devices
        for port_name in list(self.connected_ports):
            if port_name not in current_ports:
                self.connected_ports.remove(port_name)
                self.port_widgets[port_name]['status_label'].config(text="Not Connected", foreground="red")
                if port_name in self.serial_ports:
                    del self.serial_ports[port_name]
                if port_name in self.identification_threads:
                    self.identification_stop_events[port_name].set()
                    self.identification_threads[port_name].join()
                    del self.identification_threads[port_name]
                    del self.identification_stop_events[port_name]

    def refresh_device_status(self):
        self.check_connected_devices()
        self.root.after(5000, self.refresh_device_status)

    def display_recording_indicator(self):
        if self.recording_circle is None:
            self.recording_circle = self.canvas.create_oval(10, 10, 50, 50, fill="red")
        if self.recording_label is None:
            self.recording_label = self.canvas.create_text(40, 70, text="RECORDING", font=("Cascadia Code", 10), anchor="n")

    def hide_recording_indicator(self):
        if self.recording_circle is not None:
            self.canvas.delete(self.recording_circle)
            self.recording_circle = None
        if self.recording_label is not None:
            self.canvas.delete(self.recording_label)
            self.recording_label = None

    def start_identification_threads_for_connected(self):
        device_mappings = get_device_mappings_by_usb_port()
        for m in device_mappings:
            port_identifier = m['port_identifier']
            serial_port = m['serial_port']
            # Only start identification threads if we are not logging yet
            if port_identifier not in self.serial_ports and port_identifier not in self.identification_threads and not self.logging_active:
                self.start_identification_thread(serial_port, port_identifier)

    def start_identification_thread(self, serial_port, port_identifier):
        logging.info(f"Starting identification thread for {port_identifier}")
        stop_event_local = threading.Event()
        self.identification_stop_events[port_identifier] = stop_event_local
        q = self.port_queues[port_identifier]
        status_label = self.port_widgets[port_identifier]['status_label']
        t = threading.Thread(target=identification_thread, args=(serial_port, port_identifier, q, status_label, self, stop_event_local))
        t.daemon = True
        t.start()
        self.identification_threads[port_identifier] = t

    def start_experiment(self):
        if not self.connected_ports:
            messagebox.showwarning("No Devices", "No FED3 devices are connected.")
            return

        if not self.experimenter_name.get() or not self.experiment_name.get():
            messagebox.showerror("Error", "Please provide your name and experiment name.")
            return
        if not self.save_path or not self.flat_data_path:
            messagebox.showerror("Error", "Please provide both Experiment Folder and Flat Data Folder.")
            return

        self.experimenter_entry.config(state='disabled')
        self.experiment_entry.config(state='disabled')
        self.start_button.config(state='disabled')

        self.logging_active = True
        self.experimenter_name.set(self.experimenter_name.get().strip().lower())
        self.experiment_name.set(self.experiment_name.get().strip().lower())
        for p in self.port_widgets.keys():
            self.data_to_save[p] = []

        current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        experimenter_name = re.sub(r'[<>:"/\\|?*]', '_', self.experimenter_name.get())
        experiment_name = re.sub(r'[<>:"/\\|?*]', '_', self.experiment_name.get())
        experimenter_folder = os.path.join(self.save_path, experimenter_name)
        self.experiment_folder = os.path.join(experimenter_folder, f"{experiment_name}_{current_time}")
        os.makedirs(self.experiment_folder, exist_ok=True)

        self.stop_identification_threads()

        device_mappings = get_device_mappings_by_usb_port()
        for m in device_mappings:
            port_identifier = m['port_identifier']
            serial_port = m['serial_port']
            self.start_logging_for_port(serial_port, port_identifier)

        self.display_recording_indicator()

    def start_logging_for_port(self, serial_port, port_identifier):
        if port_identifier in self.serial_ports:
            return
        gpio_pins = gpio_pins_per_device.get(port_identifier)
        if not gpio_pins:
            return
        q = self.port_queues[port_identifier]
        status_label = self.port_widgets[port_identifier]['status_label']
        logging.info(f"Starting logging thread for {port_identifier} on {serial_port}")
        t = threading.Thread(target=read_from_fed, args=(serial_port, port_identifier, gpio_pins, q, status_label, self))
        t.daemon = True
        t.start()
        self.threads.append(t)
        self.serial_ports[port_identifier] = serial_port

    def stop_identification_threads(self):
        for port, event in list(self.identification_stop_events.items()):
            event.set()
        for port, t in list(self.identification_threads.items()):
            t.join()
            del self.identification_threads[port]
            del self.identification_stop_events[port]

    def update_gui(self):
        for port_identifier, q in self.port_queues.items():
            try:
                while True:
                    message = q.get_nowait()
                    if isinstance(message, list):
                        self.data_to_save[port_identifier].append(message)
                    elif message == "Ready":
                        self.port_widgets[port_identifier]['status_label'].config(text="Connected", foreground="green")
                    else:
                        text_widget = self.port_widgets[port_identifier]['text_widget']
                        text_widget.insert(tk.END, message + "\n")
                        text_widget.see(tk.END)
                        self.log_text.insert(tk.END, f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
                        self.log_text.see(tk.END)
            except queue.Empty:
                pass

        current_time = time.time()
        if current_time - self.last_device_check_time >= 5:
            self.check_connected_devices()
            self.last_device_check_time = current_time

        self.root.after(100, self.update_gui)

    def stop_experiment(self):
        if not self.logging_active:
            self.root.quit()
            self.root.destroy()
            return

        stop_event.set()
        for t in self.threads:
            t.join()
        GPIO.cleanup()
        self.save_all_data()
        self.hide_recording_indicator()
        self.logging_active = False
        messagebox.showinfo("Data Saved", "All data has been saved.")
        self.root.quit()
        self.root.destroy()

    def save_all_data(self):
        for port_identifier, data_rows in self.data_to_save.items():
            if data_rows:
                filename_user = os.path.join(self.experiment_folder, f"{port_identifier}.csv")
                try:
                    with open(filename_user, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(column_headers)
                        writer.writerows(data_rows)
                    logging.info(f"Data saved for {port_identifier} in {filename_user}")
                except Exception as e:
                    logging.error(f"Failed to save data for {port_identifier}: {e}")

                flat_filename = os.path.join(self.flat_data_path, f"{port_identifier}_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv")
                try:
                    with open(flat_filename, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(column_headers)
                        writer.writerows(data_rows)
                    logging.info(f"Flat copy saved for {port_identifier} in {flat_filename}")
                except Exception as e:
                    logging.error(f"Failed to save flat copy for {port_identifier}: {e}")
            else:
                logging.info(f"No data collected from {port_identifier}, no file saved.")

    def on_closing(self):
        if self.logging_active:
            if messagebox.askokcancel("Quit", "Logging is active. Do you want to stop and exit?"):
                self.stop_experiment()
        else:
            self.stop_identification_threads()
            self.root.quit()
            self.root.destroy()

    def trigger_indicator(self, port_identifier):
        indicator_canvas = self.port_widgets[port_identifier]['indicator_canvas']
        indicator_circle = self.port_widgets[port_identifier]['indicator_circle']
        def blink(times):
            if times > 0:
                current_color = indicator_canvas.itemcget(indicator_circle, 'fill')
                next_color = 'red' if current_color == 'gray' else 'gray'
                indicator_canvas.itemconfig(indicator_circle, fill=next_color)
                self.root.after(250, lambda: blink(times -1))
            else:
                indicator_canvas.itemconfig(indicator_circle, fill='gray')
        blink(6)

if __name__ == "__main__":
    splash_root = tk.Tk()
    splash_screen = SplashScreen(splash_root)
    splash_root.mainloop()

    root = tk.Tk()
    app = FED3MonitorApp(root)
    root.mainloop()

