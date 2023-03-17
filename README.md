# SlicerRediMinds

SlicerRediMinds is a custom extension developed by RediMinds for their web app https://dev.groundtruthfactory.com This extension enables the user to load original CT scans and segmented files into Slicer using a URL, and then use the Segment Editor module to label or polish the segments of an organ. The RediMinds module, installed from the marketplace, can be used to send the segmented files to the RediMinds backend for further processing.

## Prerequisite

1. Should have 3D Slicer installed on your system. If it's not installed, you can download and install from here: https://www.slicer.org/
2. Should have installed `RediMinds` extension. If You have not installed, You can go to `Extensions Manager`, then Click `Install Extensions` then search `RediMinds` and then install.

## Usage

To use SlicerRediMinds, follow these steps:

1. Click the button `View In Slicer` on https://dev.groundtruthfactory.com to open Slicer and load the original CT scan and segmented file using the URL.
2. Use the `Segment Editor` module to label or polish the segments of an organ.
3. Switch to the `RediMinds` module and click `Send Modified Segments to RediMinds Backend` to capture the current state of polished segmentation.
4. The polished segmented files will be sent back to the RediMinds web server for further processing.

## Screenshots

Here are some screenshots to help you understand the usage of SlicerRediMinds:

![Screenshot 1](/Screenshots/Screenshot_1.png)

![Screenshot 2](/Screenshots/Screenshot_2.png)

![Screenshot 3](/Screenshots/Screenshot_3.png)

![Screenshot 4](/Screenshots/Screenshot_4.png)

![Screenshot 5](/Screenshots/Screenshot_5.png)

![Screenshot 6](/Screenshots/Screenshot_6.png)

![Screenshot 7](/Screenshots/Screenshot_7.png)

![Screenshot 8](/Screenshots/Screenshot_8.png)

![Screenshot 9](/Screenshots/Screenshot_9.png)

## Support

If you encounter any issues while using SlicerRediMinds, please contact the RediMinds support team at <a href="mailto:slicer-support@RediMinds.com">slicer-support@RediMinds.com</a>.

## Credits

A part of this Slicer extension was built with the help of code from [SlicerSandbox](https://github.com/PerkLab/SlicerSandbox/blob/master/LoadRemoteFile/LoadRemoteFile.py). We thank the original authors for their contributions.

Thank you for using SlicerRediMinds!
