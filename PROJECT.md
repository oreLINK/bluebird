# Bluebird

**Snow odds, time slot by time slot, resort by resort.**

A "bluebird day" is what skiers call the first sunny day after a snowstorm:
deep blue sky, fresh snow everywhere. Bluebird helps you find those days.
Four times a day it tells you, for each ski resort of a mountain range, how
likely it is to snow this morning, at lunchtime, this afternoon, this
evening, tonight and tomorrow, and how likely you are to find fresh powder
on or off the pistes.

It is built for your phone, in French or English.

---

## What you see

At the top, the menu button (on the right) lets you choose the mountain range
(the Pyrenees for now) and your language. Below it, filters narrow the page
to one kind of indicator: **All**, **Snow** or **Powder**. A dark-blue strip
tells you which mountain range the forecast is for and when it was last
updated. Each tile then answers one question for one **time slot** and
presents the resorts like the odds of a match on a betting site.

| Tile | Question | How to read a high percentage |
|---|---|---|
| **Snow** (today, tomorrow, this morning, at lunchtime, this afternoon, this evening, tonight, and the same for tomorrow) | Will at least 1 cm of snow fall during that slot (for the whole day: between 08:00 and 17:00)? | Bring goggles for flat light; fresh snow may build up. |
| **Powder on piste** (this morning, at lunchtime, this afternoon, and tomorrow) | Has at least 5 cm fallen since the grooming machines finished, by the start of the slot (at lift opening for the morning)? | The pistes will be covered with fresh, ungroomed snow. |
| **Off-piste powder** (same slots) | Has at least 15 cm fallen in the 36 hours before the start of the slot near the summit, without strong wind or a thaw spoiling it? | Good chances of light, untracked powder off-piste. Always check the avalanche bulletin first. |

### Time slots

| Slot | Hours (Paris time) |
|---|---|
| This morning | 06:00 – 12:00 |
| At lunchtime | 12:00 – 14:00 |
| This afternoon | 14:00 – 18:00 |
| This evening | 18:00 – midnight |
| Tonight | midnight – 06:00 |
| Today (whole day) | shown from 06:00 to 18:00 |

Tiles are sorted by time: the slots coming soonest first, then tomorrow's.
**A tile disappears as soon as its slot is over**, even if the page stays
open: after noon you no longer see "this morning", after 18:00 you no longer
see "at lunchtime" or "this afternoon", but "this evening", "tonight" and
tomorrow's slots remain. The day switches at 06:00: at 00:30, "tonight" is
still the night that has just started, and "tomorrow morning" is the coming
morning.

Each tile shows:

- a **banner**: a photo of the
  ski area ranked first when one is available, otherwise an illustration (the
  first tile shows it across the whole card);
- the **three most likely resorts** as buttons, each with its percentage and
  a bar below it;
- optionally, betting-style **odds** (1 ÷ probability), if enabled for a tile;
- **See all** to list every other resort, from most to least likely.

Tap a resort to see why: expected snow (median and high scenario), recent
wind and temperature, the time window studied, the resort's elevation, and
how reliable the figure is.

Tap the **?** in the top-right corner of a tile, or anywhere on the tile
outside the resort buttons, to turn it over. The back explains the indicator:
what it measures, the time window studied, how it is computed, how reliable
it is today, when it was last updated and where the data comes from. Tap the
**×** (or the back of the card) to turn it again.

Resorts appear under a short name in the tiles (for example "Cauterets" for
"Cauterets – Cirque du Lys"). All tiles have the same size, so the page stays
tidy; switching filter brings the matching tiles in with a short animation.

If an update is late, the dark-blue strip says so.

### Service status

At the bottom of the page, **Service status** says whether the last update
went well ("All systems running") or how many items are degraded, with the
time of the update. Open it to see, one line each, the state of every data
source, every data processing step, every indicator and every tile:

- **Available**: fresh and complete;
- **Partial**: fresh, but some resorts are missing;
- **Outdated**: the values shown come from an earlier update (for example
  "data from 06:00"), because the latest one could not compute them;
- **Unavailable**: no value.

When an indicator cannot be updated, Bluebird keeps showing its last valid
values for the slots still to come, with a "Data from 06:00" badge on the
tile, rather than an empty page. A slot with no value at all says so on its
tile.

## Where the numbers come from

Bluebird does not invent its own weather forecast. It reads **ensemble
forecasts**: weather centres run their model dozens of times with slightly
different starting conditions to see how uncertain the forecast is.

- 51 scenarios from the European centre (ECMWF) and 40 from the German
  weather service (DWD ICON), via [Open-Meteo](https://open-meteo.com/).
- For each resort, at mid-mountain and near the summit.

A probability is simply **the share of scenarios in which the condition comes
true**. "72 %" means 72 out of 100 scenarios give enough snow.

**Reliability** ("Confidence") reflects how much the scenarios agree: when
almost all agree (very likely or very unlikely), reliability is high; when
they split half and half, it is low. The back of each tile also gives a
**reliability index** for the slot: the average reliability of all resorts
for that indicator (high counts fully, medium half, low not at all).

The high-resolution Météo-France model (AROME) is shown next to it as a
second opinion.

Fixed facts about each resort (position, elevations, grooming and opening
times, pistes and lifts) are stored with the project and refreshed at most
once a season. Only the weather is fetched at each update, with a single
request per weather service for all resorts at once.

### Update schedule

- Every 6 hours: around **00:00, 06:00, 12:00 and 18:00** (Paris time), from
  November to May.
- Updates can arrive a few minutes late.

## Features

### Available now

- Pyrenees: 18 French resorts, from La Pierre Saint-Martin to Formiguères.
- Three probabilities: snow, powder on piste, powder off-piste, for each
  time slot of today and tomorrow (morning, lunchtime, afternoon, evening,
  night, whole day for snow).
- Updated every 6 hours; tiles of slots that are over disappear on their own.
- Service status in the footer, and the last valid values kept (and flagged)
  when an update fails.
- Betting-style tiles: top three resorts as odds buttons, full ranking on
  demand, details on tap, reliability indicator, optional odds.
- Two-sided tiles: the back explains the indicator and the reliability for its slot.
- Filters by kind of indicator (All, Snow, Powder), remembered on your device.
- Menu with the mountain range and language (French or English), remembered
  on your device.
- Clean dark-blue, light-blue and white design with a sporty typeface, in
  light and dark mode following your phone's setting, without background
  animation.
- Banner photos of the ski areas, credited to their authors (photos are
  added progressively; an illustration is shown until then).
- Works on any modern phone browser; add it to your home screen for an
  app-like experience.
- Respects "reduce motion" and "reduce transparency" accessibility settings.

### Coming next

- Avalanche risk level from the Météo-France bulletin (BERA), next to each resort.
- Resort opening status (open lifts and pistes).
- Slope orientation and steepness to refine the powder estimate
  (north-facing slopes keep powder longer).
- Weekend and week-long slots, and quick "Today / Tomorrow" filters.
- A 7-day trend tile and a map of the ski areas (piste and lift data from
  OpenStreetMap is already collected and refreshed once a season).
- More mountain ranges: Northern and Southern Alps, Massif Central, Vosges, Jura.
- Checking past forecasts against observed snow to make the percentages more accurate.

## Limits and safety

- **Bluebird is a planning aid, not an avalanche bulletin.** Before any
  off-piste outing, read the official Météo-France avalanche bulletin (BERA),
  carry avalanche safety equipment and know how to use it.
- Forecasts are uncertain, mountain weather even more so. Local effects
  (wind-loaded slopes, sun, sheltered forests) are not captured.
- Resort coordinates and elevations are approximate; grooming and opening
  times are typical values, not each resort's daily schedule.
- Powder on piste assumes grooming ends around 02:00 and lifts open at 09:00
  unless configured otherwise for a resort.

## FAQ

**Why is a resort at 0 % when it's snowing outside?**
The forecast models disagree with reality sometimes, and the tile only counts
snow inside its time window and above its threshold (for example 5 cm since
grooming).

**Why don't the three tiles agree?**
They answer different questions, at different elevations and time windows.
Heavy snow overnight with strong wind can give a high "powder on piste" and
a low "off-piste powder".

**Is the site free?**
Yes. It uses free, openly licensed data (Open-Meteo, CC BY 4.0;
OpenStreetMap, ODbL) for non-commercial use.

**Does it track me?**
No account, no analytics, no cookies. Your language and last mountain range
are stored only in your browser.
