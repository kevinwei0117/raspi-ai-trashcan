# Engineering Journal: AI Smart Recycling Bin (GreenGuard)

**Author:** Kevin Wei

> Written up from my chat logs of Nov 12–13, 2026.

---

## Day 7: November 12–13, 2026
### Reviewing the project and planning version 2

### Short version (for the journal)
> **What I did:** Collected everything about the project into one summary: my notes from the September chats, the hardware, the code layout, and every bug I'd fixed. Then I built a timeline of what I did and when.
>
> **What I realized:** All my code existed **only on the Raspberry Pi's SD card**. If the card died, the whole project would be gone. Backing it up became the top priority.
>
> **What I learned:** Keeping records as you go matters. It's much harder to reconstruct what you did weeks later.
>
> **Next:** Back up the code to GitHub and start designing version 2.

### What I put together
- **Project summary ("memory file")** combining my September chat notes:
  - Hardware: Raspberry Pi 4 (8 GB), Pi Camera, PCA9685 servo driver at I2C address `0x40`, tilt servo on channel 11, rotate servo on channel 8, shutdown button on GPIO21.
  - Software: `~/raspi-ai-trashcan`, run with `python -m src.smart_bin` in `~/servo-env`.
  - The 7 bugs fixed on Sep 21.
- **Gaps:** I had never looked at `camera.py`, `classifier.py` or `category_map.py` closely, and had no record of the UN demo date.

### Risks I found
1. **No backup:** the code was only on the SD card. SD cards fail, especially when the power is pulled.
2. **Hard to restart:** an auto-started copy of the program could hold the camera (`Device or resource busy`).
3. **Too small for public use:** the 8-gallon can fills fast, and the bag is very hard to take out.

### Evidence
- My chat logs from Nov 12–13, 2026
