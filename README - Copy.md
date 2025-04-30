![Banner Image](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Banner.png)

# Home_Photometry_FED(HPFED)
* Here I am developing a home-cage photometry recording setup to incorporate [FED3](https://github.com/KravitzLabDevices/FED3/wiki) units with TDT [RZ10](https://www.tdt.com/docs/hardware/rz10-lux-integrated-processor/) photometry system.

* The process of setting up HPFED includes several steps including making adjustments to FED3 devices and updating FED3 library to enable it communicate via serial monitor connection, which was released as a separate update named [RTFED](https://github.com/mccutcheonlab/FED_RT). So the initial idea comes from RTFED, however unlike RTFED which is a good solution for longitudinal studies of food intake , in HPFED data is not transmitted to a Google Spreadsheet rather is directly relayed to the TDT system in form of TTL signals.
* The repository will include several stages of development of HPFED, from early python codes or scripts to flash Arduino boards to more advanced strategies using a [Raspberry Pi board](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)



## Arduino approach
![Arduino](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Slide1.PNG)

## RbPi Approach
![RBPI](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Slide2.PNG)






# RTFED (Raspberry Pi OS) - Open Source Behavioral Monitoring System

## Overview

RTFED is an open-source behavioral monitoring system designed for researchers to track and analyze animal behavior in real-time using Raspberry Pi 4B. The system integrates multiple FED3 devices, cameras, and TTL signal synchronization for photometry systems, providing a comprehensive solution for behavioral experiments. The system is modular, with three separate GUIs for different functionalities:

1. **FED3 Data Logging**: Logs data from FED3 devices, sends it to Google Sheets, and notifies users via JAM notifications or email.
2. **FED3 with Camera Integration**: Logs data from FED3 devices and records video of mice during pellet collection.
3. **TTL Signal Synchronization**: Sends TTL signals with high temporal accuracy to synchronize behavioral data with brain signals recorded during photometry.

## Features

- **Real-Time Data Logging**: Logs data from FED3 devices in real-time and stores it locally or sends it to Google Sheets.
- **Google Sheets Integration**: Automatically sends data to Google Sheets for remote monitoring and analysis.
- **JAM Notifications**: Sends JAM notifications to Google Sheets when a device fails or when a certain number of pellets are taken.
- **Email Notifications**: Sends email notifications when specific conditions are met (e.g., pellet count threshold).
- **Video Recording**: Records video of mice during pellet collection for behavioral analysis.
- **TTL Signal Synchronization**: Sends TTL signals with high temporal accuracy (0.003 sec latency) to synchronize behavioral data with brain signals.
- **Open Source**: The system is open-source, allowing researchers to modify and extend its functionality.

## Requirements

### Hardware
- **Raspberry Pi 4B**: The main processing unit for the system.
- **FED3 Devices**: Devices used to monitor animal behavior.
- **USB Cameras**: Cameras for recording video of mice during pellet collection.
- **TDT RZ10 Photometry System**: For synchronizing behavioral data with brain signals.
- **Powered USB Hub**: Recommended for connecting multiple FED3 devices and cameras.
- **GPIO Cables**: For connecting FED3 devices to the Raspberry Pi.

### Software
- **Pre-Configured Raspberry Pi Image**: A pre-configured image file that includes all necessary software and configurations.
- **Google API Credentials**: Required for Google Sheets integration.
- **Gspread Library**: Python library for interacting with Google Sheets.
- **OpenCV**: Library for video recording and processing.
- **RPi.GPIO**: Library for controlling GPIO pins on the Raspberry Pi.
- **Tkinter**: Python library for creating the GUI.

## Installation

1. **Flash the SD Card**:
   - Download the pre-configured Raspberry Pi image file provided.
   - Use a tool like [Raspberry Pi Imager](https://www.raspberrypi.org/software/) or [Balena Etcher](https://www.balena.io/etcher/) to flash the image onto an SD card.
   - Insert the SD card into your Raspberry Pi 4B.

2. **Power On the Raspberry Pi**:
   - Connect your Raspberry Pi to a monitor, keyboard, and mouse.
   - Power on the Raspberry Pi.

3. **Connect Hardware**:
   - Connect your FED3 devices, USB cameras, and TDT RZ10 photometry system to the Raspberry Pi using a powered USB hub.
   - Ensure all GPIO cables are properly connected.

4. **Set Up Google API Credentials**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project and enable the Google Sheets API.
   - Create credentials and download the JSON file.
   - Place the JSON file in the project directory and update the `json_path` variable in the code.

## Usage

### FED3 Data Logging
1. **Launch the GUI**:
   - Open the terminal on your Raspberry Pi.
   - Navigate to the directory containing the pre-configured image.
   - Run the following command to start the FED3 Data Logging GUI:
     ```bash
     ./fed3_monitor_gui
     ```
2. **Enter Experiment Details**: Provide your name, experiment name, Google API JSON file, and Google Spreadsheet ID.
3. **Start Logging**: Click the "START" button to begin logging data. Data will be saved locally and sent to Google Sheets.

### FED3 with Camera Integration
1. **Launch the GUI**:
   - Open the terminal on your Raspberry Pi.
   - Navigate to the directory containing the pre-configured image.
   - Run the following command to start the FED3 with Camera Integration GUI:
     ```bash
     ./fed3_camera_gui
     ```
2. **Enter Experiment Details**: Provide your name, experiment name, Google API JSON file, and Google Spreadsheet ID.
3. **Start Logging**: Click the "START" button to begin logging data and recording video.

### TTL Signal Synchronization
1. **Launch the GUI**:
   - Open the terminal on your Raspberry Pi.
   - Navigate to the directory containing the pre-configured image.
   - Run the following command to start the TTL Signal Synchronization GUI:
     ```bash
     ./ttl_sync_gui
     ```
2. **Enter Experiment Details**: Provide your name, experiment name, and other required details.
3. **Start Synchronization**: Click the "START" button to begin sending TTL signals.

## Troubleshooting

- **Device Not Detected**: Ensure that the FED3 device is properly connected to the Raspberry Pi and that the USB port is functioning.
- **Google Sheets Integration Failure**: Verify that the Google API credentials are correct and that the Google Sheets API is enabled.
- **Video Recording Issues**: Ensure that the USB camera is properly connected and recognized by the Raspberry Pi.

## Contributing

We welcome contributions to the RTFED project! If you have any suggestions, bug reports, or feature requests, please open an issue on the GitHub repository. If you would like to contribute code, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **McCutcheon Lab**: For their support and guidance in developing this system.
- **UiT The Arctic University of Norway**: For providing the resources and environment for this project.
- **Hamid Taghipourbibalan**: For developing the system and making it open-source.

## Contact

For any questions or inquiries, please contact [Hamid Taghipourbibalan](https://www.linkedin.com/in/hamid-taghipourbibalan-b7239088/).

---

Thank you for using RTFED! We hope this system helps you in your research and behavioral studies.








# RTFED_Pi_WIN

**Real-Time FED3 Monitoring and Control System for Raspberry Pi and Windows**

Welcome to **RTFED_Pi_WIN**—an open-source project for continuous monitoring of rodent feeding behavior using **FED3** devices. Our system provides:
1. **Real-time data logging** and **remote monitoring** of pellet deliveries, poke events, and device health.
2. **Video recording** integration (in the Raspberry Pi version) for behavioral observation.
3. **TTL (Transistor–Transistor Logic) output** for sub-second synchronization with neural recording devices (e.g., photometry systems).

This README provides a step-by-step guide to installing, configuring, and using the software. For more in-depth technical details and background, please see the accompanying [research paper](#).

---

## Table of Contents
1. [Features](#features)
2. [Hardware Requirements](#hardware-requirements)
3. [Software Requirements](#software-requirements)
4. [Setting Up Google Sheets and Credentials](#setting-up-google-sheets-and-credentials)
5. [Installation](#installation)
6. [Usage](#usage)
    - [A. Basic Data Logging on Raspberry Pi](#a-basic-data-logging-on-raspberry-pi)
    - [B. Video Integration (PiCAM GUI)](#b-video-integration-picam-gui)
    - [C. TTL Output for Photometry Synchronization](#c-ttl-output-for-photometry-synchronization)
    - [D. Windows Version](#d-windows-version)
7. [Data Storage and File Format](#data-storage-and-file-format)
8. [Troubleshooting](#troubleshooting)
9. [License](#license)
10. [Citation](#citation)
11. [Contributors](#contributors)

---

## 1. Features

- **Multi-Device Logging**: Monitor multiple FED3 units simultaneously.
- **Automatic Data Upload**: Push feeding events to Google Sheets for remote viewing and collaboration.
- **Event-Triggered Video** (Pi version): Optionally record camera footage of mice retrieving pellets.
- **TTL Output** (Pi version): Send fast (<0.005 s latency) TTL pulses to external hardware (e.g., TDT or other photometry systems).
- **User-Friendly GUI**: Configure experiment names, data folder, spreadsheets, and cameras with minimal coding required.

---

## 2. Hardware Requirements

### For **RTFED_Pi**:
- **Raspberry Pi 4B** (4 GB RAM or above recommended).
- **MicroSD card** (16 GB or larger) with Raspberry Pi OS (Debian-based).
- **FED3 devices** connected via USB. A **powered USB hub** is recommended if using multiple FED3s or USB cameras.
- (Optional) **USB cameras** (e.g., Logitech series) for video recording.
- (Optional) **TDT RZ10 or similar** photometry interface if you require TTL syncing.

### For **RTFED_Win**:
- **Windows 10 or 11 PC** (laptop or desktop).
- **FED3 devices** connected via USB.
- (Optional) **USB-to-TTL converter** for TTL pulse output (if your workflow requires external triggering).
- (Optional) **USB cameras** for video integration (requires OpenCV / Python environment).

---

## 3. Software Requirements

- **Python 3.7+** (recommended 3.9+).
- **pip** (Python package installer).
- **Git** (optional but recommended to clone this repository).
- **Tkinter** (often included with Python).
- **pySerial**, **gspread**, **oauth2client** (or `google-auth-oauthlib`), **opencv-python** (for PiCAM version).
- **Raspberry Pi OS** or **Windows 10/11**.

---

## 4. Setting Up Google Sheets and Credentials

1. **Google Cloud Project**: Create a project in the [Google Cloud Console](https://console.cloud.google.com).
2. **Enable Google Sheets API**: Under “APIs & Services,” enable the Sheets API.
3. **Create Service Account Credentials**:
   - Go to “Credentials” and create a service account key in JSON format.
   - Download the `.json` file and place it in a secure location on the Pi/PC.
4. **Google Spreadsheet**:
   - Create or open an existing Google Spreadsheet.
   - Share it with the service account email (found in the JSON file) so the system can append rows remotely.
5. **Spreadsheet ID**: Copy the ID from your Google Sheets URL (it looks like a long string of letters and numbers between `/d/` and `/edit`).

For more detailed instructions, refer to the example [FED_RT repository](https://github.com/mccutcheonlab/FED_RT) on GitHub, which has similar steps for credential setup.

---

## 5. Installation

1. **Clone or Download** this repository:
   ```bash
   git clone https://github.com/YourUserName/RTFED_Pi_WIN.git
