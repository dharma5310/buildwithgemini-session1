import math
import struct
import wave
import numpy as np

SAMPLE_RATE = 44100
BPM = 88
BEAT_DUR = 60.0 / BPM  # ~0.6818 sec
BAR_DUR = BEAT_DUR * 4  # ~2.727 sec
TOTAL_DURATION = 60.0  # 60 seconds
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

# Chord Frequencies (Hz)
# 1. Fmaj7: F3, A3, C4, E4
# 2. Em7:   E3, G3, B3, D4
# 3. Dm7:   D3, F3, A3, C4
# 4. Cmaj7: C3, E3, G3, B3
CHORDS = [
    ([174.61, 220.00, 261.63, 329.63], 138.59),  # Fmaj7, Bass F2 (87.31)
    ([164.81, 196.00, 246.94, 293.66], 123.47),  # Em7,   Bass E2 (82.41)
    ([146.83, 174.61, 220.00, 261.63], 110.00),  # Dm7,   Bass D2 (73.42)
    ([130.81, 164.81, 196.00, 246.94], 130.81),  # Cmaj7, Bass C2 (65.41)
]

# Simple pentatonic melody note frequencies (E4, G4, A4, C5, D5, E5)
MELODY_NOTES = [329.63, 392.00, 440.00, 523.25, 587.33, 659.25]

def generate_lofi_track():
    print("Synthesizing upbeat lo-fi track...")
    audio = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    t = np.arange(TOTAL_SAMPLES) / SAMPLE_RATE

    # 1. Vinyl Texture (soft crackle/hiss)
    vinyl_hiss = np.random.normal(0, 0.012, TOTAL_SAMPLES)
    # Add random pop/crackle spikes
    pops = (np.random.rand(TOTAL_SAMPLES) > 0.9995).astype(np.float32) * np.random.uniform(0.05, 0.15, TOTAL_SAMPLES)
    audio += (vinyl_hiss + pops) * 0.4

    # 2. Chords & Bass Loops
    num_bars = int(np.ceil(TOTAL_DURATION / BAR_DUR))
    for bar in range(num_bars):
        bar_start_sample = int(bar * BAR_DUR * SAMPLE_RATE)
        chord_idx = bar % len(CHORDS)
        notes, bass_freq = CHORDS[chord_idx]

        # Chord duration = 1 bar
        bar_samples = int(BAR_DUR * SAMPLE_RATE)
        if bar_start_sample + bar_samples > TOTAL_SAMPLES:
            bar_samples = TOTAL_SAMPLES - bar_start_sample
        
        tb = t[bar_start_sample : bar_start_sample + bar_samples] - (bar * BAR_DUR)

        # Tremolo / LFO at 3.5 Hz
        lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 3.5 * tb)
        # Envelope with soft attack and slow decay
        env = np.exp(-1.2 * tb / BAR_DUR)

        # Synthesize EP Chord
        chord_wave = np.zeros(bar_samples, dtype=np.float32)
        for f in notes:
            # Fundamental + soft harmonics
            sine = np.sin(2 * np.pi * f * tb)
            harm1 = 0.3 * np.sin(2 * np.pi * f * 2 * tb)
            harm2 = 0.1 * np.sin(2 * np.pi * f * 3 * tb)
            chord_wave += (sine + harm1 + harm2) * 0.12

        audio[bar_start_sample : bar_start_sample + bar_samples] += chord_wave * lfo * env

        # Synthesize Warm Sub Bass
        bass_wave = np.sin(2 * np.pi * (bass_freq / 2.0) * tb) * 0.22 * np.exp(-0.8 * tb / BAR_DUR)
        audio[bar_start_sample : bar_start_sample + bar_samples] += bass_wave

    # 3. Upbeat Lo-Fi Drum Beat (Kick, Snare, Hi-Hat)
    beat_samples = int(BEAT_DUR * SAMPLE_RATE)
    num_beats = int(TOTAL_DURATION / BEAT_DUR)

    for beat in range(num_beats):
        b_start = int(beat * BEAT_DUR * SAMPLE_RATE)

        # Kick on beat 1 & beat 3 (and syncopated beat 3.5)
        if beat % 4 in [0, 2] or (beat % 8 == 3 and np.random.rand() > 0.3):
            k_len = int(0.12 * SAMPLE_RATE)
            if b_start + k_len < TOTAL_SAMPLES:
                tk = np.linspace(0, 0.12, k_len)
                freq_sweep = 120 * np.exp(-30 * tk) + 45
                kick = np.sin(2 * np.pi * freq_sweep * tk) * np.exp(-20 * tk) * 0.35
                audio[b_start : b_start + k_len] += kick

        # Snare on beat 2 & beat 4
        if beat % 4 in [1, 3]:
            s_len = int(0.18 * SAMPLE_RATE)
            if b_start + s_len < TOTAL_SAMPLES:
                ts = np.linspace(0, 0.18, s_len)
                noise = np.random.normal(0, 0.2, s_len) * np.exp(-25 * ts)
                body = np.sin(2 * np.pi * 180 * ts) * np.exp(-30 * ts) * 0.15
                snare = (noise + body) * 0.28
                audio[b_start : b_start + s_len] += snare

        # Hi-Hats on every 8th note (sub-beat)
        for sub in [0, 0.5]:
            hh_start = int((beat + sub) * BEAT_DUR * SAMPLE_RATE)
            hh_len = int(0.05 * SAMPLE_RATE)
            if hh_start + hh_len < TOTAL_SAMPLES:
                thh = np.linspace(0, 0.05, hh_len)
                hh = np.random.normal(0, 0.15, hh_len) * np.exp(-60 * thh) * (0.12 if sub == 0 else 0.08)
                audio[hh_start : hh_start + hh_len] += hh

    # 4. Lo-Fi Pluck Melody (Occasional sweet lead notes)
    for beat in range(0, num_beats, 2):
        if np.random.rand() > 0.35:
            m_note = np.random.choice(MELODY_NOTES)
            m_start = int((beat + np.random.choice([0, 0.5, 1.0])) * BEAT_DUR * SAMPLE_RATE)
            m_len = int(0.4 * SAMPLE_RATE)
            if m_start + m_len < TOTAL_SAMPLES:
                tm = np.linspace(0, 0.4, m_len)
                pluck = np.sin(2 * np.pi * m_note * tm) * np.exp(-10 * tm) * 0.12
                # Echo / Delay effect
                delay_samples = int(0.25 * SAMPLE_RATE)
                audio[m_start : m_start + m_len] += pluck
                if m_start + m_len + delay_samples < TOTAL_SAMPLES:
                    audio[m_start + delay_samples : m_start + m_len + delay_samples] += pluck * 0.4

    # Soft master limiting & normalization
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = (audio / max_val) * 0.85

    # Convert to 16-bit PCM WAV
    int_audio = (audio * 32767).astype(np.int16)
    
    out_path = "/config/Desktop/Session1/lofi_background.wav"
    with wave.open(out_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int_audio.tobytes())
    
    print(f"Generated upbeat lo-fi track: {out_path}")
    return out_path

if __name__ == "__main__":
    generate_lofi_track()
