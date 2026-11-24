# Engineering Journal: AI Smart Recycling Bin (GreenGuard)

**Author:** Kevin Wei

> Written up from my Git history and chat logs, Nov 15–23, 2026.

---

## Day 10: November 15–23, 2026
### Documenting the project, finding the real timeline, and choosing a 3D printer

### Short version (for the journal)
> **What I did:** Wrote this journal from real evidence: my Git history, file timestamps on my Pi, my Fusion 360 files, and my UNGA registrations. I found out exactly what I changed compared to my mentor's starting code, and corrected my own timeline. I also researched a better 3D printer for building version 2.
>
> **What I learned:** Evidence beats memory. I had remembered the demo as November and the servo problem as a loose wire; the records showed it was September 22–23, and the real cause was stripped wires touching.
>
> **Next:** Start journaling in real time, on the day I do the work.

### What the evidence showed
- **What I added to my mentor's code:** 13 files, +334 / −120 lines (`git diff fb4751d 7c74974`).
- **The code I demoed at UNGA:** no files changed on the Pi between Sep 22 and Nov 13.
- **The bin is still running:** the log shows real sorts, for example *cardboard 60.9% → Recycle*, *paper 53.1% → Recycle*, and *glass 37.9% → Trash (low confidence)*, a real limitation: glass should be recycled.
- **The Pi only keeps logs since the last boot** and overwrites `smartbin.log` on every start, so I couldn't recover older data. Fix planned: keep logs across reboots and add timestamps.

### 3D printer research (for building v2 parts in PETG/ASA)
Requirements: fully enclosed, quiet, built-in filtering, multi-color with little waste, good size and price.
- Top choice: **Snapmaker U1 + Top Cover** (~$830–1,000): 4 tool heads (about 4 g of waste vs ~85 g on a single-nozzle color changer), under 50 dB, 3-layer filter, 270 mm cube.
- Runner-up: **Bambu Lab X2D** (~$790–900): heated chamber, HEPA, best accuracy, but more waste in multi-color.

### Evidence
- Journal commits on branch `journal/day-01` of `kevinwei0117/raspi-ai-trashcan`
- `~/journal_evidence.txt` on my Pi (boot record, bin log, file history)
