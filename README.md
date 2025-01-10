# HyperHDR Control for Home Assistant

A Home Assistant integration to control HyperHDR LED controller. This integration provides a switch to control the USB capture device and buttons to activate various effects.

## Features

- Control USB Video Capture device (on/off)
- Activate various effects with buttons:
  - Atomic Swirl
  - Blue mood blobs
  - Breath
  - Candle
  - Cinema brighten/dim lights
  - And many more!

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Add"
7. Search for "HyperHDR Control" in HACS
8. Click "Download"
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/hyperhdr_control` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "HyperHDR Control"
4. Enter your HyperHDR server's IP address and port (default: 8090)

## Usage

### USB Capture Control
- Use the "HyperHDR USB Capture" switch to turn the video capture on or off

### Effects
- Each effect is available as a button in Home Assistant
- Press any effect button to activate that effect
- Effects will run indefinitely until another effect is activated or the USB capture is turned off

## Support

If you encounter any issues or have suggestions, please open an issue on GitHub. 