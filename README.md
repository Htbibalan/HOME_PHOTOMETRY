![Banner Image](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Banner.png)

# Home_Photometry_FED(HPFED)
* Here I am developing a home-cage photometry recording setup to incorporate [FED3](https://github.com/KravitzLabDevices/FED3/wiki) units with TDT [RZ10](https://www.tdt.com/docs/hardware/rz10-lux-integrated-processor/) photometry system.

* The process of setting up HPFED includes several steps including making adjustments to FED3 devices and updating FED3 library to enable it communicate via serial monitor connection, which was released as a separate update named [RTFED](https://github.com/mccutcheonlab/FED_RT). So the initial idea comes from RTFED, however unlike RTFED which is a good solution for longitudinal studies of food intake , in HPFED data is not transmitted to a Google Spreadsheet rather is directly relayed to the TDT system in form of TTL signals.
* The repository will include several stages of development of HPFED, from early python codes or scripts to flash Arduino boards to more advanced strategies using a [Raspberry Pi board](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)



## Arduino approach
![Arduino](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Slide1.PNG)

## RbPi Approach
![RBPI](https://github.com/Htbibalan/HOME_PHOTOMETRY/blob/main/source/Slide2.PNG)

