#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import threading
import datetime
import csv
import gspread
from google.oauth2.service_account import Credentials
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial
import serial.tools.list_ports
import queue
import time
import re
import cv2
import webbrowser

# Column headers
column_headers = [
    "MM/DD/YYYY hh:mm:ss.SSS", "Temp", "Humidity", "Library_Version", "Session_type",
    "Device_Number", "Battery_Voltage", "Motor_Turns", "FR", "Event", "Active_Poke",
    "Left_Poke_Count", "Right_Poke_Count", "Pellet_Count", "Block_Pellet_Count",
    "Retrieval_Time", "InterPelletInterval", "Poke_Time"
]

# Google Sheets Scope
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

class SplashScreen:
    def __init__(self, root, duration=6000):
        self.root = root
        self.duration = duration
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 1)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.configure(bg="black")

        self.label = tk.Label(
            self.root,
            text="McCutcheonLab Technologies\nRTFED(PiCAM)",
            font=("Cascadia Code", 32, "bold"),
            bg="black",
            fg="violet"
        )
        self.label.pack(expand=True)

        self.faded_in = False
        self.fade_in(1000, self.start_camera_detection)

    def fade_in(self, time_ms, callback):
        alpha = 0.0
        increment = 1 / (time_ms // 50)
        def fade():
            nonlocal alpha
            if alpha < 1.0:
                alpha += increment
                self.root.attributes("-alpha", alpha)
                self.root.after(50, fade)
            else:
                self.faded_in = True
                callback()
        fade()

    def update_label(self, text):
        self.label.config(text=text)
        self.root.update_idletasks()
        self.root.update()

    def start_camera_detection(self):
        self.update_label("McCutcheonLab Technologies\nRTFED(PiCAM)\nDetecting USB Cameras...")
        self.root.update()

        # Detect cameras
        self.camera_indices = []
        for index in range(20):
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                self.camera_indices.append(str(index))
                cap.release()
            else:
                cap.release()

        self.fade_out(2000, self.close)

    def fade_out(self, time_ms, callback):
        alpha = 1.0
        decrement = 1 / (time_ms // 50)
        def fade():
            nonlocal alpha
            if alpha > 0.0:
                alpha -= decrement
                self.root.attributes("-alpha", alpha)
                self.root.after(50, fade)
            else:
                callback()
        fade()

    def close(self):
        self.root.destroy()

class FED3MonitorApp:
    def __init__(self, root, camera_indices):
        self.root = root
        self.root.title("RTFED(PiCAM)")
        self.root.geometry("1200x800")

        # Variables
        self.experimenter_name = tk.StringVar()
        self.experiment_name = tk.StringVar()
        self.json_path = tk.StringVar()
        self.spreadsheet_id = tk.StringVar()
        self.save_path = ""
        self.data_queue = queue.Queue()
        self.serial_ports = set(self.detect_serial_ports())
        self.threads = []
        self.port_widgets = {}
        self.port_queues = {}
        self.port_threads = {}
        self.identification_threads = {}
        self.identification_stop_events = {}
        self.log_queue = queue.Queue()
        self.recording_circle = None
        self.recording_label = None
        self.data_to_save = {}
        self.stop_event = threading.Event()
        self.logging_active = False
        self.data_saved = False
        self.gspread_client = None
        self.last_device_check_time = time.time()
        self.retry_attempts = 5
        self.retry_delay = 2

        # Maps to ensure stable association
        self.port_to_device_number = {}
        self.device_number_to_port = {}

        # Camera handling
        self.port_to_camera_index = {}
        self.camera_objects = {}
        self.recording_states = {}
        self.last_event_times = {}
        self.recording_locks = {}

        # Use camera_indices from splash detection
        self.camera_indices = camera_indices

        self.setup_gui()
        self.root.after(0, self.update_gui)
        self.root.after(100, self.show_instruction_popup)
        self.root.after(200, self.start_identification_threads)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def detect_serial_ports(self):
        ports = list(serial.tools.list_ports.comports())
        fed3_ports = []
        for port in ports:
            if port.vid == 0x239A and port.pid == 0x800B:
                fed3_ports.append(port.device)
        return fed3_ports

    def setup_gui(self):
        self.root.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.root.grid_rowconfigure((0,1,2,3,4,5,6), weight=1)

        label_font = ("Cascadia Code", 12, "bold")
        entry_font = ("Cascadia Code", 11)

        tk.Label(self.root, text="Your Name:", font=label_font).grid(column=0, row=0, sticky=tk.E, padx=5, pady=5)
        self.experimenter_entry = ttk.Entry(self.root, textvariable=self.experimenter_name, width=30, font=entry_font)
        self.experimenter_entry.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5)

        tk.Label(self.root, text="Experiment Name:", font=label_font).grid(column=2, row=0, sticky=tk.E, padx=5, pady=5)
        self.experiment_entry = ttk.Entry(self.root, textvariable=self.experiment_name, width=30, font=entry_font)
        self.experiment_entry.grid(column=3, row=0, sticky=tk.W, padx=5, pady=5)

        tk.Label(self.root, text="Google API JSON File:", font=label_font).grid(column=0, row=1, sticky=tk.E, padx=5, pady=5)
        self.json_entry = ttk.Entry(self.root, textvariable=self.json_path, width=50, font=entry_font)
        self.json_entry.grid(column=1, row=1, sticky=tk.W, padx=5, pady=5)
        self.browse_json_button = tk.Button(self.root, text="Browse", command=self.browse_json, font=("Cascadia Code", 10))
        self.browse_json_button.grid(column=2, row=1, padx=5, pady=5, sticky=tk.W)

        tk.Label(self.root, text="Google Spreadsheet ID:", font=label_font).grid(column=0, row=2, sticky=tk.E, padx=5, pady=5)
        self.spreadsheet_entry = ttk.Entry(self.root, textvariable=self.spreadsheet_id, width=50, font=entry_font)
        self.spreadsheet_entry.grid(column=1, row=2, sticky=tk.W, padx=5, pady=5)

        self.start_button = tk.Button(self.root, text="START", font=label_font, bg="green", fg="white", command=self.start_logging)
        self.start_button.grid(column=2, row=2, padx=10, pady=10, sticky=tk.W)
        self.stop_button = tk.Button(self.root, text="STOP(SAVE & QUIT)", font=label_font, bg="red", fg="white", command=self.stop_logging)
        self.stop_button.grid(column=3, row=2, padx=10, pady=10, sticky=tk.W)
        self.browse_button = tk.Button(self.root, text="Browse Data Folder", font=label_font, command=self.browse_folder, bg="gold", fg="blue")
        self.browse_button.grid(column=0, row=3, padx=10, pady=10, sticky=tk.W)

        indicator_frame = tk.Frame(self.root)
        indicator_frame.grid(column=1, row=3, columnspan=2, pady=10)
        self.canvas = tk.Canvas(indicator_frame, width=100, height=100)
        self.canvas.pack()
        self.recording_circle = self.canvas.create_oval(25, 25, 75, 75, fill="Orange")
        self.recording_label = self.canvas.create_text(50, 90, text="Standby", font=("Cascadia Code", 12), fill="black")

        ports_frame_container = tk.Frame(self.root)
        ports_frame_container.grid(column=0, row=4, columnspan=4, pady=20, sticky=(tk.N, tk.S, tk.E, tk.W))
        ports_canvas = tk.Canvas(ports_frame_container)
        ports_scrollbar = ttk.Scrollbar(ports_frame_container, orient="vertical", command=ports_canvas.yview)
        ports_canvas.configure(yscrollcommand=ports_scrollbar.set)
        ports_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ports_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.ports_frame = tk.Frame(ports_canvas)
        ports_canvas.create_window((0,0), window=self.ports_frame, anchor="nw")
        self.ports_frame.bind("<Configure>", lambda event: ports_canvas.configure(scrollregion=ports_canvas.bbox("all")))

        if not self.serial_ports:
            tk.Label(self.ports_frame, text="Connect your FED3 devices and restart the GUI!", font=("Cascadia Code", 14), fg="red").pack()
        else:
            for idx, port in enumerate(self.serial_ports):
                self.initialize_port_widgets(port, idx)

        log_frame = tk.Frame(self.root)
        log_frame.grid(column=0, row=5, columnspan=4, pady=10, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.log_text = tk.Text(log_frame, height=10, width=130, font=("Cascadia Code", 10))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.grid(column=0, row=6, columnspan=4, pady=10, sticky=(tk.S, tk.E, tk.W))
        tk.Label(bottom_frame, text="© 2024 McCutcheonLab | UiT | Norway", font=("Cascadia Code", 10), fg="royalblue").pack(pady=5)
        hyperlink_label = tk.Label(bottom_frame, text="Developed by Hamid Taghipourbibalan", font=("Cascadia Code", 10, "italic"), fg="blue", cursor="hand2")
        hyperlink_label.pack(pady=5)
        hyperlink_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.linkedin.com/in/hamid-taghipourbibalan-b7239088/"))

    def show_instruction_popup(self):
        messagebox.showinfo("Instructions", "First make a poke or trigger the pellet sensor on each FED3 to identify each device!")
        messagebox.showwarning("Caution", "1) If you need to restart a FED3 after pressing START, only do it when the internet connection is on, more importantly, ONYL RESTART AND RECONNECT DEVICES ONE AT A TIME\n2)You must use a powered USB hub for multiple FED3s and Cameras(more than 4 existing USB ports on RbPi 4B)\n3)DO NOT unplug a camera which is already paired with a FED3 device after pressing START\n4)In theory up to 20 cameras can be detected by this software")

    def browse_json(self):
        filename = filedialog.askopenfilename(title="Select JSON File", filetypes=[("JSON Files", "*.json")])
        if filename:
            self.json_path.set(filename)

    def browse_folder(self):
        self.save_path = filedialog.askdirectory(title="Select Folder to Save Data")
        if self.save_path:
            self.log_queue.put(f"Data folder selected: {self.save_path}")

    def initialize_port_widgets(self, port, idx=None):
        if port in self.port_widgets:
            return

        if idx is None:
            idx = len(self.port_widgets)
        port_name = os.path.basename(port)
        frame = ttk.LabelFrame(self.ports_frame, text=f"Port {port_name}")
        frame.grid(column=idx % 2, row=idx // 2, padx=10, pady=10, sticky=tk.W)
        status_label = ttk.Label(frame, text="Not Ready", font=("Cascadia Code", 10, "italic"), foreground="red")
        status_label.grid(column=0, row=0, sticky=tk.W)
        indicator_canvas = tk.Canvas(frame, width=20, height=20)
        indicator_canvas.grid(column=1, row=0, padx=5)
        indicator_circle = indicator_canvas.create_oval(5, 5, 15, 15, fill="gray")

        camera_label = ttk.Label(frame, text="Camera Index:", font=("Cascadia Code", 9))
        camera_label.grid(column=0, row=1, sticky=tk.W)
        camera_var = tk.StringVar(value='None')
        camera_combobox = ttk.Combobox(frame, textvariable=camera_var, values=['None'] + self.camera_indices, width=10, font=("Cascadia Code", 9))
        camera_combobox.grid(column=1, row=1, sticky=tk.W)

        test_cam_button = tk.Button(frame, text="Test Camera", font=("Cascadia Code", 9), command=lambda p=port: self.test_camera(p))
        test_cam_button.grid(column=2, row=1, padx=5)

        text_widget = tk.Text(frame, width=50, height=8, font=("Cascadia Code", 9))
        text_widget.grid(column=0, row=2, columnspan=3, sticky=(tk.N, tk.S, tk.E, tk.W))

        self.port_widgets[port] = {
            'status_label': status_label,
            'text_widget': text_widget,
            'camera_var': camera_var,
            'test_cam_button': test_cam_button,
            'indicator_canvas': indicator_canvas,
            'indicator_circle': indicator_circle,
            'camera_combobox': camera_combobox
        }
        self.port_queues[port] = queue.Queue()

        try:
            ser = serial.Serial(port, 115200, timeout=1)
            ser.close()
            status_label.config(text="Ready", foreground="green")
        except serial.SerialException as e:
            status_label.config(text="Not Ready", foreground="red")
            self.log_queue.put(f"Error with port {port}: {e}")

    def test_camera(self, port):
        camera_index_str = self.port_widgets[port]['camera_var'].get()
        if camera_index_str == 'None':
            messagebox.showinfo("Info", "Please select a camera index to test.")
            return
        camera_index = int(camera_index_str)
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            messagebox.showerror("Error", f"Cannot open camera with index {camera_index}")
            return

        cv2.namedWindow(f"Camera {camera_index}", cv2.WINDOW_NORMAL)
        cv2.resizeWindow(f"Camera {camera_index}", 640, 480)
        start_time = time.time()
        while time.time() - start_time < 5:
            ret, frame = cap.read()
            if ret:
                cv2.imshow(f"Camera {camera_index}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                messagebox.showerror("Error", f"Failed to read from camera {camera_index}")
                break
        cap.release()
        cv2.destroyWindow(f"Camera {camera_index}")

    def start_identification_threads(self):
        for port in self.serial_ports:
            # Only start identification if we don't already know the device_number
            if port not in self.port_to_device_number:
                self.start_identification_thread(port)

    def start_identification_thread(self, port):
        if port in self.identification_threads:
            return

        stop_event = threading.Event()
        self.identification_stop_events[port] = stop_event

        def identification_with_delay():
            time.sleep(1)
            self.identification_thread(port, stop_event)

        t = threading.Thread(target=identification_with_delay)
        t.daemon = True
        t.start()
        self.identification_threads[port] = t
        self.log_queue.put(f"Started identification thread for {port}.")

    def stop_identification_threads(self):
        for port, event in list(self.identification_stop_events.items()):
            event.set()
        for port, t in list(self.identification_threads.items()):
            t.join()
            self.log_queue.put(f"Stopped identification thread for {port}.")
            del self.identification_threads[port]
            del self.identification_stop_events[port]

    def identification_thread(self, port, stop_event):
        # If device_number is already known for this port or device_number known and associated with a different port,
        # no need to identify again.
        if port in self.port_to_device_number:
            return
        try:
            ser = serial.Serial(port, 115200, timeout=0.1)
            event_index_in_headers = column_headers.index("Event")
            event_index_in_data = event_index_in_headers - 1
            device_number_index_in_headers = column_headers.index("Device_Number")
            device_number_index_in_data = device_number_index_in_headers - 1

            device_number_found = None
            while not stop_event.is_set():
                try:
                    data = ser.readline().decode('utf-8', errors='replace').strip()
                    if data:
                        data_list = data.split(",")[1:]
                        if len(data_list) == len(column_headers)-1:
                            event_value = data_list[event_index_in_data].strip()
                            dn = data_list[device_number_index_in_data].strip()
                            if event_value == "Right":
                                self.port_queues[port].put("RIGHT_POKE")
                            if dn:
                                device_number_found = dn
                                break
                except serial.SerialException as e:
                    self.log_queue.put(f"Device on {port} disconnected during identification: {e}")
                    break
                except Exception as e:
                    self.log_queue.put(f"Error in identification thread for {port}: {e}")
        except serial.SerialException as e:
            if "PermissionError" not in str(e):
                self.log_queue.put(f"Could not open serial port {port} for identification: {e}")
        finally:
            try:
                ser.close()
            except:
                pass

        if device_number_found:
            self.log_queue.put(f"Identified device_number={device_number_found} on port={port}")
            self.register_device_number(port, device_number_found)

    def register_device_number(self, port, device_number):
        # If we already know this device_number from before (device reconnected)
        if device_number in self.device_number_to_port:
            old_port = self.device_number_to_port[device_number]
            if old_port != port:
                # Device reconnected to a different port
                self.log_queue.put(f"Device {device_number} reconnected on {port} (was on {old_port}).")
                # Transfer camera assignment and data queues if needed
                if old_port in self.port_to_camera_index:
                    self.port_to_camera_index[port] = self.port_to_camera_index[old_port]
                    del self.port_to_camera_index[old_port]

                if old_port in self.port_widgets:
                    # Move widget references if needed (keep for clarity)
                    # Actually we will just update statuses since port_widgets keyed by port still valid
                    pass

                # Remove old references
                if old_port in self.port_to_device_number:
                    del self.port_to_device_number[old_port]

                self.port_to_device_number[port] = device_number
                self.device_number_to_port[device_number] = port

                # If logging is active, start logging for this port if not already started
                if self.logging_active:
                    self.start_logging_for_port(port)

            else:
                # Same port (unlikely scenario), just ensure consistency
                self.port_to_device_number[port] = device_number
        else:
            # New device_number discovered first time
            self.port_to_device_number[port] = device_number
            self.device_number_to_port[device_number] = port
            # If logging already started, start logging for this new device immediately
            if self.logging_active:
                self.start_logging_for_port(port)

    def start_logging(self):
        self.stop_identification_threads()
        self.stop_event.clear()
        self.logging_active = True

        self.experimenter_name.set(self.experimenter_name.get().strip().lower())
        self.experiment_name.set(self.experiment_name.get().strip().lower())
        self.json_path.set(self.json_path.get().strip())
        self.spreadsheet_id.set(self.spreadsheet_id.get().strip())

        if not self.experimenter_name.get() or not self.experiment_name.get():
            messagebox.showerror("Error", "Please provide your name and experiment name.")
            return
        if not self.json_path.get() or not self.spreadsheet_id.get() or not self.save_path:
            messagebox.showerror("Error", "Please provide the JSON file, Spreadsheet ID, and data folder.")
            return

        experimenter_name = re.sub(r'[<>:"/\\|?*]', '_', self.experimenter_name.get())
        experiment_name = re.sub(r'[<>:"/\\|?*]', '_', self.experiment_name.get())
        self.experimenter_name.set(experimenter_name)
        self.experiment_name.set(experiment_name)

        try:
            creds = Credentials.from_service_account_file(self.json_path.get(), scopes=SCOPE)
            self.gspread_client = gspread.authorize(creds)
            self.log_queue.put("Connected to Google Sheets!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to Google Sheets: {e}")
            return

        self.disable_input_fields()
        self.canvas.itemconfig(self.recording_circle, fill="yellow")
        self.canvas.itemconfig(self.recording_label, text="Logging...", fill="black")

        self.experiment_start_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        experimenter_name = self.experimenter_name.get().lower().strip()
        experiment_name = self.experiment_name.get().lower().strip()
        experimenter_folder = os.path.join(self.save_path, experimenter_name)
        self.experiment_folder = os.path.join(experimenter_folder, f"{experiment_name}_{self.experiment_start_time}")
        os.makedirs(self.experiment_folder, exist_ok=True)
        self.log_queue.put(f"Experiment folder created at {self.experiment_folder}")

        for port, widget_data in self.port_widgets.items():
            widget_data['camera_combobox'].config(state='disabled')
            widget_data['test_cam_button'].config(state='disabled')
            camera_index_str = widget_data['camera_var'].get()
            camera_index = None if camera_index_str == 'None' else int(camera_index_str)
            self.port_to_camera_index[port] = camera_index

        # Open cameras if available
        for port, camera_index in self.port_to_camera_index.items():
            if camera_index is not None:
                cam = cv2.VideoCapture(camera_index)
                if cam.isOpened():
                    self.camera_objects[camera_index] = cam
                    self.log_queue.put(f"Camera {camera_index} associated with port {port}.")
                    current_status = self.port_widgets[port]['status_label'].cget("text")
                    if "Ready" in current_status and "CAM" not in current_status:
                        self.port_widgets[port]['status_label'].config(text="Ready (CAM Ready)", foreground="green")
                else:
                    self.log_queue.put(f"Camera {camera_index} failed to open for {port}.")
                    current_status = self.port_widgets[port]['status_label'].cget("text")
                    if "Ready" in current_status and "CAM" not in current_status:
                        self.port_widgets[port]['status_label'].config(text="Ready (CAM Not Connected)", foreground="orange")
                    cam.release()
            self.recording_states[port] = False
            self.last_event_times[port] = None
            self.recording_locks[port] = threading.Lock()

        # Start logging threads only for ports that have device_number known
        for port in list(self.serial_ports):
            if port in self.port_to_device_number:
                self.start_logging_for_port(port)
            else:
                self.log_queue.put(f"Device number not yet known for {port}, logging will start once identified.")

    def disable_input_fields(self):
        self.experimenter_entry.config(state='disabled')
        self.experiment_entry.config(state='disabled')
        self.json_entry.config(state='disabled')
        self.spreadsheet_entry.config(state='disabled')
        self.browse_json_button.config(state='disabled')
        self.browse_button.config(state='disabled')
        self.start_button.config(state='disabled')

    def enable_input_fields(self):
        self.experimenter_entry.config(state='normal')
        self.experiment_entry.config(state='normal')
        self.json_entry.config(state='normal')
        self.spreadsheet_entry.config(state='normal')
        self.browse_json_button.config(state='normal')
        self.browse_button.config(state='normal')
        self.start_button.config(state='normal')
        for port, widget_data in self.port_widgets.items():
            widget_data['camera_combobox'].config(state='normal')
            widget_data['test_cam_button'].config(state='normal')

    def start_logging_for_port(self, port):
        if port in self.port_threads:
            return

        device_number = self.port_to_device_number.get(port)
        if not device_number:
            self.log_queue.put(f"Cannot start logging for {port}, no device_number known yet.")
            return

        worksheet_name = f"Device_{device_number}"

        def attempt_connection(retries=self.retry_attempts, delay=self.retry_delay):
            for attempt in range(retries):
                try:
                    ser = serial.Serial(port, 115200, timeout=0.1)
                    self.data_to_save[port] = []
                    t = threading.Thread(
                        target=self.read_from_port,
                        args=(ser, worksheet_name, port)
                    )
                    t.daemon = True
                    t.start()
                    self.port_threads[port] = t

                    # Always set status to "Ready" now that connection succeeded
                    self.port_widgets[port]['status_label'].config(text="Ready", foreground="green")

                    # If camera is associated, update status accordingly
                    camera_index = self.port_to_camera_index.get(port)
                    if camera_index is not None:
                        cam = self.camera_objects.get(camera_index)
                        if cam and cam.isOpened():
                            self.port_widgets[port]['status_label'].config(text="Ready (CAM Ready)", foreground="green")
                        else:
                            current_status = self.port_widgets[port]['status_label'].cget("text")
                            if "Ready" in current_status and "CAM" not in current_status:
                                self.port_widgets[port]['status_label'].config(text="Ready (CAM Not Connected)", foreground="orange")

                    self.log_queue.put(f"Started logging from {port} with sheet {worksheet_name}.")
                    return
                except serial.SerialException as e:
                    self.log_queue.put(f"Attempt {attempt+1}: Error with port {port}: {e}")
                    time.sleep(delay)
            self.log_queue.put(f"Failed to connect to port {port} after {retries} attempts.")

        threading.Thread(target=attempt_connection).start()

    def stop_logging(self):
        self.stop_event.set()
        self.logging_active = False
        self.log_queue.put("Stopping logging...")

        self.hide_recording_indicator()
        self.enable_input_fields()

        threading.Thread(target=self._join_threads_and_save).start()

    def _join_threads_and_save(self):
        for port, t in list(self.port_threads.items()):
            t.join()
            self.log_queue.put(f"Logging thread for {port} has stopped.")
            del self.port_threads[port]

        self.save_all_data()
        self.data_saved = True

        for cam in self.camera_objects.values():
            cam.release()
        self.log_queue.put("Cameras released.")

        self.root.after(0, self._finalize_exit)

    def _finalize_exit(self):
        messagebox.showinfo("Data Saved", "All data has been saved locally.")
        self.root.destroy()

    def save_all_data(self):
        if not self.save_path:
            self.log_queue.put("Error: No save path specified.")
            return
        for port, data_rows in self.data_to_save.items():
            if data_rows:
                port_name = os.path.basename(port)
                safe_port_name = re.sub(r'[<>:"/\\|?*]', '_', port_name)
                device_number = self.port_to_device_number.get(port, "unknown")
                filename_user = os.path.join(self.experiment_folder, f"{safe_port_name}_device_{device_number}_{self.experiment_start_time}.csv")
                try:
                    with open(filename_user, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(column_headers)
                        writer.writerows(data_rows)
                    self.log_queue.put(f"Data saved for {port} in {filename_user}.")
                except Exception as e:
                    self.log_queue.put(f"Failed to save data for {port}: {e}")

    def update_gui(self):
        # Check port queues
        for port_identifier, q in list(self.port_queues.items()):
            try:
                while True:
                    message = q.get_nowait()
                    if message == "RIGHT_POKE":
                        self.trigger_indicator(port_identifier)
                    else:
                        if port_identifier in self.port_widgets:
                            self.port_widgets[port_identifier]['text_widget'].insert(tk.END, message + "\n")
                            self.port_widgets[port_identifier]['text_widget'].see(tk.END)
            except queue.Empty:
                pass

        # Check log messages
        try:
            while True:
                log_message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, f"{datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')}: {log_message}\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass

        current_time = time.time()
        if current_time - self.last_device_check_time >= 5:
            self.check_device_connections()
            self.last_device_check_time = current_time

        self.root.after(100, self.update_gui)

    def check_device_connections(self):
        current_ports = set(self.detect_serial_ports())
        # Check for disconnected devices
        for port in list(self.serial_ports):
            if port not in current_ports:
                # Device disconnected
                if port in self.port_widgets:
                    self.port_widgets[port]['status_label'].config(text="Not Ready", foreground="red")
                self.log_queue.put(f"Device on {port} disconnected.")

        # Check for reconnected or new devices
        for port in current_ports:
            if port not in self.serial_ports:
                # New device (never seen before)
                self.serial_ports.add(port)
                if port not in self.port_widgets:
                    idx = len(self.port_widgets)
                    self.initialize_port_widgets(port, idx)

            
                # Identification will run if we don't know the device_number.
                known_device = False
                # We do not know which device_number this is yet, so run identification if not logging
                # If logging active, we still need to identify to figure out device_number
                if self.logging_active:
                    # If logging is active, we can identify it again. It will return a known device_number if it matches one we had before.
                    self.start_identification_thread(port)
                else:
                    # Not logging, safe to identify
                    self.start_identification_thread(port)
            else:
                # Port already known
                status = self.port_widgets[port]['status_label'].cget("text")
                if "Not Ready" in status:
                    # Device reconnected
                    if self.logging_active:
                        # If device_number known for this device (if previously identified)
                        device_number = self.port_to_device_number.get(port)
                        if device_number:
                            # known device
                            self.start_logging_for_port(port)
                            self.port_widgets[port]['status_label'].config(text="Ready", foreground="green")
                            camera_index = self.port_to_camera_index.get(port)
                            if camera_index is not None:
                                cam = self.camera_objects.get(camera_index)
                                if cam and cam.isOpened():
                                    self.port_widgets[port]['status_label'].config(text="Ready (CAM Ready)", foreground="green")
                                else:
                                    current_status = self.port_widgets[port]['status_label'].cget("text")
                                    if "Ready" in current_status and "CAM" not in current_status:
                                        self.port_widgets[port]['status_label'].config(text="Ready (CAM Not Connected)", foreground="orange")
                        else:
                            # unknown device_number, logging active
                            # Need identification
                            self.port_widgets[port]['status_label'].config(text="Not Ready", foreground="red")
                            self.start_identification_thread(port)
                    else:
                        # Not logging
                        # If device_number known, just mark ready
                        device_number = self.port_to_device_number.get(port)
                        if device_number:
                            self.port_widgets[port]['status_label'].config(text="Ready", foreground="green")
                        else:
                            # unknown device_number and not logging -> try identify
                            self.start_identification_thread(port)

    def trigger_indicator(self, port_identifier):
        if port_identifier not in self.port_widgets:
            return
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

    def hide_recording_indicator(self):
        self.canvas.itemconfig(self.recording_circle, fill="red")
        self.canvas.itemconfig(self.recording_label, text="OFF", fill="red")

    def get_or_create_worksheet(self, spreadsheet, title):
        try:
            return spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=title, rows="1000", cols="20")
            sheet.append_row(column_headers)
            return sheet

    def on_closing(self):
        if not self.data_saved:
            self.stop_identification_threads()
            self.stop_event.set()
            self.logging_active = False

            for t in list(self.identification_threads.values()):
                t.join()

            for t in list(self.port_threads.values()):
                t.join()

            self.save_all_data()
            self.data_saved = True

        self.root.destroy()

    def read_from_port(self, ser, worksheet_name, port_identifier):
        device_number = self.port_to_device_number.get(port_identifier, 'unknown')
        try:
            spreadsheet = self.gspread_client.open_by_key(self.spreadsheet_id.get())
            sheet = self.get_or_create_worksheet(spreadsheet, worksheet_name)
            cached_data = []
            send_interval = 5
            last_send_time = time.time()
            jam_event_occurred = False

            event_index_in_headers = column_headers.index("Event")
            event_index_in_data = event_index_in_headers - 1
            device_number_index_in_headers = column_headers.index("Device_Number")

            while not self.stop_event.is_set():
                try:
                    data = ser.readline().decode('utf-8', errors='replace').strip()
                except serial.SerialException as e:
                    self.log_queue.put(f"Device on {port_identifier} disconnected: {e}")
                    if port_identifier in self.port_widgets:
                        self.port_widgets[port_identifier]['status_label'].config(text="Not Ready", foreground="red")
                    break

                if data:
                    data_list = data.split(",")[1:]
                    timestamp = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S.%f")[:-3]
                    if len(data_list) == len(column_headers)-1:
                        event_value = data_list[event_index_in_data].strip()
                        row_data = [timestamp] + data_list
                        cached_data.append(row_data)
                        self.port_queues[port_identifier].put(f"Data logged: {data_list}")
                        self.data_to_save[port_identifier].append(row_data)

                        if event_value == "JAM":
                            jam_event_occurred = True

                        # Trigger camera recording on "Pellet" event
                        if event_value == "Pellet":
                            with self.recording_locks[port_identifier]:
                                self.last_event_times[port_identifier] = datetime.datetime.now()
                                if not self.recording_states[port_identifier]:
                                    self.recording_states[port_identifier] = True
                                    threading.Thread(target=self.record_video, args=(port_identifier,)).start()
                    else:
                        self.log_queue.put(f"Warning: Data length mismatch on {port_identifier}")

                current_time = time.time()
                if current_time - last_send_time >= send_interval:
                    if cached_data:
                        try:
                            sheet.append_rows(cached_data)
                            self.log_queue.put(f"Appended {len(cached_data)} rows from {port_identifier} to Google Sheets.")
                            cached_data.clear()
                        except Exception as e:
                            self.log_queue.put(f"Failed to send data to Google Sheets for {port_identifier}: {e}")
                    if jam_event_occurred:
                        # Log a JAM event separately
                        try:
                            jam_row = [''] * len(column_headers)
                            jam_row[0] = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S.%f")[:-3]
                            jam_row[event_index_in_headers] = "JAM"
                            jam_row[device_number_index_in_headers] = device_number
                            sheet.append_row(jam_row)
                            self.log_queue.put(f"Additional JAM event logged for {port_identifier}.")
                            jam_event_occurred = False
                        except Exception as e:
                            self.log_queue.put(f"Failed to send JAM event to Google Sheets for {port_identifier}: {e}")

                    last_send_time = current_time
                time.sleep(0.1)
        except Exception as e:
            self.log_queue.put(f"Error reading from {ser.port}: {e}")
        finally:
            try:
                ser.close()
            except:
                pass
            self.log_queue.put(f"Closed serial port {ser.port}")
            # Remove the port from port_threads when thread finishes to allow re-logging after reconnect
            if port_identifier in self.port_threads:
                del self.port_threads[port_identifier]
            self.log_queue.put(f"Logging ended for {port_identifier}")

    def record_video(self, port_identifier):
        camera_index = self.port_to_camera_index.get(port_identifier)
        device_number = self.port_to_device_number.get(port_identifier, 'unknown')

        if camera_index is None:
            self.log_queue.put(f"No camera associated with port {port_identifier}")
            return

        cam = self.camera_objects.get(camera_index)
        if cam is None:
            self.log_queue.put(f"Camera {camera_index} not available for {port_identifier}")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        port_name = os.path.basename(port_identifier)
        safe_port_name = re.sub(r'[<>:"/\\|?*]', '_', port_name)

        path = os.path.join(self.experiment_folder, f"Device_{device_number}")
        os.makedirs(path, exist_ok=True)
        filename = os.path.join(path, f"{safe_port_name}_device_{device_number}_camera_{timestamp}.avi")

        frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if frame_width == 0 or frame_height == 0:
            self.log_queue.put(f"Camera {camera_index} is not returning frames.")
            with self.recording_locks[port_identifier]:
                self.recording_states[port_identifier] = False
                self.last_event_times[port_identifier] = None
            return
        out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'XVID'), 20.0, (frame_width, frame_height))

        try:
            while True:
                with self.recording_locks[port_identifier]:
                    last_event_time = self.last_event_times[port_identifier]
                if last_event_time is None:
                    break
                time_since_last_event = (datetime.datetime.now() - last_event_time).total_seconds()
                if time_since_last_event > 30:
                    break
                ret, frame = cam.read()
                if ret:
                    out.write(frame)
                else:
                    self.log_queue.put(f"Failed to read frame from camera {camera_index}")
                    break
                time.sleep(0.05)
        finally:
            out.release()
            with self.recording_locks[port_identifier]:
                self.recording_states[port_identifier] = False
                self.last_event_times[port_identifier] = None
            self.log_queue.put(f"Video saved as {filename}")

def main():
    # Splash screen
    splash_root = tk.Tk()
    splash = SplashScreen(splash_root, duration=7000)
    splash_root.mainloop()

    camera_indices = splash.camera_indices

    root = tk.Tk()
    app = FED3MonitorApp(root, camera_indices)
    root.mainloop()

if __name__ == "__main__":
    main()

