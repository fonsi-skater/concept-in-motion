# PROCEDURE: making a video, start to finish (Windows + PowerShell)

Every command assumes this first line was run in the PowerShell window:

```powershell
$root = [Environment]::GetFolderPath("Desktop") + "\CONCEPTinMOTION"
```
(If your Desktop is not where you expect, that line still finds it, even inside OneDrive.)

## The loop for each new video (V03, V04, ...)

### 1. Pick the concept
- One concept per video. Prefer "what is X" and "how does X work" topics people search for.
- Add a row to `06_Planning\video-tracker.csv` (status: Scripting).

### 2. Write the script (about 500 to 700 words, 3 to 5 minutes)
Structure: **Hook** (a question, under 20 seconds) -> **Analogy** (everyday comparison) -> **Visual walkthrough** (steps)
-> **Example or demo** -> **Recap in 3 points** -> **Teaser for the next video**.
Rules: short sentences; no brackets or stage directions in narration (the voice reads everything);
write numbers and symbols the way you want them spoken; fact-check every claim against official sources.

### 3. Turn the script into a scenes file
Copy `02_Pipeline\scenes_nlp.json` to `scenes_<topic>.json` and edit it. Each scene:

```json
{
  "chapter": "Step 1: Tokens",
  "narration": "Exactly what the voice says...",
  "visual": {"type": "tokens", "...": "settings for that type"},
  "cues": {"split": "exact phrase from the narration"}
}
```
**Visual types** (all in `scenes.py`):

| type | settings | cue names |
|---|---|---|
| `title` | title, subtitle | none |
| `bullets` | title, items[] | a list: one phrase per bullet |
| `flow` | mode (request or response), title, request, response, thinking, json[], nodes[] | request mode: app, server, api, request, check, forward. response mode: work, response, json, arrive |
| `restaurant` | mode (intro or mapping), title | intro: customer, kitchen, waiter, order, meal. mapping: api, software, hide |
| `code` | title, code, output | output |
| `tokens` | title, sentence, tokens[], ids[], note | split, ids |
| `wordmap` | title, clusters[] (optional), note | map, c0, c1, c2, note |
| `pipeline` | title, stages[] (label, color) | s0, s1, s2, ... |
| `hub` | title, center, center_color, items[] (label, sub, color), up to 4 | center, n0, n1, n2, n3 (order: left, right, bottom, top) |
| `agentloop` | title; optional goal, done_text, log[] (stage think/act/observe, text) | no log: think, act, observe, repeat, done. With log: l0, l1, l2, ... and done |
| `probbars` | title, prompt, bars[] (word, p), more, note; mode build (default) or pick with pick, temp | build: prompt, b0, b1, ..., note. pick: pick, temp |
| `genloop` | title, prompt, words[], label | label, w0, w1, ... |
| `neuralnet` | title, layers[], input_label, outputs[], guess[], after[], error_text, pre[] (nodes, weights, lit, guess, error) | input, hidden, output, weights, signal, answer, error, adjust, done |
| `descent` | title | valley, ball, steps, label, name, rate |
| `losscurve` | title | axes, curve, test |

**Cues** = phrases copied EXACTLY (letter for letter) from that scene's narration. The visual appears about half a second before the voice says it. If a scene lists cues, only the cued events run, so a template can offer more events than a scene uses; with no cues at all, events are spread evenly.
**Chapters**: put `chapter` on scenes where a new section starts. YouTube needs the first at 0:00, at least 3 chapters, each at least 10 seconds.
**Need a visual that does not exist?** Ask your AI assistant to add a template (see the header of `scenes.py`), or draw it as a simple `title`/`bullets` scene.
**Upload text**: edit the `"youtube"` block at the bottom (title, summary, tags, hashtags, playlist, next_video).

### 4. Create the video folder
```powershell
mkdir "$root\03_Videos\V03_Your-Topic\Final" -Force
mkdir "$root\03_Videos\V03_Your-Topic\Source" -Force
```

### 5. Build a fast preview (low resolution)
```powershell
cd "$root\02_Pipeline"
del audio\scene_*.wav -ErrorAction SilentlyContinue      # important: clears the previous video's audio
python build.py scenes_yourtopic.json --preview --voice en_US-lessac-medium --speed 0.85 --sentence-pause 0.5 --scene-pause 0.8
start final_preview.mp4
```
Review: Do visuals appear just before the words? Any text overlapping or off screen? Every fact right? Bottom-right corner clear?
Fixes: `--lead 0.8` (visuals earlier) or `--lead 0.2` (later); `--only 4` rebuilds one scene; edit the json and rebuild.
Your own voice: record each scene in Audacity, export WAV as `audio\scene_01.wav`, `scene_02.wav`, ... (a recording beats Piper for that scene).

### 6. Build the final video (1080p, takes about 10 to 30 minutes)
```powershell
python build.py scenes_yourtopic.json --voice en_US-lessac-medium --speed 0.85 --sentence-pause 0.5 --scene-pause 0.8
start final.mp4
```

### 7. Copy the results out immediately (the next build overwrites them)
```powershell
$v = "$root\03_Videos\V03_Your-Topic"
copy final.mp4, captions.srt, chapters.txt, metadata.txt "$v\Final\"
copy scenes_yourtopic.json "$v\Source\"
```
Optional music: save a licensed track as `music.mp3`, then
```powershell
ffmpeg -i final.mp4 -stream_loop -1 -i music.mp3 -filter_complex "[1:a]volume=0.08[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac final_music.mp4
```

### 8. Make the thumbnail
```powershell
cd "$root\02_Pipeline\tools"
python thumbnail.py "WHAT IS" "TOPIC?" "Short subtitle" "Box one" "Box two" "Box three" --out "$root\01_Branding\Thumbnails\thumbnail-video3-topic-1280x720.png"
copy "$root\01_Branding\Thumbnails\thumbnail-video3-topic-1280x720.png" "$v\Final\"
```
3 to 5 big words, high contrast, bottom-right corner empty. If the PNG step fails (Cairo missing), open the `.svg` it saved in Chrome or Inkscape and export 1280x720.

### 9. Upload to YouTube Studio (manually, as a private draft)
Open `metadata.txt` and copy from it.
1. studio.youtube.com -> Create -> Upload videos -> `final.mp4`.
2. Paste title and description (chapters are already inside it). Upload the thumbnail.
3. Playlist as listed; audience "No, it's not made for kids"; Show more: tags, language English, category Education.
4. Altered or synthetic content question: answer honestly using YouTube's current definition.
5. Subtitles -> Add language -> English -> Upload file -> With timing -> `captions.srt`.
6. Wait for checks. Visibility: **Private**. Save. Watch the processed video fully, check chapters and captions.
7. Then set **Public** (or Schedule).
Why manual: the YouTube API locks uploads from new, unaudited projects to private, and the details above are worth a human check.

### 10. After publishing
- Update `video-tracker.csv` (status, date, link).
- Cut 2 Shorts (vertical 9:16, large captions) into `04_Shorts`.
- Reply to comments; after 48 hours read Analytics (click-through rate, retention) and note findings in `07_Analytics-and-Notes`.
- Save to GitHub: see `docs/GITHUB.md`.

## Facts and decisions log (so you do not have to rediscover them)
- Pipeline tested with Manim 0.22.0, FFmpeg, Python 3.12 (build machine) and Piper voice `en_US-lessac-medium`.
- Piper speed: `--length-scale` is the inverse of speed (speed 0.85 = length-scale 1.176). Pauses: `--sentence-silence`.
- `final.mp4`, `captions.srt`, `chapters.txt`, `metadata.txt` are overwritten by every build: copy them out each time.
- Captions are generated from the script text (not speech recognition), so they match your narration exactly. If you record your own voice they are timed by the estimated reading speed of each scene, so check them in YouTube's subtitle editor.
- Cue timing is estimated from the position of each phrase in the text, so it is close, not frame-exact.
- YouTube Partner Program: thresholds change. Check the Earn tab in YouTube Studio. Create AdSense from YouTube Studio when eligible.
- The watermark appears bottom-right on long videos only; keep that corner clear in animations.
- Check licenses of voices, fonts, music and any AI models before monetizing. Review every video yourself; keep your own script and voice or review in each video (YouTube targets mass-produced, repetitive content).
