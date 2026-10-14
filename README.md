# CONCEPT in MOTION

YouTube channel **@ConceptInMotion**: tech concepts explained with animated, narrated videos.
This folder is the whole channel: branding, the video-making pipeline, scripts, and notes.

**Promise:** any tech concept, understood in under 8 minutes, with visuals that make it click.

## How a video is made (one line)
`script  ->  scenes json  ->  python build.py  ->  final.mp4 + captions + chapters + upload text  ->  YouTube Studio`

## Folder map
| Folder | What is in it |
|---|---|
| `01_Branding` | logo, banner, watermarks, thumbnails (all regenerable from code) |
| `02_Pipeline` | `build.py`, `scenes.py`, one `scenes_*.json` per video, `tools/` (thumbnail and brand makers) |
| `03_Videos` | one folder per video: `Final` (upload files) and `Source` (script json) |
| `04_Shorts` | vertical clips |
| `05_Music-and-Assets` | licensed music/images (keep license notes) |
| `06_Planning` | `video-tracker.csv`, `RESTART-PROMPT.txt` (paste into a new AI chat) |
| `07_Analytics-and-Notes` | what worked, retention notes |
| `08_Backups` | copies kept outside Git |
| `docs` | procedure, setup and recovery, GitHub, troubleshooting |

## Start here
- Making a new video: `docs/PROCEDURE.md`
- New computer, or lost something: `docs/SETUP-AND-RECOVERY.md`
- Saving to GitHub: `docs/GITHUB.md`
- Something broke: `docs/TROUBLESHOOTING.md`
- Continuing with an AI assistant in a new chat: `06_Planning/RESTART-PROMPT.txt`

## Videos
| # | Title | Scenes file |
|---|---|---|
| V01 | What Is an API? Explained with a Restaurant | `02_Pipeline/scenes.json` |
| V02 | What Is Natural Language Processing (NLP)? Explained Simply | `02_Pipeline/scenes_nlp.json` |
| V03 | What Is an AI Agent? How AI Agents Work | `02_Pipeline/scenes_agent.json` |
| V05 | How Do LLMs Predict the Next Word? | `02_Pipeline/scenes_llm.json` |
| V06 | How Does a Neural Network Learn? | `02_Pipeline/scenes_nn.json` |

## Brand rules
Blue = data/API, orange = user/packet, green = server, dark navy background, Poppins font, "CM" monogram.
Show, then say: visuals appear just before the narration names them. One concept per video.
Fact-check every claim. Check licenses for voices, music, fonts and models before monetizing.
