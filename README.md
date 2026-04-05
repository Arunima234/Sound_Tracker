Sound Tracker – Eye Iris Visualizer
A real-time audio visualizer built with Python.  
A detailed black & white eye iris  bounces around your screen, with flowing tendrils that writhe and pulse to the beat of any sound playing on your PC.

Features
- 200+ radial fibre tendrils radiating from the pupil
- Pupil that dilates and contracts with bass
- Organic tendril movement reacting to mid frequencies
- Captures ALL PC audio (Spotify, YouTube, any app) via Stereo Mix
- Falls back to microphone if Stereo Mix is not enabled
- 64-band frequency spectrum display
- Live scrolling waveform
- Physics-based bouncing with gravity & wall collisions
- Pure black & white — no RGB colour shifts

Requirements
- Python 3.10+
- Windows 10/11 (tested), should work on Linux/macOS too

Run
```
python sound_tracker.py
```

Capture PC Audio (Music, YouTube, Spotify)
By default the app uses your microphone. To make it react to any app audio:

Windows – Enable Stereo Mix
1. Right-click the 🔊 speaker icon in the taskbar → Sounds
2. Go to the Recording tab
3. Right-click empty space → tick "Show Disabled Devices"
4. Find "Stereo Mix" → right-click → Enable
5. Right-click Stereo Mix → Set as Default Device
6. Re-run the script

The terminal will confirm:
```
[Audio] ✅ Found loopback device: 'Stereo Mix' (index 2)
[Audio]    Will capture ALL PC audio (music, YouTube, etc.)
```

Project Structure
```
sound-tracker/
├── sound_tracker.py   # Main application
└── README.md          # This file
```

How It Works
`sounddevice` : Captures audio from mic or Stereo Mix in real-time |
`numpy` : FFT (Fast Fourier Transform) to split audio into Bass / Mid / High bands |
`pygame` : Renders the eye, tendrils, spectrum, and waveform at 60 FPS |
 Physics : Simple gravity + friction + wall bounce system |
 Tendrils : 200 radial fibres with per-fibre noise offsets, animated with sine waves |



Customize
Open `sound_tracker.py` and tweak these values at the top:

```python
# Window size
WIDTH, HEIGHT = 950, 750

# Physics feel
GRAVITY  = 0.22
FRICTION = 0.97
BOUNCE   = 0.68

# Frequency bands (Hz)
BASS_LOW, BASS_HIGH = 60, 250
MID_LOW,  MID_HIGH  = 250, 2000
```


Dependencies
`sounddevice` : Audio input stream |
`numpy` : FFT & signal processing |
`pygame` : Graphics & window rendering |

License
MIT License — free to use, modify and share.

Credits
Built with Python, sounddevice, numpy, and pygame.  
Eye design inspired by detailed iris illustrations.
