#!/usr/bin/env python3
"""Gemini TTS voiceover for the reel (promo/instagram/{zh/}reel.mp4).

Each language's narration is one TTS request (natural prosody across lines),
then split at its pauses and each line placed at the start of its scene, so
the voice stays in step with the animation.

    python3 scripts/voiceover.py                         # zh + en, default voices
    python3 scripts/voiceover.py --lang zh --voices Aoede,Sulafat,Achird
    python3 scripts/voiceover.py --print                 # just show the script
    python3 scripts/voiceover.py --lang en --hook planted --voices Aoede \
        --model gemini-2.5-flash-preview-tts             # alternative opening (reel-planted.mp4)

Outputs, per voice:
    promo/instagram/{zh/}reel-vo-<voice>.mp4   video + voice
    promo/instagram/{zh/}vo-<voice>.wav        voice only (for editing in the app)
With --hook H: reel-H-vo-<voice>.mp4 and vo-H-<voice>.wav, over reel-H.mp4.

Uses GOOGLE_API_KEY — the demo key without billing; the TTS flash models are on
the free tier. Raw TTS responses are cached in data/work/voiceover/, so
re-running only re-mixes (pass --fresh to regenerate).
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_promo import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REEL = {"en": ROOT / "promo" / "instagram" / "reel.mp4",
        "zh": ROOT / "promo" / "instagram" / "zh" / "reel.mp4"}
WORK = ROOT / "data" / "work" / "voiceover"
MODEL = "gemini-3.8-flash-tts"  # each TTS model has its own free-tier quota
RATE = 24000
SECONDS = 18.0
DEFAULT_VOICES = ["Aoede", "Sulafat", "Achird"]

# How the voice should sound. A bare instruction gets read aloud; the
# notes/transcript layout from Google's TTS prompting guide does not.
STYLE = """### DIRECTOR'S NOTES
Style: a relaxed, friendly short-video voiceover, like telling a friend about something you just
discovered — conversational, a little upbeat, a hint of surprise. Pace: slightly fast.
Language: {language}. Leave a clear one-second pause between lines.
Read ONLY the transcript below, nothing else.

### TRANSCRIPT
"""
LANGUAGE = {"zh": "Mandarin Chinese (natural mainland accent)", "en": "American English"}


def pct(city: dict) -> int:
    return round(100 * city["fall"] / city["total"])


# Alternative openings, matching HOOKS in assets/promo/reel.html (?hook=…): {line index: text}.
# {sf}/{cup} are filled from species_stats.json.
HOOKS = {"planted": {"en": {
    0: "Bay Area fall colour isn't random. It was planted — street by street.",
    1: "In San Francisco, {sf}% of street trees turn. In Cupertino, {cup}%.",  # old line 2 leaned on the old hook
}}}


def script(lang: str, hook: str | None = None) -> list[tuple[float, str]]:
    """(scene start in seconds, line) — scene times match assets/promo/reel.html."""
    lines = base_script(lang)
    if hook:
        info = stats()
        numbers = {"sf": pct(info["city"]["sf"]), "cup": pct(info["city"]["cupertino"])}
        for i, text in HOOKS[hook][lang].items():
            lines[i] = (lines[i][0], text.format(**numbers))
    return lines


def base_script(lang: str) -> list[tuple[float, str]]:
    info = stats()
    sf, cup = pct(info["city"]["sf"]), pct(info["city"]["cupertino"])
    if lang == "zh":
        return [
            (0.0, "在湾区住了六七年，才知道树会变色。"),
            (3.4, f"旧金山只有{sf}%的树会变色，库比蒂诺是{cup}%。"),
            (8.0, f"湾区{round(info['bay_trees'] / 1e4)}万棵行道树，全在这张地图上。"),
            (11.5, "点开任意一棵，就知道它是什么树。"),
            (14.9, "找秋色，走过去。不用装App。"),
        ]
    return [
        (0.0, "Six years in the Bay Area, and I never saw the trees turn."),
        (3.4, f"Turns out only {sf}% of San Francisco's trees do. Cupertino? {cup}%."),
        (8.0, f"Here are all {round(info['bay_trees'], -4):,} of them, on one map."),
        (11.5, "Tap any tree to see what it is."),
        (14.9, "Find the colour. Walk to it. No app needed."),
    ]


def api_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise SystemExit("GOOGLE_API_KEY not set")
    return key


def transcribe(wav: Path) -> str:
    """Timestamped transcript of the final track — a check for whoever can't listen."""
    body = json.dumps({"contents": [{"parts": [
        {"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav.read_bytes()).decode()}},
        {"text": "Transcribe this audio verbatim, one line per sentence, each prefixed with its start time "
                 "in seconds. Mention anything that isn't narration."}]}]}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key()}"
    reply = json.load(urllib.request.urlopen(urllib.request.Request(url, body, {"Content-Type": "application/json"})))
    return reply["candidates"][0]["content"]["parts"][0]["text"].strip()


def tts(text: str, voice: str, model: str) -> np.ndarray:
    body = json.dumps({
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}},
    }).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key()}"
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, body, {"Content-Type": "application/json"})
            reply = json.load(urllib.request.urlopen(request, timeout=180))
            break
        except urllib.error.HTTPError as err:
            if err.code not in (429, 500, 503) or attempt == 4:
                raise SystemExit(f"TTS {err.code}: {err.read()[:300]!r}")
            print(f"    {err.code}, waiting {30 * (attempt + 1)} s")
            time.sleep(30 * (attempt + 1))
    part = reply["candidates"][0]["content"]["parts"][0]["inlineData"]
    raw = base64.b64decode(part["data"])
    if raw[:4] == b"RIFF":
        with wave.open(io.BytesIO(raw)) as wav:
            assert wav.getframerate() == RATE and wav.getnchannels() == 1
            raw = wav.readframes(wav.getnframes())
    return np.frombuffer(raw, dtype=np.int16)


def split(audio: np.ndarray, lines: list[str]) -> list[np.ndarray]:
    """Cut between lines, trimming the silence around each one.

    The model's pauses between lines are often no longer than those inside a
    line, so for each boundary we estimate where it should fall (by character
    count) and cut at the pause nearest to that.
    """
    hop = RATE // 50  # 20 ms
    frames = audio[: len(audio) // hop * hop].astype(np.float32).reshape(-1, hop)
    loud = np.sqrt((frames ** 2).mean(axis=1)) > 0.02 * 32768
    voiced = np.flatnonzero(loud)
    gaps = [(a + 1, b) for a, b in zip(voiced[:-1], voiced[1:]) if b - a > 10]  # pauses > 200 ms
    if len(gaps) < len(lines) - 1:
        raise SystemExit(f"found {len(gaps)} pauses, need {len(lines) - 1} — try another voice or --fresh")
    weight = np.cumsum([len(text) for text in lines])
    first, last = voiced[0], voiced[-1] + 1
    cuts = []
    for share in weight[:-1] / weight[-1]:
        expected = first + share * (last - first)
        left = [g for g in gaps if not cuts or g[0] > cuts[-1][0]]
        cuts.append(min(left, key=lambda g: abs((g[0] + g[1]) / 2 - expected)))
    bounds = [first] + [x for s, e in cuts for x in (s, e)] + [last]
    pad = 3  # keep 60 ms either side so consonants aren't clipped
    return [audio[max(0, (s - pad) * hop): (e + pad) * hop] for s, e in zip(bounds[::2], bounds[1::2])]


def tighten(audio: np.ndarray, max_pause: float) -> np.ndarray:
    """Shorten every silence longer than max_pause seconds down to max_pause."""
    hop = RATE // 50
    frames = audio[: len(audio) // hop * hop].astype(np.float32).reshape(-1, hop)
    loud = np.sqrt((frames ** 2).mean(axis=1)) > 0.02 * 32768
    keep, run, limit = [], 0, int(max_pause * 50)
    for i, is_loud in enumerate(loud):
        run = 0 if is_loud else run + 1
        if run <= limit:
            keep.append(audio[i * hop: (i + 1) * hop])
    return np.concatenate(keep)


def speed_up(audio: np.ndarray, tempo: float) -> np.ndarray:
    """Faster speech at the same pitch (ffmpeg atempo)."""
    out = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "s16le", "-ar", str(RATE), "-ac", "1", "-i", "-",
         "-af", f"atempo={tempo}", "-f", "s16le", "-"], input=audio.tobytes(), capture_output=True, check=True)
    return np.frombuffer(out.stdout, dtype=np.int16)


def place(lines: list[tuple[float, str]], clips: list[np.ndarray]) -> tuple[np.ndarray, list[str]]:
    track = np.zeros(int(SECONDS * RATE) + sum(map(len, clips)), dtype=np.int16)
    cursor, report = 0.0, []
    for (start, text), clip in zip(lines, clips):
        at = max(start, cursor + 0.15)
        i = int(at * RATE)
        track[i: i + len(clip)] = clip
        cursor = at + len(clip) / RATE
        report.append(f"{at:5.2f}–{cursor:5.2f} s  (scene {start:4.1f})  {text}")
    return track[: int(max(cursor, SECONDS) * RATE)], report


def write_wav(path: Path, audio: np.ndarray) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(audio.tobytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", choices=["zh", "en", "both"], default="both")
    parser.add_argument("--voices", default=",".join(DEFAULT_VOICES))
    parser.add_argument("--hook", choices=sorted(HOOKS), help="alternative opening line")
    parser.add_argument("--model", default=MODEL, help=f"TTS model (default {MODEL})")
    parser.add_argument("--tempo", type=float, default=1.0, help="speed up the voice, e.g. 1.08 (pitch kept)")
    parser.add_argument("--max-pause", type=float, help="shorten pauses inside a line to this many seconds")
    parser.add_argument("--fresh", action="store_true", help="ignore cached TTS audio")
    parser.add_argument("--print", action="store_true", help="print the script and exit")
    parser.add_argument("--check", action="store_true", help="transcribe each result with Gemini to verify it")
    args = parser.parse_args()

    WORK.mkdir(parents=True, exist_ok=True)
    for lang in (["zh", "en"] if args.lang == "both" else [args.lang]):
        if args.hook and lang not in HOOKS[args.hook]:
            print(f"[{lang}] no '{args.hook}' opening, skipped")
            continue
        lines = script(lang, args.hook)
        reel = REEL[lang].with_stem(f"reel-{args.hook}") if args.hook else REEL[lang]
        tag = f"{args.hook}-" if args.hook else ""
        if args.print:
            print(f"[{lang}]", *(f"  {t:4.1f} s  {text}" for t, text in lines), sep="\n")
            continue
        prompt = STYLE.format(language=LANGUAGE[lang]) + "\n".join(text for _, text in lines)
        for voice in args.voices.split(","):
            # the original cache names predate --hook/--model; keep them valid
            model = "" if args.model == MODEL else f"-{args.model}"
            cache = WORK / f"{lang}-{tag}{voice}{model}.raw"
            if args.fresh or not cache.exists():
                print(f"  {lang}/{voice}: requesting TTS")
                cache.write_bytes(tts(prompt, voice, args.model).tobytes())
                time.sleep(8)  # free tier is a few requests per minute
            audio = np.frombuffer(cache.read_bytes(), dtype=np.int16)
            clips = split(audio, [text for _, text in lines])
            if args.max_pause:
                clips = [tighten(clip, args.max_pause) for clip in clips]
            if args.tempo != 1.0:
                clips = [speed_up(clip, args.tempo) for clip in clips]
            track, report = place(lines, clips)
            folder = reel.parent
            wav = folder / f"vo-{tag}{voice}.wav"
            write_wav(wav, track)
            out = folder / f"{reel.stem}-vo-{voice}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(reel), "-i", str(wav),
                "-filter_complex", "[1:a]loudnorm=I=-16:TP=-1.5,apad[a]", "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-t", str(SECONDS),
                "-movflags", "+faststart", str(out)], check=True)
            print(f"  {lang}/{voice}: {out.relative_to(ROOT)}", *(f"      {r}" for r in report), sep="\n")
            if len(track) > SECONDS * RATE:
                print(f"      ! runs {len(track) / RATE - SECONDS:.1f} s past the end — cut off")
            if args.check:
                print("      transcript:", *("        " + row for row in transcribe(wav).splitlines()), sep="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
