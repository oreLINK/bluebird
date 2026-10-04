# Bluebird

**Snow odds, time slot by time slot, resort by resort.**

A "bluebird day" is what skiers call the first sunny day after a snowstorm:
deep blue sky, fresh snow everywhere. Bluebird helps you find those days.
Four times a day it tells you, for each ski resort of a mountain range, how
likely it is to snow this morning, at lunchtime, this afternoon, this
evening, tonight and tomorrow, and how likely you are to find fresh powder
on or off the pistes.

Once a season is over, a **Rewind** looks back at it: which resort got the
most snow, the longest snowfall, the snowiest slopes and the snowiest
off-piste terrain around them. The first one is **Rewind 25/26**.

It is built for your phone, in French or English.

---

## What you see

At the top, the Bluebird name sits on the left and the menu button on the
right lets you choose your language. Below the name, large buttons let you
choose the mountain range (the Pyrenees for now), and smaller filters narrow
the page to one kind of indicator: **All**, **Snow**, **Powder** or
**Visibility**. Just
above the tiles, a date tells you which day the data are for (the day of
their last update), with the update time on a small line below it. Each
tile then answers one question for one **time slot** (see [Available
indicators](#available-indicators)) and presents the resorts like the odds of
a match on a betting site.

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
  first tile shows it across the whole card). Tiles lower on the page, such as
  **Off-piste powder**, have no banner and are shorter;
- the **three most likely resorts** as buttons, each with its percentage,
  three **reliability dots** (one: low, two: medium, three: high) and a bar
  below it;
- optionally, betting-style **odds** (1 ÷ probability), if enabled for a tile;
- **See all** to list every other resort, from most to least likely, each
  with its reliability dots. While the list is open, a **See less** button
  also appears above it, so you can close it without scrolling down.

For now, the tiles show the probability only: tapping a resort does
nothing. (A detailed view per resort — expected snow, recent wind and
temperature, time window, elevation — exists and may come back later.)

Tap the **?** in the top-right corner of a tile, or anywhere on the tile
outside the resort buttons, to turn it over. The back explains the indicator:
what it measures, the time window studied, how it is computed, how reliable
it is today, when it was last updated, where the data comes from and who
took the photo. Tap the
**×** (or the back of the card) to turn it again.

Resorts appear under a short name in the tiles (for example "Cauterets" for
"Cauterets – Cirque du Lys"). All tiles have the same size, so the page stays
tidy; switching filter brings the matching tiles in with a short animation.

If an update is late, a line under the date above the tiles says so.

### Service status

At the bottom of the page, the **Service status** link (with a small coloured
dot showing the overall state) opens a full-window page, like the privacy
page. It says whether the last update went well ("All systems running") or
how many items are degraded, with the time of the update, then lists, one
line each, the state of every data source, every data processing step, every
indicator and every tile:

- **Available**: fresh and complete;
- **Partial**: fresh, but some resorts are missing;
- **Outdated**: the values shown come from an earlier update (for example
  "data from 06:00"), because the latest one could not compute them;
- **Unavailable**: no value.

When an indicator cannot be updated, Bluebird keeps showing its last valid
values for the slots still to come, with a "Data from 06:00" badge on the
tile, rather than an empty page. A slot with no value at all says so on its
tile.


### Rewind 25/26

The red **Rewind 25/26** filter, right after **All**, replaces the day's
tiles with a review of the 2025/26 season (1 December 2025 to 1 May 2026, in
the Pyrenees). "All" never shows these tiles: they are only under their red
filter. Rewind tiles look like the day's tiles (photo of the leading resort
or an illustration, podium, full ranking), dressed in Christmas red and white
with a "REWIND 25/26" badge. Their indicators are listed in
[Available indicators](#available-indicators).

The top three resorts are on the podium; **See all** lists the others with
their value. Snow totals are in metres (for example 4.43 m), the longest
snowfall in hours and the ideal snow cover as a share of the season's days
(its bars go from 0 to 100 %; the other bars are relative to the best resort).
The back of each tile explains the measure, the season dates, how it is
computed and the sources. The line above the tiles reads "Season 2025/2026"
instead of the update time.

## Available indicators

### Every 6 hours (live)

Probabilities for each time slot of today and tomorrow (see [Time
slots](#time-slots)), refreshed every 6 hours, with reliability dots.

| Indicator | Filter | Slots | Question | How to read a high percentage |
|---|---|---|---|---|
| **Snow** | Snow | whole day, morning, lunchtime, afternoon, evening, night | Will at least 1 cm of snow fall during the slot (for the whole day: between 08:00 and 17:00), at mid-mountain? | Bring goggles for flat light; fresh snow may build up. |
| **Powder on piste** | Powder | morning, lunchtime, afternoon | Has at least 5 cm fallen since the grooming machines finished, by the start of the slot (at lift opening for the morning)? | The pistes will be covered with fresh, ungroomed snow. |
| **Off-piste powder** | Powder | morning, lunchtime, afternoon | Has at least 15 cm fallen in the 36 hours before the start of the slot near the summit, without strong wind or a thaw spoiling it? | Good chances of light, untracked powder off-piste. Always check the avalanche bulletin first. |
| **White day** | Visibility | today, tomorrow (whole day) | Will the ski day (09:00–17:00) be a white day at mid-mountain? | Expect no relief and poor contrast: stay near trees and markers, take tinted goggles. |

A **white day** ("jour blanc") is a day without visible relief. Hour by hour
over the ski day (09:00–17:00), Bluebird counts an hour as white when the
resort is inside the cloud (humidity of at least 98 % and low cloud of at
least 90 %), when at least 0.5 cm of snow falls per hour, or in flat light
(sunlight below 30 % of what a clear sky would give at that hour). A day with
at least 6 white hours out of 8 is a white day.

### Rewind 25/26 (season review)

Values over the 2025/26 season (1 December 2025 to 1 May 2026, Pyrenees),
computed once from archived forecasts, under the red **Rewind 25/26** filter.

| Indicator | Question | Value |
|---|---|---|
| **Most snow** | Which resort got the most snow over the whole season, at mid-mountain? | metres of snow fallen |
| **Longest snowfall** | Which resort had the longest continuous snowfall? A lull of an hour does not interrupt it. | hours |
| **Most snow on the slopes** | Which ski area got the most snow, on average over points spread along its pistes? | metres of snow fallen |
| **Most off-piste snow** | Which resort got the most snow in the terrain around its ski area? | metres of snow fallen |
| **Ideal snow cover** | On what share of the season's days was the snowpack deeper than 70 cm on average over the slopes? That is the ideal cover, smoothing out the bumps of the terrain, and powder paradise when the snow is fresh. | % of the season's days |
| **Fewest white days** | Which resort had the fewest white days on its slopes over the season (same definition as above, on points along the pistes)? The resort with the fewest comes first. | days |

### Future indicators

Ideas under study, not yet on the site. They are ranked by family; the most
likely next ones are marked ⭐. Each will be checked against the data really
available before it is built.

**Every 6 hours (live)**

| Indicator | Question |
|---|---|
| **Bluebird day** ⭐ | Chance of a "bluebird day": fresh snow (15 cm or more in 36 hours) followed by a clear, sunny ski day. |
| **Lifts stopped by wind** ⭐ | Chance that the top chairlifts close because of strong gusts during the ski day. |
| **Rain at the resort** ⭐ | Chance of rain up to the summit, making a wet day and heavy snow. |
| **Spring snow window** | Hours when the snow softens into "corn" after a night freeze, or a warning of rock-hard snow. |
| **Ice and crust** | Risk of hard, icy snow tomorrow morning after rain or melting followed by a night freeze. |
| **Wind chill** | Felt temperature at the summit in the morning, with a frostbite warning. |
| **UV and sunburn** | Peak UV at altitude, made stronger by the snow's reflection. |
| **Powder alert (3 days)** | Chance of 30 cm or more over the next three days, and the best day to go. |
| **Wind-blown snow** | Fresh snow moved by the wind, a warning sign off-piste (always alongside the avalanche bulletin, never instead of it). |
| **Snow cannons tonight** | Whether the night is cold and dry enough for resorts to make snow (early season). |
| **Road up to the resort** | Chance of snow and ice on the access road between 07:00 and 09:00 (chains or winter tyres). |
| **Expected crowds** | Crowd index from school holidays by zone, weekends and good weather. |
| **Avalanche risk** | Danger level (1 to 5) of the Météo-France avalanche bulletin, and whether it rises tomorrow. |
| **Best time slot** | The best hours of the day per resort, combining visibility, sun and wind. |
| **Ski touring start time** | Best start and return times for a ski tour (night freeze, warming, avalanche risk). |

**Season review (Rewind)**

| Indicator | Question |
|---|---|
| **Sunniest resort** ⭐ | Which resort got the most sunshine over the season (the sunlight is already stored)? |
| **Bluebird days** ⭐ | How many bluebird days each resort had. |
| **Powder days** ⭐ | Days with 20 cm or more of new snow in 24 hours. |
| **Biggest storm** | The largest snowfall over 72 hours, with its dates. |
| **Rain days at the resort** | Days of rain up to the summit in mid-season. |
| **Lifts stopped by wind** | Days when the wind would have closed the top lifts. |
| **Natural snow season** | First and last day with at least 30 cm of snow on the ground, and the number of days in between. |
| **Peak snowpack** | The deepest snow on the ground and its date. |
| **Coldest morning and freeze-thaw days** | The season's coldest morning and the number of spring-snow days. |
| **Holiday luck** | Which school-holiday zone (A, B or C) had the best conditions. |
| **Weekend index** | Share of weekends with good conditions: what most skiers actually live. |
| **Snow cannon nights** | Nights cold and dry enough to make snow. |
| **Slopes vs off-piste gap** | Resorts where the terrain around the slopes got much more snow than the slopes. |
| **High avalanche risk days** | Days with an avalanche danger level of 4 or 5. |

**All time (since the data exist)**

Built on weather reanalyses going back to 1950 (and checked against
Météo-France snow observations). Their grid is coarser than the daily model:
they compare resorts and decades, they are not measurements.

| Indicator | Question |
|---|---|
| **This season in history** ⭐ | Where the current season ranks since 1950 ("the 12th snowiest"), updated every day. |
| **Climate trend** ⭐ | How the number of snow days changes per decade at each resort. |
| **Snow reliability** | Share of seasons with at least 100 days of enough snow: useful to choose a season pass. |
| **When to go?** | For each week of the season, the historical chance of good conditions at each resort. |
| **Snow at Christmas** | Historical chance of at least 30 cm of snow on the ground on 25 December. |
| **Records** | Biggest 24-hour snowfall, biggest storm, coldest season since 1950. |
| **Later openings** | Average date of the first good snow cover, decade by decade. |
| **Rising rain-snow line** | Average winter altitude of the 0 °C level, decade by decade. |
| **Longest bluebird streak** | The record number of sunny days in a row. |
| **Our success rate** | How well Bluebird's past probabilities matched the snow that fell ("when we say 70 %, it snows 68 % of the time"). |

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

**Rewinds** use a different source: the archived hour-by-hour forecasts of
Météo-France's high-resolution model (AROME, 1.5 km grid), via Open-Meteo,
once the season is over. For each resort Bluebird takes the resort point at
mid-mountain, points spread along its pistes (from OpenStreetMap) and points
in a circle around its ski area. The season's hourly data is stored with the
project once and for all, so the rankings never change and new season
indicators can be added later without fetching it again. The snow depth on
the ground comes from the German weather service's ICON model (Météo-France's
archive does not include it), on a coarser grid of about 7 km.

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
- A service status page (linked from the footer), and the last valid values kept (and flagged)
  when an update fails.
- Betting-style tiles: top three resorts as odds buttons with their
  reliability dots, full ranking on demand, optional odds.
  Compact tiles without a picture for the indicators lower on the page.
- Two-sided tiles: the back explains the indicator and the reliability for its slot.
- Filters by kind of indicator (All, Snow, Powder, Visibility), remembered on
  your device.
- White day chances for today and tomorrow, under the **Visibility** filter.
- **Rewind 25/26**: the review of the 2025/26 season in the Pyrenees (most
  snow, longest snowfall, most snow on the slopes, most off-piste snow, ideal
  snow cover days, fewest white days), behind its own red filter.
- Mountain range buttons above the filters, and a menu with the language
  (French or English), both remembered on your device.
- Clean dark-blue, light-blue and white design with a sporty typeface, in
  light and dark mode following your phone's setting, without background
  animation.
- Banner photos of the ski areas (photos are added progressively; an
  illustration is shown until then). Each photo is credited on the back of
  its tile and in the legal notice.
- A short footer: the GitHub logo (link to the project's source code) and
  small links to **About**, **Legal notice** and **Privacy**. Each opens as
  a full-screen page over a blurred background, sliding up from the bottom;
  close it with the **×**, the Escape key or your phone's back gesture.
- Works on any modern phone browser; add it to your home screen for an
  app-like experience.
- Respects "reduce motion" and "reduce transparency" accessibility settings.

### Coming next

- New indicators: see [Future indicators](#future-indicators).
- A Rewind for each new season, from the 2026/27 season on.
- Webcams of the resorts, a comparator of two resorts, a "near me" sort by
  conditions and travel time, a season calendar for the Rewind, and tiles
  ordered by relevance and reliability of the day.
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
- White days are estimated from humidity, cloud, snowfall and sunlight: the
  models do not forecast visibility. A local fog patch or a sea of clouds
  below the resort may be missed.
- Rewind figures come from a weather model's archived forecasts, not from
  snow measurements at the resorts. They compare resorts fairly with each
  other but are not official snowfall records. Resorts that share pistes in
  the map data (Peyragudes/Val Louron, Font-Romeu/Les Angles) get similar
  slope values.
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
No account, no analytics, no cookies. Your language, last mountain range
and filter are stored only in your browser. See the **Privacy** page (link
at the bottom of the site).
