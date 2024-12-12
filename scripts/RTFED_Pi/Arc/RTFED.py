#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import sys
import serial
import threading
import datetime
import gspread
from google.oauth2.service_account import Credentials
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import queue
import re
import csv

# Column headers for the Google Spreadsheet
column_headers = [
    "MM/DD/YYYY hh:mm:ss.SSS", "Temp", "Humidity", "Library_Version", "Session_type",
    "Device_Number", "Battery_Voltage", "Motor_Turns", "FR", "Event", "Active_Poke",
    "Left_Poke_Count", "Right_Poke_Count", "Pellet_Count", "Block_Pellet_Count",
    "Retrieval_Time", "InterPelletInterval", "Poke_Time"
]

# Google Sheets scope and client initialization
SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

# Global stop event for threads
stop_event = threading.Event()

# Splash screen class
class SplashScreen:
    def __init__(self, root, duration=3000):
        self.root = root
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 1)

        # Resize splash screen for 7-inch screen (800x480 resolution)
        width, height = 800, 600
        x = (800 - width) // 2
        y = (480 - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(bg="black")

        self.label = tk.Label(self.root, text="McCutcheonlab Technologies", font=("Cascadia Code", 28, "bold"), bg="black", fg="violet")
        self.label.pack(expand=True)
        self.fade_in_out(duration)

    def fade_in_out(self, duration):
        self.fade_in(1000, lambda: self.fade_out(2000, self.close))

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
                self.root.after(50, fade)
            else:
                callback()
        fade()

    def close(self):
        self.root.destroy()

# Main GUI Class
class FED3MonitorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Realtime FED monitor")
        self.root.geometry("800x480")  # Set for 7-inch touchscreen resolution

        # Variables for the GUI
        self.experimenter_name = tk.StringVar()
        self.experiment_name = tk.StringVar()
        self.json_path = tk.StringVar()
        self.spreadsheet_id = tk.StringVar()
        self.save_path = ""
        self.data_queue = queue.Queue()
        self.threads = []
        self.device_mappings = []
        self.port_widgets = {}
        self.recording_circle = None
        self.recording_label = None
        self.data_to_save = {}

        self.gspread_client = None

        self.setup_gui()
        self.check_connected_devices()  # Check for connected devices on startup

    def setup_gui(self):
        # Resize GUI elements to fit 7-inch screen
        self.root.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Experimenter name input
        tk.Label(self.root, text="Your Name:", font=("Cascadia Code", 8, "bold")).grid(column=0, row=0, sticky=tk.E, padx=2, pady=2)
        self.experimenter_entry = ttk.Entry(self.root, textvariable=self.experimenter_name, width=12)
        self.experimenter_entry.grid(column=1, row=0, sticky=tk.W, padx=2, pady=5)

        # Experiment name input
        tk.Label(self.root, text="Experiment Name:", font=("Cascadia Code", 8, "bold")).grid(column=2, row=0, sticky=tk.E, padx=2, pady=2)
        self.experiment_entry = ttk.Entry(self.root, textvariable=self.experiment_name, width=15)
        self.experiment_entry.grid(column=3, row=0, sticky=tk.E, padx=2, pady=2)

        # JSON file path
        tk.Label(self.root, text="Google API JSON File:", font=("Cascadia Code", 8, "bold")).grid(column=0, row=1, sticky=tk.E, padx=2, pady=2)
        self.json_entry = ttk.Entry(self.root, textvariable=self.json_path, width=25)
        self.json_entry.grid(column=1, row=1, columnspan=2, sticky=tk.W, padx=2, pady=2)
        self.browse_json_button = tk.Button(self.root, text="Browse", command=self.browse_json)
        self.browse_json_button.grid(column=2, row=1, padx=2, pady=2)

        # Google Spreadsheet ID
        tk.Label(self.root, text="Google Spreadsheet ID:", font=("Cascadia Code", 8, "bold")).grid(column=0, row=2, sticky=tk.E, padx=2, pady=2)
        self.spreadsheet_entry = ttk.Entry(self.root, textvariable=self.spreadsheet_id, width=25)
        self.spreadsheet_entry.grid(column=1, row=2, columnspan=2, sticky=tk.W, padx=2, pady=2)

        # Start button
        self.start_button = tk.Button(self.root, text="START", font=("Cascadia Code", 10, "bold"), bg="green", fg="white", command=self.start_logging)
        self.start_button.grid(column=0, row=3, padx=5, pady=5, sticky=tk.W)

        # Stop button
        self.stop_button = tk.Button(self.root, text="STOP(SAVE & QUIT)", font=("Cascadia Code", 10, "bold"), bg="red", fg="white", command=self.stop_logging)
        self.stop_button.grid(column=1, row=3, padx=5, pady=5, sticky=tk.W)

        # Browse button for selecting data folder path
        self.browse_button = tk.Button(self.root, text="Browse Data Folder", font=("Cascadia Code", 10, "bold"), command=self.browse_folder, bg="gold", fg="blue")
        self.browse_button.grid(column=2, row=3, padx=5, pady=5, sticky=tk.W)

        # Canvas for Recording Indicator (reduced size)
        self.canvas = tk.Canvas(self.root, width=100, height=100)
        self.canvas.grid(column=2, row=4, pady=5, sticky=tk.N)

        # Port display configuration
        self.setup_ports()
         # Add copyright message at the bottom
        self.copyright_label = tk.Label(
            self.root,
            text="© 2024 McCutcheonlab | UiT | Norway",
            font=("Cascadia Code", 8),
            fg="black"
        )
        # Position at the bottom of the window, spanning all columns
        self.copyright_label.grid(column=0, row=10, columnspan=4, sticky="s", pady=5)

    def browse_json(self):
        self.json_path.set(filedialog.askopenfilename(title="Select JSON File"))

    def browse_folder(self):
        self.save_path = filedialog.askdirectory(title="Select Folder to Save Data")

    def setup_ports(self):
        # Arrange port boxes in two rows for optimal screen fit
        port_names = ['Port 1', 'Port 2', 'Port 3', 'Port 4']
        for idx, port_name in enumerate(port_names):
            frame = ttk.LabelFrame(self.root, text=port_name)
            row_position = 4 + (idx // 2)
            column_position = idx % 2
            frame.grid(column=column_position, row=row_position, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
            status_label = ttk.Label(frame, text="Not Ready", font=("Cascadia Code", 8, "italic"), foreground="red")
            status_label.grid(column=0, row=0, sticky=tk.W)
            text_widget = tk.Text(frame, width=33, height=5)  # Adjusted width and height for better fit
            text_widget.grid(column=0, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))
            self.port_widgets[port_name] = {'frame': frame, 'status_label': status_label, 'text_widget': text_widget}

    def check_connected_devices(self):
        self.device_mappings = self.get_device_mappings_by_usb_port()
        for mapping in self.device_mappings:
            port_identifier = mapping['port_identifier']
            self.port_widgets[port_identifier]['status_label'].config(text="Ready", foreground="green")

    def start_logging(self):
        # **Added check to ensure a data folder is selected**
        if not self.save_path:
            messagebox.showerror("Error", "Please select a folder to save data before starting.")
            return

        # Disable entry fields and normalize inputs
        self.experimenter_entry.config(state='disabled')
        self.experiment_entry.config(state='disabled')
        self.json_entry.config(state='disabled')
        self.spreadsheet_entry.config(state='disabled')
        
        self.experimenter_name.set(self.experimenter_name.get().strip().lower())
        self.experiment_name.set(self.experiment_name.get().strip().lower())
        self.json_path.set(self.json_path.get().strip())
        self.spreadsheet_id.set(self.spreadsheet_id.get().strip())
        
        try:
            creds = Credentials.from_service_account_file(self.json_path.get(), scopes=SCOPE)
            self.gspread_client = gspread.authorize(creds)
            print(f"Connected to Google Spreadsheet: {self.spreadsheet_id.get()}")
        except Exception as e:
            messagebox.showerror("Error", f"Error setting up Google Sheets API: {e}")
            return

        self.show_recording_indicator()
        self.start_data_collection()

    def show_recording_indicator(self):
        if self.recording_circle is None:
            self.recording_circle = self.canvas.create_oval(25, 25, 75, 75, fill="red")
        if self.recording_label is None:
            self.recording_label = self.canvas.create_text(50,90 , text="ON AIR!", font=("Cascadia Code", 12), fill="red")

    def hide_recording_indicator(self):
        if self.recording_circle is not None:
            self.canvas.delete(self.recording_circle)
            self.recording_circle = None
        if self.recording_label is not None:
            self.canvas.delete(self.recording_label)
            self.recording_label = None

    def start_data_collection(self):
        for mapping in self.device_mappings:
            serial_port = mapping['serial_port']
            port_identifier = mapping['port_identifier']
            q = self.port_widgets[port_identifier]['text_widget']
            self.data_to_save[port_identifier] = []
            t = threading.Thread(target=self.read_from_port, args=(serial_port, f"Port_{port_identifier}", q, port_identifier))
            t.daemon = True
            t.start()
            self.threads.append(t)

    def get_device_mappings_by_usb_port(self):
        device_mappings = []
        usb_port_mapping = {'usb-0:1.1': 'Port 1', 'usb-0:1.2': 'Port 2', 'usb-0:1.3': 'Port 3', 'usb-0:1.4': 'Port 4'}
        for symlink in os.listdir('/dev/serial/by-path/'):
            symlink_path = os.path.join('/dev/serial/by-path/', symlink)
            serial_port = os.path.realpath(symlink_path)
            if 'ttyACM' in serial_port or 'ttyUSB' in serial_port:
                usb_port_path = self.get_usb_port_path_from_symlink(symlink)
                port_identifier = usb_port_mapping.get(usb_port_path)
                if port_identifier:
                    device_mappings.append({'serial_port': serial_port, 'port_identifier': port_identifier})
                    self.port_widgets[port_identifier]['status_label'].config(text="Ready", foreground="green")
        return device_mappings

    def get_usb_port_path_from_symlink(self, symlink):
        match = re.search(r'usb-\d+:\d+(\.\d+)*', symlink)
        return match.group() if match else None

    def read_from_port(self, serial_port, worksheet_name, text_widget, port_identifier):
        try:
            ser = serial.Serial(serial_port, 115200, timeout=1)
            spreadsheet = self.gspread_client.open_by_key(self.spreadsheet_id.get())
            sheet = self.get_or_create_worksheet(spreadsheet, worksheet_name)

            while not stop_event.is_set():
                data = ser.readline().decode('utf-8').strip()
                data_list = data.split(",")
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                data_list = data_list[1:]

                if len(data_list) == len(column_headers) - 1:
                    sheet.append_row([timestamp] + data_list)
                    text_widget.insert(tk.END, f"Data logged: {data_list}\n")
                    text_widget.see(tk.END)
                    self.data_to_save[port_identifier].append([timestamp] + data_list)

        except Exception as e:
            messagebox.showerror("Error", f"Error connecting to port {serial_port}: {e}")

    def get_or_create_worksheet(self, spreadsheet, title):
        try:
            return spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=title, rows="1000", cols="20")
            sheet.append_row(column_headers)
            return sheet

    def stop_logging(self):
        stop_event.set()
        for t in self.threads:
            t.join()

        self.hide_recording_indicator()
        self.save_all_data()
        self.root.quit()
        self.root.destroy()

    def save_all_data(self):
        current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        experimenter_name = self.experimenter_name.get().lower().strip()
        experiment_name = self.experiment_name.get().lower().strip()

        experimenter_folder = os.path.join(self.save_path, experimenter_name)
        experiment_folder = os.path.join(experimenter_folder, f"{experiment_name}_{current_time}")
        os.makedirs(experiment_folder, exist_ok=True)

        for port_identifier, data_rows in self.data_to_save.items():
            filename_user = f"{experiment_folder}/{port_identifier}_{current_time}.csv"
            with open(filename_user, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(column_headers)
                writer.writerows(data_rows)

# Main execution
if __name__ == "__main__":
    splash_root = tk.Tk()
    splash_screen = SplashScreen(splash_root)
    splash_root.after(3000, splash_screen.close)
    splash_root.mainloop()

    root = tk.Tk()
    app = FED3MonitorApp(root)
    root.mainloop()

