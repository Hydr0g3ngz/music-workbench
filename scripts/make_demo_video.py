"""Edit real UI captures and an exported sketch into a captioned demo (av, Pillow, numpy)."""

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont


def build(captures, audio, output, gif, font):
    shots = [
        ("listen.png", "01  先听见一段音乐", "Listen to a sketch you can edit"),
        ("layers.png", "02  拆开听，认识每一层", "Hear drums, keys, bass and pad"),
        ("melody.png", "03  改一个音，让它成为自己的", "Change a note. Undo any time."),
        ("balance.png", "04  调整混音，给声音留出空间", "Balance the parts in the mixer"),
        ("export.png", "05  导出声音，也保留可编辑工程", "Export WAV. Keep an MWB project."),
        ("complete.png", "第一段音乐，只是开始", "Start creating. Add local AI when ready."),
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    title_font = ImageFont.truetype(str(font), 34)
    sub_font = ImageFont.truetype(str(font), 25)
    label_font = ImageFont.truetype(str(font), 20)
    images = []
    for filename, title, subtitle in shots:
        canvas = Image.new("RGB", (1920, 1080), "#11151e")
        shot = Image.open(captures / filename).convert("RGB")
        shot.thumbnail((1760, 890), Image.Resampling.LANCZOS)
        canvas.paste(shot, ((1920 - shot.width) // 2, 93 + (890 - shot.height) // 2))
        draw = ImageDraw.Draw(canvas)
        draw.text((45, 18), title, font=title_font, fill="#edeafa")
        draw.text((1140, 27), "Music Workbench  |  Windows preview", font=sub_font, fill="#bcb1e0")
        draw.text((45, 1003), subtitle, font=sub_font, fill="#d2c5ff")
        draw.text(
            (45, 1040),
            "真实操作画面节选 / Edited UI highlights · 示例配乐 / Exported example audio",
            font=label_font, fill="#b9c8ce",
        )
        images.append(canvas)

    samples, rate = sf.read(audio, dtype="float32", always_2d=True)
    if rate != 44100 or samples.shape[1] != 2:
        raise ValueError("Use a stereo 44.1 kHz export")
    fps, seconds_per_shot = 20, 6
    frames = fps * seconds_per_shot * len(images)
    count = frames * rate // fps
    music = np.tile(samples, (int(np.ceil(count / len(samples))), 1))[:count].copy()
    # This is background accompaniment; preserve headroom and fade both ends of the edit.
    music *= .8
    fade = np.linspace(0, 1, rate, dtype=np.float32)
    music[:rate] *= fade[:, None]
    music[-rate:] *= fade[::-1, None]
    with av.open(str(output), "w", options={"movflags": "+faststart"}) as container:
        video = container.add_stream("libx264", rate=fps)
        video.width, video.height, video.pix_fmt = 1920, 1080, "yuv420p"
        video.options = {"crf": "22", "preset": "fast"}
        sound = container.add_stream("aac", rate=rate)
        sound.layout = "stereo"
        sound.bit_rate = 160000
        for index in range(frames):
            frame = av.VideoFrame.from_image(images[index // (fps * seconds_per_shot)])
            frame.pts, frame.time_base = index, Fraction(1, fps)
            for packet in video.encode(frame):
                container.mux(packet)
            start, end = index * rate // fps, (index + 1) * rate // fps
            block = np.ascontiguousarray(music[start:end].T)
            frame = av.AudioFrame.from_ndarray(block, format="fltp", layout="stereo")
            frame.sample_rate, frame.pts, frame.time_base = rate, start, Fraction(1, rate)
            for packet in sound.encode(frame):
                container.mux(packet)
        for stream in (video, sound):
            for packet in stream.encode():
                container.mux(packet)
    gif.parent.mkdir(parents=True, exist_ok=True)
    thumbs = [im.resize((960, 540), Image.Resampling.LANCZOS) for im in images]
    thumbs[0].save(gif, save_all=True, append_images=thumbs[1:], duration=3000, loop=0)
    metadata = {
        "kind": "edited UI screenshots with exported example accompaniment; not real-time video",
        "seconds": frames / fps, "resolution": [1920, 1080], "fps": fps,
        "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
        "captures": {name: hashlib.sha256((captures / name).read_bytes()).hexdigest()
                     for name, _, _ in shots},
        "mp4_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "gif_sha256": hashlib.sha256(gif.read_bytes()).hexdigest(),
    }
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gif", type=Path, required=True)
    parser.add_argument("--font", type=Path, default=Path("C:/Windows/Fonts/msyh.ttc"))
    args = parser.parse_args()
    build(args.captures, args.audio, args.output, args.gif, args.font)
