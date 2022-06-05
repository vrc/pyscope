# Simple python based live data visualisation.

The idea is to visualise data as they are being generated from a source that doesn't lend itself to be displayed on an Oscilloscope. In the current hard coded setup the data source is an accellerometer from Adafruit - or some test data being generated.
The core code was inspired by an Adafruit tutorial which can be found [here](https://learn.adafruit.com/pi-video-output-using-pygame?view=all)

The test setup being used is a 7", 1024x600 HDMI TFT touch screen attached to a Raspberry Pi - basic console installation (no X11). There is some issue with the SDL mouse driver and this particular touch screen which is why there is some odd code to get the current mouse position from an `evdev.InputDevice`.

Currently a lot of pieces are hard coded and puprose built which might change over time if this turns out to be useful to others.
Specifically the _widgets_ are in their infancy and hopefully get replaced with a dedicated library.

At this stage everything is highly experimental and it just barely does what it's supposed to do.
