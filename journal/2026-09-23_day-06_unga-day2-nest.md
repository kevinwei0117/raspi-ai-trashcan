# Engineering Journal: AI Smart Recycling Bin (GreenGuard)

**Author:** Kevin Wei

> Written up in November 2026 from my registration records, itinerary, my Nest Climate Campus
> visitor badge, and the bin's code history. Parts marked **(to confirm)** still need my own
> memory or photos before this entry is final.

---

## Day 6: Wednesday, September 23, 2026
### UN General Assembly Week, Day 2: demoing GreenGuard at the Nest Climate Campus

### Short version (for the journal)
> **What I did:** Showed **GreenGuard**, my AI recycling bin, at the **Nest Climate Campus** (Javits Center North, NYC Climate Week). The bin ran on the code I finished two nights before. I also went to sessions from UChicago and Dartmouth/SAP on climate, AI and energy.
>
> **How it went:** *(to fill in: how many people saw it, what they said, anything that went wrong)*
>
> **What I learned:** *(to fill in)*
>
> **Next:** Use the feedback to design version 2.

### Schedule (from my registrations)

| Time (ET) | Event | Where | Status |
|---|---|---|---|
| 9:00 AM–6:00 PM | **The Nest Climate Campus** (multi-company and university climate campus) | Javits Center North, 445 11th Ave | Registered. **I still have the visitor badge.** |
| 10:30 AM (optional) | Yale: *Cities as Climate Catalysts: Science-Driven Solutions for People and Nature* | NY Botanical Garden | Registered |
| 1:00–2:00 PM | UChicago: *A Postcard from the Future: The Heat Toll of the 2026–27 Super El Niño and What We Can Still Do* | Glasshouse on Bryant Park, 9th Floor | Registered |
| 2:30–7:00 PM | Dartmouth & SAP: *The Security Imperative: Data, AI, Critical Minerals, and Energy Systems* | SAP Experience Center, 10 Hudson Yards, 52nd Floor | Registered |
| ~6:00 PM | Departure (itinerary) | | *(to confirm: overlaps the Dartmouth/SAP event)* |

### The bin I demoed
- **Exactly the Sep 21 code.** On my Pi, no project files were modified between Sep 22 and Nov 13, so nothing changed during the conference.
- Hardware: 8-gallon can, Ender 3 aluminum frame, Raspberry Pi 4 + Pi Camera, PCA9685 + 2 servos, my 3D-printed tray (SERVO plate 3.0), battery box, screen, and shutdown button.
- How it works: camera sees an item → AI (MobileNetV2 trained on TrashNet) guesses the material → Recycle or Trash → rotate + tilt to 120° to drop it.

### To confirm / fill in
- [ ] About how many people saw GreenGuard or tried the 60-second challenge, and from how many countries
- [ ] Feedback people gave ("What would you change?", ratings)
- [ ] Anything that went wrong during the demo, and how I handled it
- [ ] A moment, question or person that stuck with me
- [ ] Photos of GreenGuard at the Nest (with dates)

### Evidence
- Nest Climate Campus visitor badge (visible in my photo of the bin from Nov 14)
- Registration emails
- Pi file history: no code changes Sep 22 – Nov 13
- Photos (to add)
