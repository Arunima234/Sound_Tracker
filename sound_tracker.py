"""
🎵 Sound Tracker – Eye Iris Visualizer  (Black & White Edition)
===============================================================
• Pure black & white – no RGB colour shifts
• Captures ALL PC audio (Spotify, YouTube, etc.) via Stereo Mix
• Falls back to microphone if Stereo Mix is not found

Requirements:
    pip install sounddevice numpy pygame

Setup for PC audio capture (Windows):
    1. Right-click speaker icon → Sounds → Recording tab
    2. Right-click empty area → Show Disabled Devices
    3. Enable "Stereo Mix" → Set as Default Device
    Then re-run this script.

Run:
    python sound_tracker.py
"""
# cspell:ignore indata wasapi rfftfreq freqs roff consolas greyscale gsurf hanning lsurf rfft rsurf samplerate  

import numpy as np
import pygame
import sounddevice as sd
import math
import sys
from collections import deque
import threading

# ── Audio Config ──────────────────────────────────────────────────────────────
CHUNK    = 1024
RATE     = 44100
CHANNELS = 1

BASS_LOW  = 60;   BASS_HIGH  = 250
MID_LOW   = 250;  MID_HIGH   = 2000
HIGH_LOW  = 2000; HIGH_HIGH  = 8000

# ── Display ───────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 950, 750
FPS           = 300

# ── Shared audio buffer ───────────────────────────────────────────────────────
audio_buffer = np.zeros(CHUNK, dtype=np.float32)
buffer_lock  = threading.Lock()


def audio_callback(indata, _frames, _time_info, _status):
    global audio_buffer
    mono = indata[:, 0] if indata.ndim > 1 else indata.flatten()
    with buffer_lock:
        audio_buffer = (
            mono[-CHUNK:] if len(mono) >= CHUNK
            else np.pad(mono, (CHUNK - len(mono), 0))
        )


def find_stereo_mix():
    """Return device index of Stereo Mix / loopback, or None."""
    devices = sd.query_devices()
    keywords = ["stereo mix", "wave out mix", "what u hear",
                 "loopback", "wasapi", "speakers (loopback)"]
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            name_lower = d["name"].lower()
            if any(kw in name_lower for kw in keywords):
                return i, d["name"]
    return None, None


def freq_band_energy(fft_data, low_hz, high_hz):
    freqs = np.fft.rfftfreq(CHUNK, d=1 / RATE)
    mask  = (freqs >= low_hz) & (freqs <= high_hz)
    band  = fft_data[mask]
    return float(np.sqrt(np.mean(band ** 2))) if len(band) > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
#  Drawing — pure black & white palette
# ─────────────────────────────────────────────────────────────────────────────

def draw_eye_iris(surface, cx, cy, iris_r, pupil_r, bass, mid, high, frame):
    """
    Draw a detailed black-and-white eye iris with flowing tendrils,
    exactly like the reference image.
    """
    # Dark base circle
    pygame.draw.circle(surface, (6, 6, 6), (cx, cy), iris_r)

    rng = np.random.default_rng(42)   # fixed seed = stable fibre shape
    num_fibres = 200

    for i in range(num_fibres):
        base_angle = (i / num_fibres) * math.tau
        segments   = 12
        prev_x = cx + math.cos(base_angle) * (pupil_r + 4)
        prev_y = cy + math.sin(base_angle) * (pupil_r + 4)

        noise_seed = rng.random(segments) * math.tau

        for s in range(1, segments + 1):
            t         = s / segments
            radius_at = pupil_r + (iris_r - pupil_r) * t

            # Organic wobble – reacts to mid freq and bass
            wobble = (
                0.20 * math.sin(noise_seed[s - 1] + frame * 0.025 + mid * 7)
              + 0.08 * math.sin(frame * 0.06 + i * 0.11)
              + 0.12 * bass * math.sin(frame * 0.09 + i * 0.09)
            )
            angle = base_angle + wobble

            nx = cx + math.cos(angle) * radius_at
            ny = cy + math.sin(angle) * radius_at

            # Brightness: bright near inner edge, dims toward outer rim
            bright = int(200 + 55 * (1 - t) * (1 + bass))
            bright = min(255, bright)

            # Every ~10th fibre is a thick "main branch"
            if i % 10 == 0:
                thick = 2 if t < 0.4 else 1
            else:
                thick = 1

            pygame.draw.line(surface,
                             (bright, bright, bright),
                             (int(prev_x), int(prev_y)),
                             (int(nx), int(ny)),
                             thick)
            prev_x, prev_y = nx, ny

    # ── Secondary finer fibres (fills gaps, denser texture) ──────────────────
    rng2 = np.random.default_rng(99)
    for i in range(120):
        base_angle = (i / 120) * math.tau + (math.pi / 120)
        noise2     = rng2.random(8) * math.tau
        prev_x = cx + math.cos(base_angle) * (pupil_r + 10)
        prev_y = cy + math.sin(base_angle) * (pupil_r + 10)
        for s in range(1, 9):
            t         = s / 8
            radius_at = (pupil_r + 12) + (iris_r * 0.75 - pupil_r) * t
            wobble    = (
                0.14 * math.sin(noise2[s - 1] + frame * 0.03 + mid * 5)
              + 0.06 * bass * math.sin(frame * 0.08 + i * 0.15)
            )
            angle = base_angle + wobble
            nx = cx + math.cos(angle) * radius_at
            ny = cy + math.sin(angle) * radius_at
            bright = int(130 + 80 * (1 - t))
            pygame.draw.line(surface,
                             (bright, bright, bright),
                             (int(prev_x), int(prev_y)),
                             (int(nx), int(ny)), 1)
            prev_x, prev_y = nx, ny

    # ── Outer dotted ring ─────────────────────────────────────────────────────
    dot_count = 160
    for d in range(dot_count):
        angle = (d / dot_count) * math.tau
        dot_r = iris_r - 4 + int(high * 4)
        dx = int(cx + math.cos(angle) * dot_r)
        dy = int(cy + math.sin(angle) * dot_r)
        bright = 80 + int(100 * high)
        pygame.draw.circle(surface, (bright, bright, bright), (dx, dy), 1)

    # ── Inner bright corona ring ──────────────────────────────────────────────
    corona_r = pupil_r + int(6 + bass * 18)
    for roff in range(5, 0, -1):
        alpha = 60 - roff * 10
        rsurf = pygame.Surface((corona_r * 2 + 12, corona_r * 2 + 12), pygame.SRCALPHA)
        pygame.draw.circle(rsurf,
                           (255, 255, 255, alpha),
                           (corona_r + 6, corona_r + 6),
                           corona_r + roff, roff + 1)
        surface.blit(rsurf, (cx - corona_r - 6, cy - corona_r - 6))

    # ── Pupil – dilates with bass ──────────────────────────────────────────────
    actual_pupil = int(pupil_r * (0.65 + bass * 1.0))
    actual_pupil = min(actual_pupil, iris_r - 12)

    # Soft dark edge
    for layer in range(8, 0, -1):
        lsurf = pygame.Surface((actual_pupil * 2 + 22, actual_pupil * 2 + 22), pygame.SRCALPHA)
        pygame.draw.circle(lsurf,
                           (0, 0, 0, 255 - layer * 12),
                           (actual_pupil + 11, actual_pupil + 11),
                           actual_pupil + layer)
        surface.blit(lsurf, (cx - actual_pupil - 11, cy - actual_pupil - 11))

    pygame.draw.circle(surface, (0, 0, 0), (cx, cy), actual_pupil)

    # White glint
    hl_r = max(3, int(actual_pupil * 0.18))
    hl_x = cx - int(actual_pupil * 0.32)
    hl_y = cy - int(actual_pupil * 0.32)
    pygame.draw.circle(surface, (255, 255, 255), (hl_x, hl_y), hl_r)
    pygame.draw.circle(surface, (180, 180, 180), (hl_x + 2, hl_y + 2), max(1, hl_r // 2))


def draw_outer_glow(surface, cx, cy, radius, bass):
    """Subtle white glow ring on bass hits."""
    for layer in range(6, 0, -1):
        alpha = int(35 * (layer / 6) ** 2 * (0.3 + bass * 0.7))
        r_l   = radius + layer * 6
        gsurf = pygame.Surface((r_l * 2, r_l * 2), pygame.SRCALPHA)
        pygame.draw.circle(gsurf, (220, 220, 220, alpha), (r_l, r_l), r_l, layer * 2)
        surface.blit(gsurf, (cx - r_l, cy - r_l), special_flags=pygame.BLEND_RGBA_ADD)


def draw_spectrum_bars(surface, fft_data, rect):
    """Black & white spectrum bars."""
    x0, y0, bw, bh = rect
    num_bars = 80
    freqs    = np.fft.rfftfreq(CHUNK, d=1 / RATE)
    max_freq = 8000
    bar_w    = bw // num_bars

    for i in range(num_bars):
        frac   = i / num_bars
        f_low  = frac ** 2 * max_freq
        f_hi   = ((frac + 1 / num_bars) ** 2) * max_freq
        mask   = (freqs >= f_low) & (freqs < f_hi)
        band   = fft_data[mask]
        energy = float(np.sqrt(np.mean(band ** 2))) if len(band) > 0 else 0.0
        bar_h  = min(bh, int(energy * bh * 0.95))
        # Gradient: bright white at top, dimmer at base
        bright = int(180 + 75 * (1 - frac))
        col    = (bright, bright, bright)
        bx = x0 + i * bar_w
        by = y0 + bh - bar_h
        pygame.draw.rect(surface, col, (bx + 1, by, bar_w - 2, bar_h))
        # White cap
        pygame.draw.rect(surface, (255, 255, 255), (bx + 1, by, bar_w - 2, 2))


def draw_waveform(surface, waveform_buf, center_y, width):
    data = list(waveform_buf)
    if len(data) < 2:
        return
    step = width / len(data)
    pts  = [(int(i * step), int(center_y + v * 45)) for i, v in enumerate(data)]
    pygame.draw.lines(surface, (60, 60, 60), False, pts, 1)


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("Sound Tracker")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock  = pygame.time.Clock()

    try:
        font_big   = pygame.font.SysFont("consolas", 20, bold=True)
        font_small = pygame.font.SysFont("consolas", 13)
    except Exception:
        font_big   = pygame.font.Font(None, 26)
        font_small = pygame.font.Font(None, 17)

    # ── Find best audio device ─────────────────────────────────────────────────
    device_idx, device_name = find_stereo_mix()
    if device_idx is not None:
        print(f"[Audio] ✅ Found loopback device: '{device_name}' (index {device_idx})")
        print("[Audio]    Will capture ALL PC audio (music, YouTube, etc.)")
    else:
        print("[Audio] ⚠  Stereo Mix not found — using default mic input.")
        print("[Audio]    To capture app audio: enable 'Stereo Mix' in Windows Sound settings.")

    stream_ok = False
    stream    = None
    try:
        stream = sd.InputStream(
            samplerate=RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=CHUNK,
            device=device_idx,       # None = system default (mic)
            callback=audio_callback,
        )
        stream.start()
        stream_ok = True
        actual_name = device_name or sd.query_devices(kind="input")["name"]
        print(f"[Audio] 🎙  Stream open on: {actual_name}")
    except Exception as e:
        print(f"[Audio] ❌ Stream error: {e}")

    # ── Layout ────────────────────────────────────────────────────────────────
    SPEC_H  = 110
    MARGIN  = 18
    EYE_AREA = HEIGHT - SPEC_H - MARGIN * 2
    IRIS_BASE  = min(EYE_AREA, WIDTH) // 2 - 35
    IRIS_MIN   = IRIS_BASE - 25
    PUPIL_BASE = int(IRIS_BASE * 0.33)

    # Ball physics
    ex, ey = float(WIDTH // 2), float(MARGIN + EYE_AREA // 2)
    vx, vy = 1.6, -1.0
    GRAVITY  = 0.22
    FRICTION = 0.97
    BOUNCE   = 0.68

    bass_hist  = deque([0.0] * 14, maxlen=14)
    mid_hist   = deque([0.0] * 8,  maxlen=8)
    waveform   = deque([0.0] * WIDTH, maxlen=WIDTH)
    fft_smooth = np.zeros(CHUNK // 2 + 1)
    frame      = 0

    # Static background
    bg = pygame.Surface((WIDTH, HEIGHT))
    bg.fill((0, 0, 0))
    for gx in range(0, WIDTH, 70):
        pygame.draw.line(bg, (10, 10, 10), (gx, 0), (gx, HEIGHT), 1)
    for gy in range(0, HEIGHT, 70):
        pygame.draw.line(bg, (10, 10, 10), (0, gy), (WIDTH, gy), 1)

    running = True
    while running:
        clock.tick(FPS)
        frame += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # ── Audio ─────────────────────────────────────────────────────────────
        raw_bass = raw_mid = raw_high = 0.0
        if stream_ok:
            with buffer_lock:
                samples = audio_buffer.copy()
            waveform.extend(samples[::max(1, CHUNK // WIDTH)])
            windowed   = samples * np.hanning(len(samples))
            fft_raw    = np.abs(np.fft.rfft(windowed))
            fft_smooth = fft_smooth * 0.72 + fft_raw * 0.28
            raw_bass = freq_band_energy(fft_smooth, BASS_LOW,  BASS_HIGH)
            raw_mid  = freq_band_energy(fft_smooth, MID_LOW,   MID_HIGH)
            raw_high = freq_band_energy(fft_smooth, HIGH_LOW,  HIGH_HIGH)

        bass_hist.append(raw_bass)
        mid_hist.append(raw_mid)

        bass = min(1.0, np.mean(bass_hist) * 18)
        mid  = min(1.0, np.mean(mid_hist)  * 12)
        high = min(1.0, raw_high            * 8)

        # ── Physics ───────────────────────────────────────────────────────────
        vx += (mid - 0.5) * 2.2 + math.sin(frame * 0.033) * 0.5
        vy -= bass * 13
        vy += GRAVITY
        vx *= FRICTION
        vy *= FRICTION
        ex += vx
        ey += vy

        iris_r  = int(IRIS_MIN + (IRIS_BASE - IRIS_MIN) * (0.55 + bass * 0.45))
        pupil_r = PUPIL_BASE

        left_wall  = MARGIN + iris_r
        right_wall = WIDTH  - MARGIN - iris_r
        top_wall   = MARGIN + iris_r
        bot_wall   = HEIGHT - SPEC_H - MARGIN - iris_r

        if ex < left_wall:  ex = left_wall;  vx =  abs(vx) * BOUNCE
        if ex > right_wall: ex = right_wall; vx = -abs(vx) * BOUNCE
        if ey < top_wall:   ey = top_wall;   vy =  abs(vy) * BOUNCE
        if ey > bot_wall:   ey = bot_wall;   vy = -abs(vy) * BOUNCE

        # ── Render ────────────────────────────────────────────────────────────
        screen.blit(bg, (0, 0))

        # Waveform
        draw_waveform(screen, waveform, HEIGHT - SPEC_H - 22, WIDTH)

        # Outer glow (white, subtle)
        draw_outer_glow(screen, int(ex), int(ey), iris_r, bass)

        # Eye rendered on its own surface
        eye_surf = pygame.Surface((iris_r * 2 + 24, iris_r * 2 + 24), pygame.SRCALPHA)
        draw_eye_iris(eye_surf, iris_r + 12, iris_r + 12,
                      iris_r, pupil_r, bass, mid, high, frame)
        screen.blit(eye_surf, (int(ex) - iris_r - 12, int(ey) - iris_r - 12))

        # Spectrum bars
        draw_spectrum_bars(screen, fft_smooth, (0, HEIGHT - SPEC_H, WIDTH, SPEC_H - 5))
        pygame.draw.rect(screen, (28, 28, 28), (0, HEIGHT - SPEC_H, WIDTH, SPEC_H - 5), 1)

        # HUD bars – greyscale
        def bar_hud(label, val, brightness, yo):
            screen.blit(font_small.render(label, True, (140, 140, 140)), (10, yo))
            pygame.draw.rect(screen, (20, 20, 20),  (65, yo + 3, 110, 9))
            c = (brightness, brightness, brightness)
            pygame.draw.rect(screen, c, (65, yo + 3, int(110 * val), 9))

        bar_hud("BASS",  bass,  230, 10)
        bar_hud("MID",   mid,   170, 26)
        bar_hud("HIGH",  high,  120, 42)

        # Device label top-right
        src_label = device_name if device_name else "Microphone"
        src_surf  = font_small.render(f"SRC: {src_label[:30]}", True, (60, 60, 60))
        screen.blit(src_surf, (WIDTH - src_surf.get_width() - 10, 28))

        title = font_big.render(" •  SOUND TRACKER   • ", True, (160, 160, 160))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 10))
        screen.blit(font_small.render("ESC to quit", True, (55, 55, 55)), (WIDTH - 82, 10))

        if not stream_ok:
            warn = font_big.render("⚠  No audio input detected", True, (200, 200, 200))
            screen.blit(warn, (WIDTH // 2 - warn.get_width() // 2, HEIGHT // 2))

        pygame.display.flip()

    if stream:
        stream.stop()
        stream.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()