# Engineering Journal: AI Smart Recycling Bin (GreenGuard)

**Author:** Kevin Wei

> Written on the day of the work.

---

## Day 11: Tuesday, November 24, 2026
### What my bin's own records revealed, and what they couldn't tell me

### Goal for today
Find out what my Raspberry Pi could prove about the past two months: when the bin was running, what it sorted, and whether I changed any code after the UN General Assembly Week demo. I also wanted to find the exact date of the demo, which I had forgotten.

### What I did
I connected to the Pi over SSH from my laptop and ran one combined command that collected six kinds of records into a single file, `~/journal_evidence.txt`, so I'd have a permanent copy:

1. **Boot history** (`journalctl --list-boots`): every time the Pi was turned on.
2. **Login history** (`last -F`): who logged in, and when.
3. **Reboots and shutdowns** (`last -x reboot shutdown`).
4. **The bin's own log** (`~/smartbin.log`): what the sorting program printed.
5. **Every file I changed between Sep 22 and Nov 13** (`find ~ -newermt 2026-09-22 ! -newermt 2026-11-14`), skipping hidden folders and Python environments.
6. **My last 100 terminal commands** (`~/.bash_history`).

### Finding 1: The bin has been running for almost 10 days without crashing
The boot history showed only **one boot**:

```
IDX BOOT ID                          FIRST ENTRY                 LAST ENTRY
  0 ab71a82ac2b54215b60fa94a43bb87ea Sat 2026-11-14 18:58:37 PST Tue 2026-11-24 11:35:17 PST
```

The Pi was turned on at **6:58 PM on November 14**, right after I backed up my code to GitHub, and it had been on ever since: **9 days, 16 hours and 37 minutes**. The bin's log file was last written at **11:35 AM today**, the same minute as the last system entry. So the sorting program started automatically when the Pi booted, and has run the entire time without stopping. That's the first real **reliability** number I have for GreenGuard.

### Finding 2: I didn't change any code after September 21
The search for files changed between September 22 and November 13 came back **completely empty**. My command history matches: the last commands from September were writing the final version of `servo_sorter.py` and running the bin. The very next commands are from November 14, when I backed everything up.

**This proves the bin I demoed at UNGA81 on September 22–23 ran exactly the code I finished on September 21**, the night before I left for New York. I didn't touch the code during the conference or for seven weeks after.

### Finding 3: Real sorting results, and a real weakness
The end of the log showed three real sorts:

```
Detected: glass (37.9%) -> Trash (low-confidence -> Trash)
Detected: cardboard (60.9%) -> Recycle
Detected: paper (53.1%) -> Recycle
```

| AI's guess | Confidence | Bin | What happened |
|---|---|---|---|
| glass | 37.9% | Trash | Below my 40% cutoff, so it went to the safe default (Trash) |
| cardboard | 60.9% | Recycle | Normal sort |
| paper | 53.1% | Recycle | Normal sort |

**What I noticed:**
- **Glass missed my cutoff by only 2.1 points.** If the AI was right that it was glass, a recyclable item went to the trash. I set "unsure → Trash" on purpose, because one wrong item can contaminate a whole recycling batch, but this is the cost of that choice.
- **None of the three guesses were very confident** (38–61%). My mentor's model scored 82.6% accuracy on TrashNet test photos, but TrashNet photos are single items on a plain background with even lighting. My tray has a different background, different lighting, and glare. The AI is seeing pictures that don't look like the ones it learned from, which is called a **domain shift**.
- **Glass is the hardest material for a camera.** It's see-through, so it takes on the color of whatever is behind it, and it reflects light. That explains why it had the lowest confidence.

**What the log doesn't tell me:** what each item **actually** was. The log records the AI's guess, but not the truth, so I can't calculate a real accuracy percentage from it.

### Finding 4: My item detection ignores noise very well
Most of the log is debug lines like this:

```
[debug] present=False area=50 motion=False already_sorted=False
```

`area` is the size (in pixels) of the biggest changed spot the camera sees. With the tray empty, it stayed between **0 and 50 pixels**. My code only counts something as an item at **6,000 pixels** (`MIN_BOX_AREA`), so there was a **120× safety margin**. Shadows, camera noise and small lighting changes never came close to triggering a false sort. The detection I rebuilt on September 19 is working the way I designed it.

### Finding 5: Most of the history is gone, and why
Three things meant I couldn't find older records, including the UNGA demo date:

1. **The system log only lives in memory.** My Pi wasn't set up to save system logs to the SD card, so every time it powered off, the history was erased. The only boot it remembers is the current one.
2. **The `last` command isn't installed** on my Pi's version of the operating system, so login history wasn't available that way.
3. **My own start script erases the bin's log every time.** In `start_with_display.sh`, the line `python -m src.smart_bin > ~/smartbin.log` uses `>`, which **replaces** the file instead of adding to it. Every restart wiped the record of everything sorted before.

On top of that, **the log has no timestamps**, so even the three sorts above could have happened any time in the last ten days.

I found the demo date in my registration emails and itinerary instead: **September 22–23, 2026**. The "The Nest Campus" visitor badge in my photo of the bin is from the Nest Climate Campus at the Javits Center on September 23.

### What I learned
1. **Records have to be designed in.** I built a machine that makes decisions all day, but I never designed a way to keep the history of those decisions.
2. **One character can erase data.** `>` vs `>>` decided whether my sorting history survived a restart.
3. **Confidence isn't accuracy.** The AI's percentage is how sure it feels, not whether it's right. To measure accuracy, I have to record the truth too.
4. **Lab results don't transfer automatically.** 82.6% on clean dataset photos doesn't mean 82.6% on my tray.

### Next steps
- [ ] **Keep system logs across restarts:** `sudo mkdir -p /var/log/journal && sudo systemctl restart systemd-journald`
- [ ] **Stop erasing the bin's log:** change `>` to `>>` in `start_with_display.sh`
- [ ] **Add a timestamp to every log line**, e.g. `2026-11-24 11:35 Detected: paper (53.1%) -> Recycle`
- [ ] **Save the cropped photo of every item** the AI classifies, with its guess and confidence. That builds my **own dataset** for retraining the model on what my camera actually sees.
- [ ] **Run a 50-item test** where I write down what each item really is, to get a true accuracy number and a list of the items it gets wrong.

### Evidence
- `~/journal_evidence.txt` on my Pi (full output of today's command)
- Boot record: single boot, Nov 14 18:58:37 PST → Nov 24 11:35:17 PST
- `~/smartbin.log`: 5,463 bytes, last modified 2026-11-24 11:35
- Empty result for files changed Sep 22 – Nov 13
