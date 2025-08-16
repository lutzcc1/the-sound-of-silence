from pydub import AudioSegment
from functools import lru_cache

# -----------------------
# Tunables (safe defaults)
# -----------------------
FADE_MS = 3000          # loop seam fade length
BED_GAIN_DB = -20.0     # music bed level relative to original file
TARGET_PEAK_DBFS = -0.5 # final safety headroom
TINY_TAIL_FADE_MS = 80  # prevent end clicks on some players

# -----------------------
# Loaders & caching
# -----------------------
@lru_cache(maxsize=1)
def load_music_aligned(music_path, frame_rate, channels):
    """
    Decode once, align once, cache the result.
    """
    music = AudioSegment.from_file(music_path)  # WAV or anything ffmpeg can read
    music = music.set_channels(channels).set_frame_rate(frame_rate)
    return music

def load_narration(narration_path):
    return AudioSegment.from_file(narration_path)

# -----------------------
# Loop builder
# -----------------------
def build_loopable_unit(music, fade_ms, bed_gain_db):
    """
    Apply fixed bed gain and shape ends for looping:
    fade-in at start + fade-out at end.
    """
    bed = music + bed_gain_db  # pydub: "+" adds dB, "-" subtracts
    return bed.fade_in(fade_ms).fade_out(fade_ms)

def extend_with_overlap(unit, target_ms, crossfade_ms):
    """
    Repeat 'unit' overlapping by crossfade_ms until length >= target_ms.
    Simple while-loop avoids off-by-one length math.
    """
    loop = unit
    while len(loop) < target_ms:
        loop = loop.append(unit, crossfade=crossfade_ms)
    return loop[:target_ms]

# -----------------------
# Mix & safety
# -----------------------
def overlay_bed(narration, bed):
    return narration.overlay(bed)

def apply_peak_safety(seg, target_peak_dbfs):
    if seg.max_dBFS > target_peak_dbfs:
        adjust = target_peak_dbfs - seg.max_dBFS
        seg = seg.apply_gain(adjust)
    return seg

# -----------------------
# Public API
# -----------------------
def add_background_music(
    narration_path,
    music_path,
    fade_ms=FADE_MS,
    bed_gain_db=BED_GAIN_DB,
    target_peak_dbfs=TARGET_PEAK_DBFS,
    tiny_tail_fade_ms=TINY_TAIL_FADE_MS,
    out_path="mixed_phase7.wav",
):
    # Load narration first to know target format
    narration = load_narration(narration_path)

    # Cached, aligned music
    music_aligned = load_music_aligned(music_path, narration.frame_rate, narration.channels)

    # Build looped bed
    unit = build_loopable_unit(music_aligned, fade_ms=fade_ms, bed_gain_db=bed_gain_db)
    bed = extend_with_overlap(unit, target_ms=len(narration), crossfade_ms=fade_ms)

    # Mix
    mixed = overlay_bed(narration, bed)

    # Polish
    mixed = mixed.fade_out(tiny_tail_fade_ms)
    mixed = apply_peak_safety(mixed, target_peak_dbfs=target_peak_dbfs)

    # Export
    mixed.export(out_path, format="wav")
    return out_path

# -----------------------
# Example call
# -----------------------
if __name__ == "__main__":
    out = add_background_music(
        narration_path="meditation.wav",
        music_path="music.wav",
        fade_ms=3000,
        bed_gain_db=-20.0,
        target_peak_dbfs=-0.5,
        out_path="mixed_phase7.wav",
    )
    print("Wrote:", out)
