![Banner Image](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Banner.png)

# RTFED_Pi
* RTFED_Pi is the other version of RTFED(classic on Windows) which is an open-source versatile tool for home-cage monitoring of behaviour and fiber photometry recording in mice
* RTFED_Pi is developed as a home-cage setup to incorporate [FED3](https://github.com/KravitzLabDevices/FED3/wiki) units with TDT [RZ10](https://www.tdt.com/docs/hardware/rz10-lux-integrated-processor/) photometry system or capture event-triggered videos of behaviour or to monitor food intake and other relevant behaviours remotely and online.

## RbPi Approach
![RBPI](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Slide2.PNG)


![RTFED_Pi](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Clipped_image_20241221_120025.png)
![RTFED_TOWER](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Clipped_image_20241221_120929.png)

# RTFED(PiOS)
RTFED(PiOS) can be used to remotely monitor the feeding behaviour and other interactions made by mice on FED3, the data is automatically transferred to a Google spreadsheet where you can view it or define alarm notification using the Google Apps Scripts. Using the RTFED you can also change the Mode of your FED3s without the hassle of poking one by one!
![RTFED_PiOS](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/RTFED_Pi.png)

# RTFED(PiCAM)
RTFED(PiCAM) is an additional feature to the basic RTFED where you can enhance your behavioural studies by having event-triggered video recording. Primarily the RTFED(PiCAM) can record videos of mice using common USB cameras after taking Pellets, making Left or Right pokes or a combination of All of these events. Videos are limited to 30 sec length to capture only relevant behaviours while saving storage space, in this configuration, e.g. after taking a pellet, the GUI records the behaviour for 30 sec, if another pellet is taken within this 30 sec, it keeps recording for an extra 30 sec until no more pellet is taken.
![RTFED_PiCAM](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/RTFED(PiCAM).png)

# RTFED(PiTTL)
The TTL station of RTFED logs behavioural events made on FED3 devices and transmit them to the TDT RZ10 processors as TTL pulses. This features enables you to study event-locked signals in your experiments.

![RTFED_PiTTL](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/RTFED(PiTTL).png)
