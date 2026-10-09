# Concept in Motion pipeline (v2)

Build:   python build.py scenes.json --preview --voice en_US-lessac-medium
Final:   python build.py scenes.json --voice en_US-lessac-medium
One scene only: add --only 4
Slower narration: add --speed 0.85 --sentence-pause 0.5 --scene-pause 0.8  (speed 1.0 = normal, works for Piper and for recorded audio)        Visual arrives earlier/later: add --lead 0.8 (default 0.5)

## Visual types (the "visual" field in scenes.json)
- title        title, subtitle
- bullets      title, items[]            cues: list of phrases, one per bullet
- flow         mode request | response   cues: app, server, api, request, check, forward  (request)
                                               work, response, json, arrive               (response)
- restaurant   mode intro | mapping      cues: customer, kitchen, waiter, order, meal     (intro)
                                               api, software, hide                        (mapping)
- code         title, code, output       cues: output
- tokens       title, sentence, tokens[], ids[], note      cues: split, ids
- wordmap      title, clusters[] (optional), note          cues: map, c0, c1, c2, note
- pipeline     title, stages[] (label, color)              cues: s0, s1, s2 ... (one per stage)

## Cues = syncing visuals to the voice
"cues" lists phrases copied EXACTLY from that scene's narration. The visual appears
about half a second BEFORE the voice says the phrase ("show, then say").
Timing is estimated from the position of the phrase in the text, so it is close, not frame-exact.
If a phrase is not found, build.py stops and tells you which one.

## Upload details
A full build also writes metadata.txt (title, description with chapters, tags, playlist, checklist).
Edit the "youtube" section at the bottom of scenes.json to change them.
python build.py scenes.json --metadata-only   rewrites metadata.txt from the existing chapters.txt (instant)

## Video files
scenes.json = Video 1 (API).  scenes_nlp.json = Video 2 (NLP).  Build one with: python build.py scenes_nlp.json --voice en_US-lessac-medium
A build overwrites final.mp4, captions.srt, chapters.txt, metadata.txt in this folder, so copy them to the video's Final folder right after each build.
