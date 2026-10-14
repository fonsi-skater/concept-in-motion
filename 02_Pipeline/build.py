#!/usr/bin/env python3
r"""Concept in Motion: script-to-video pipeline  (build.py)
=====================================================================
WHAT IT DOES
  scenes_xxx.json  ->  narration audio  ->  Manim animations timed to the audio
                   ->  final.mp4 + captions.srt + chapters.txt + metadata.txt

HOW IT WORKS (read this if something breaks)
  1. Reads the scenes file. Each scene has: narration (what you say), visual (what is shown),
     optional chapter (YouTube chapter title) and optional cues (phrases that trigger visuals).
  2. AUDIO per scene: if audio/scene_NN.wav (or mp3/m4a) exists it is used (your own recording),
     otherwise Piper text-to-speech makes it. Speed/pauses are applied here (--speed etc.).
  3. DURATION of that audio (ffprobe) tells the animation how long to run.
  4. CUES: each cue phrase is located inside the narration text and converted to a time
     (position in the text, weighted for punctuation pauses), then moved earlier by --lead
     so the visual appears BEFORE the words ("show, then say"). Estimated, not frame-exact.
  5. VISUAL: scenes.py is run with Manim, once per scene, with the settings passed through
     environment variables SCENE_SPEC, SCENE_DURATION, SCENE_CUES.
  6. Each scene video + its audio are muxed into build/clip_NN.mp4, all clips are joined with
     ffmpeg, and captions.srt / chapters.txt / metadata.txt are written next to the pipeline.

COMMANDS (run inside 02_Pipeline)
  python build.py scenes_nlp.json --preview --voice en_US-lessac-medium     fast 480p draft
  python build.py scenes_nlp.json --voice en_US-lessac-medium               final 1080p
  add  --speed 0.85 --sentence-pause 0.5 --scene-pause 0.8                  slower narration
  add  --only 4                                                             one scene only
  add  --lead 0.8                                                           visuals earlier (0.2 = later)
  python build.py scenes_nlp.json --metadata-only                           rewrite metadata.txt only

IMPORTANT
  * A build OVERWRITES final.mp4, captions.srt, chapters.txt, metadata.txt in this folder.
    Copy them into 03_Videos\Vxx_Name\Final right after each build.
  * Delete audio\scene_*.wav before building a NEW video, or old recordings get reused.
  * "cue phrase not found" = the phrase must be copied EXACTLY from that scene's narration.
  * If you add a visual type, add it to CLASSES below (see scenes.py for how to write one).

REQUIREMENTS: Python 3.10+, FFmpeg (ffmpeg + ffprobe on PATH), manim, piper-tts (optional if you record voice).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
CLASSES = {"title": "TitleCard", "bullets": "Bullets", "flow": "Flow", "code": "CodeCard", "restaurant": "Restaurant",
           "tokens": "Tokens", "wordmap": "WordMap", "pipeline": "Pipeline",
           "hub": "Hub", "agentloop": "AgentLoop",
           "probbars": "ProbBars", "genloop": "GenLoop",
           "neuralnet": "NeuralNet", "descent": "Descent", "losscurve": "LossCurve"}
PAD = 0.4  # seconds of silence after each scene


def run(cmd, **kw):
    print("> " + " ".join(str(c) for c in cmd))
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)])
    return float(out)


def find_recorded(n):
    for ext in ("wav", "mp3", "m4a", "flac", "ogg"):
        p = ROOT / "audio" / f"scene_{n:02d}.{ext}"
        if p.exists():
            return p
    return None


def make_audio(n, text, voice, out_wav, speed=1.0, sentence_pause=0.2):
    """Use your recording if present, otherwise Piper text-to-speech."""
    src = find_recorded(n)
    if src is None:
        if not voice:
            sys.exit(f"No audio for scene {n}. Record audio/scene_{n:02d}.wav or pass --voice <piper voice>.")
        raw = ROOT / "build" / f"raw_{n:02d}.wav"
        run([sys.executable, "-m", "piper", "-m", voice, "--data-dir", ROOT / "voices",
             "--length-scale", f"{1 / speed:.3f}", "--sentence-silence", f"{sentence_pause:.2f}",
             "-f", raw], input=text.encode())
        src = raw
        tempo = ""                       # Piper already applied the speed
    else:
        tempo = f"atempo={speed:.3f}," if abs(speed - 1.0) > 0.01 else ""   # slow a recording, keep pitch
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "44100", "-ac", "1",
         "-af", f"{tempo}apad=pad_dur={PAD}", out_wav])


def weight(text, upto):
    """Rough speaking time of text[:upto]: characters, plus extra for pauses at punctuation."""
    seg = text[:upto]
    return len(seg) + 10 * sum(seg.count(c) for c in ".?!:;") + 4 * seg.count(",")


def cue_times(n, narration, cues, speech, lead):
    """Turn cue phrases into seconds, shifted earlier by `lead` so visuals appear BEFORE the words."""
    if not cues:
        return {}
    if isinstance(cues, list):
        cues = {str(i): p for i, p in enumerate(cues)}
    whole = weight(narration, len(narration))
    out = {}
    for name, phrase in cues.items():
        i = narration.lower().find(phrase.lower())
        if i < 0:
            sys.exit(f"Scene {n}: cue phrase not found in narration: '{phrase}'")
        out[name] = max(speech * weight(narration, i) / whole - lead, 0.0)
    return out


def render_visual(n, visual, seconds, preview, cue_map):
    kind = visual.get("type")
    if kind not in CLASSES:
        sys.exit(f"Scene {n}: unknown visual type '{kind}'. Use one of {list(CLASSES)}")
    env = dict(os.environ, SCENE_SPEC=json.dumps(visual), SCENE_DURATION=f"{seconds:.3f}",
               SCENE_CUES=json.dumps(cue_map))
    res, fps = ("854,480", "15") if preview else ("1920,1080", "30")
    media = ROOT / "build" / "media"
    run([sys.executable, "-m", "manim", "render", "-r", res, "--fps", fps,
         "--media_dir", media, "--disable_caching", "--progress_bar", "none", "-o", f"scene_{n:02d}",
         ROOT / "scenes.py", CLASSES[kind]], env=env,
        stdout=subprocess.DEVNULL if not os.environ.get("VERBOSE") else None)
    hits = [p for p in (media / "videos").rglob(f"scene_{n:02d}.mp4") if "partial" not in str(p)]
    if not hits:
        sys.exit(f"Scene {n}: Manim produced no video.")
    return max(hits, key=lambda p: p.stat().st_mtime)


def mux(video, wav, seconds, out):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", wav,
         "-map", "0:v", "-map", "1:a", "-t", f"{seconds:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-r", "15" if "preview" in str(out) else "30",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", out])


def stamp(t, sep=","):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def caption_chunks(text, max_words=9):
    words, chunks = text.split(), []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i:i + max_words]))
    return chunks


def read_chapters():
    p = ROOT / "chapters.txt"
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


def check_chapters(text):
    """YouTube chapter rules: first at 0:00, at least 3, each at least 10 seconds."""
    warnings, starts = [], []
    for line in text.splitlines():
        m, s = line.split(" ", 1)[0].split(":")
        starts.append(int(m) * 60 + int(s))
    if not starts or starts[0] != 0:
        warnings.append("first chapter must start at 0:00")
    if len(starts) < 3:
        warnings.append("YouTube needs at least 3 chapters")
    if any(b - a < 10 for a, b in zip(starts, starts[1:])):
        warnings.append("every chapter must last at least 10 seconds")
    return warnings


def write_metadata(data):
    yt = data.get("youtube")
    if not yt:
        print("No 'youtube' section in scenes.json, skipping metadata.txt")
        return
    chapters = read_chapters()
    if not chapters:
        sys.exit("chapters.txt not found. Run a full build first.")
    description = (f"{yt['summary']}\n\nChapters\n{chapters}\n\n"
                   "New concept every week on Concept in Motion. Subscribe, and comment with what you want explained next.\n\n"
                   f"Next video: {yt.get('next_video', 'coming soon')}\n\n{' '.join(yt.get('hashtags', []))}")
    tags = ", ".join(yt.get("tags", []))
    problems = [f"chapters: {w}" for w in check_chapters(chapters)]
    if len(yt["title"]) > 100:
        problems.append("title is over 100 characters")
    if len(tags) > 500:
        problems.append("tags are over 500 characters")
    if len(description) > 5000:
        problems.append("description is over 5000 characters")
    out = ["TITLE (copy into YouTube Studio)", yt["title"], "",
           "DESCRIPTION (copy everything between the lines)", "-" * 40, description, "-" * 40, "",
           "TAGS (Show more > Tags)", tags, "",
           f"PLAYLIST: {yt.get('playlist', '')}", f"CATEGORY: {yt.get('category', 'Education')}",
           "AUDIENCE: No, it's not made for kids", "VISIBILITY: Private first, then Public after review", "",
           "FILES: final.mp4 (or final_music.mp4), captions.srt, thumbnail PNG"]
    if problems:
        out += ["", "FIX BEFORE UPLOADING:"] + [f"- {p}" for p in problems]
    (ROOT / "metadata.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("Wrote metadata.txt" + ("  (WARNINGS: " + "; ".join(problems) + ")" if problems else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes")
    ap.add_argument("--voice", help="Piper voice name, e.g. en_US-lessac-medium")
    ap.add_argument("--preview", action="store_true", help="480p draft, much faster")
    ap.add_argument("--only", type=int, help="render just this scene number")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="narration speed: 1.0 normal, 0.85 = 15%% slower (recommended for beginners), 0.75 = much slower")
    ap.add_argument("--sentence-pause", type=float, default=0.2,
                    help="seconds of silence between sentences with a Piper voice (try 0.5)")
    ap.add_argument("--scene-pause", type=float, default=0.4,
                    help="seconds of silence after each scene (try 0.8)")
    ap.add_argument("--lead", type=float, default=0.5, help="seconds a visual appears BEFORE the words (default 0.5)")
    ap.add_argument("--metadata-only", action="store_true", help="only write metadata.txt from the existing chapters.txt")
    args = ap.parse_args()

    global PAD
    PAD = args.scene_pause
    if not 0.5 <= args.speed <= 1.5:
        sys.exit("--speed must be between 0.5 and 1.5")
    data = json.loads(Path(args.scenes).read_text(encoding="utf-8"))
    if args.metadata_only:
        write_metadata(data)
        return
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    suffix = "_preview" if args.preview else ""
    clips, srt, chapters, t = [], [], [], 0.0

    for n, scene in enumerate(data["scenes"], start=1):
        if args.only and n != args.only:
            continue
        print(f"\n=== Scene {n}: {scene['narration'][:50]}...")
        wav = build / f"audio_{n:02d}.wav"
        make_audio(n, scene["narration"], args.voice, wav, args.speed, args.sentence_pause)
        seconds = duration(wav)
        cue_map = cue_times(n, scene["narration"], scene.get("cues"), max(seconds - PAD, 0.5), args.lead)
        video = render_visual(n, scene["visual"], seconds, args.preview, cue_map)
        clip = build / f"clip_{n:02d}{suffix}.mp4"
        mux(video, wav, seconds, clip)
        clips.append(clip)

        speech = max(seconds - PAD, 0.5)
        chunks = caption_chunks(scene["narration"])
        total_words = sum(len(c.split()) for c in chunks)
        cur = t
        for c in chunks:
            span = speech * len(c.split()) / total_words
            srt.append((cur, cur + span, c))
            cur += span
        if scene.get("chapter"):
            chapters.append((t, scene["chapter"]))
        t += seconds

    listing = build / "clips.txt"
    listing.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
    final = ROOT / f"final{suffix}.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", listing, "-c", "copy", final])

    with open(ROOT / "captions.srt", "w", encoding="utf-8") as f:
        for i, (a, b, text) in enumerate(srt, start=1):
            f.write(f"{i}\n{stamp(a)} --> {stamp(b)}\n{text}\n\n")
    with open(ROOT / "chapters.txt", "w", encoding="utf-8") as f:
        for start, title in chapters:
            m, s = divmod(int(start), 60)
            f.write(f"{m}:{s:02d} {title}\n")

    write_metadata(data)
    print(f"\nDone: {final}  ({t:.0f}s)\nCaptions: captions.srt\nChapters: chapters.txt\nUpload details: metadata.txt")


if __name__ == "__main__":
    main()
