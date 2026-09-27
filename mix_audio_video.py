import os
import subprocess
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

video_input = "/config/Desktop/Session1/demo_video.webm"
audio_input = "/config/Desktop/Session1/lofi_background.wav"
output_mp4 = "/config/Desktop/Session1/demo_video_with_lofi.mp4"
output_webm = "/config/Desktop/Session1/demo_video_with_lofi.webm"

print(f"Mixing {video_input} with lo-fi background music {audio_input}...")

# 1. Output MP4 format
cmd_mp4 = [
    ffmpeg_exe,
    "-y",
    "-i", video_input,
    "-i", audio_input,
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    output_mp4
]

res_mp4 = subprocess.run(cmd_mp4, capture_output=True, text=True)
if res_mp4.returncode == 0:
    print(f"SUCCESS! Mixed MP4 saved to: {output_mp4}")
else:
    print("MP4 mix error:", res_mp4.stderr[:500])

# 2. Output WebM format
cmd_webm = [
    ffmpeg_exe,
    "-y",
    "-i", video_input,
    "-i", audio_input,
    "-c:v", "copy",
    "-c:a", "libvpx_vp8" if "libvpx_vp8" in res_mp4.stderr else "libvorbis",
    "-shortest",
    output_webm
]

res_webm = subprocess.run(cmd_webm, capture_output=True, text=True)
if res_webm.returncode == 0:
    print(f"SUCCESS! Mixed WebM saved to: {output_webm}")
else:
    # Try alternative audio codec for webm
    cmd_webm_alt = [
        ffmpeg_exe,
        "-y",
        "-i", video_input,
        "-i", audio_input,
        "-c:v", "copy",
        "-shortest",
        output_webm
    ]
    res_alt = subprocess.run(cmd_webm_alt, capture_output=True, text=True)
    if res_alt.returncode == 0:
        print(f"SUCCESS! Mixed WebM saved to: {output_webm}")
    else:
        print("WebM mix error:", res_alt.stderr[:500])
