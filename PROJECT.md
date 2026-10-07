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
the page step by step (see [Filters](#filters)). Just
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

### Filters

The filters work like those of a music app on the phone, one level at a time:

1. **Home page** (no filter chosen): a quick overview, always led by the
   **bluebird day** of today, then snow today, on-piste powder this morning
   and white day today (each switches to tomorrow once today's slot is
   over). The filter row shows
   **Rewind 25/26** and the six categories **Snow**, **Snow quality**,
   **Sky**, **Comfort**, **Getting there** and **Safety** (see
   [Categories](#categories)).
2. Tap a filter, for example **Snow**: its button fills in, moves to the
   left with a small **×**, the other filters of that row disappear, and the
   page shows every snow tile. Next to it appear **Today** and **Tomorrow**.
3. Tap **Today**: it joins the row the same way, and the time slots still to
   come appear: **Morning**, **Lunchtime**, **Afternoon**, **Evening**,
   **Night** (only those with tiles left; whole-day tiles are not under a
   slot).
4. Tap a slot to keep only its tiles.

Tap a chosen filter (the one with the **×**) to remove it and the ones after
it. **Safety** stops at Today/Tomorrow (wind-blown snow is computed for the
whole day), and **Rewind 25/26** has no further level. Whole-day tiles (white
day, bluebird day, sunset, mild day, chains…) appear under Today or Tomorrow,
not under a time slot. The first-level filter
you chose is remembered on your device.

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

The red **Rewind 25/26** filter, the first of the filter row, replaces the
day's tiles with a review of the 2025/26 season (1 December 2025 to 1 May
2026, in the Pyrenees). The home page never shows these tiles: they are only
under their red filter. Rewind tiles look like the day's tiles (photo of the leading resort
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

### Categories

Every indicator, available or planned, belongs to one category that answers a
simple question, whatever your level or activity:

| Category | The question it answers |
|---|---|
| ❄️ **Snow** | Will it snow, how much, and is there enough snow on the ground? |
| 🎿 **Snow quality** | What will the snow be like under your skis or snowshoes: powder, spring snow, ice? |
| ☀️ **Sky** | What will you see: sun, cloud, a white day, a sunset? |
| 🧣 **Comfort** | How will it feel: cold, wind, strong sun, a mild day? |
| 🚗 **Getting there** | Can you drive up, will the lifts run, will it be crowded? |
| ⚠️ **Safety** | Which mountain hazards to watch? (Always read the official avalanche bulletin too.) |

They are the filters of the site (in French **Neige**, **Glisse**,
**Ciel**, **Confort**, **Accès**, **Sécurité**). They replaced the first topics (Snow,
Powder, Visibility): powder is one kind of snow quality, and a white day is
about light and sky. The season reviews (Rewinds) keep their own filter.

### Every 6 hours (live)

Probabilities for each time slot of today and tomorrow (see [Time
slots](#time-slots)), refreshed every 6 hours, with reliability dots.

Indicators are grouped by **category**, which is also their filter on the
site (see [Categories](#categories)). Each one is shown in the most telling
way:

- **an amount** (centimetres, hours, °C, km/h) when the quantity itself
  speaks: it is the **median** of the 91 scenarios (half give more, half
  less), and the dots say how close the scenarios are. Some come with a word
  that places the value on a scale (the official wind chill risk, light /
  strong wind…);
- **Yes / Possible / No** when you have a decision to take: Yes from a 60 %
  chance, Possible from 25 %;
- **a percentage** for uncertain events or combinations of conditions: the
  share of the 91 scenarios in which it happens.

The word or time next to a value (risk, sunset time) shows in the full list
of resorts ("See all").

| Category | Indicator | Shown as | Slots | Question | How to read it |
|---|---|---|---|---|---|
| ❄️ Snow | **Snow** | cm of snow (median) | whole day, morning, lunchtime, afternoon, evening, night | How much snow will fall during the slot (for the whole day: between 08:00 and 17:00), at mid-mountain? | Bring goggles for flat light; fresh snow may build up. |
| ❄️ Snow | **Snow alert** | cm in 36 h (median), with light / good / alert | today, tomorrow (whole day) | How much snow will fall at mid-mountain within 36 hours from 06:00? "Alert" from 30 cm. | A big dump is coming: plan a powder day, and check the roads. |
| ❄️ Snow | **Snow cannons** | hours of snowmaking weather (median) | tonight, tomorrow night | How many hours of the night (20:00–06:00) will be cold and dry enough to make snow at mid-mountain (wet-bulb temperature of −2.5 °C or less)? A useful night has 6 or more. | The resort can make snow overnight: better-covered pistes in the morning, especially early season. |
| 🎿 Snow quality | **Powder on piste** | cm since grooming (median) | morning, lunchtime, afternoon | How much snow will have fallen on the pistes since the grooming machines finished, by the start of the slot (at lift opening for the morning)? Powder from 5 cm. | The pistes will be covered with fresh, ungroomed snow. |
| 🎿 Snow quality | **Off-piste powder** | % | morning, lunchtime, afternoon | Has at least 15 cm fallen in the 36 hours before the start of the slot near the summit, without strong wind or a thaw spoiling it? | Good chances of light, untracked powder off-piste. Always check the avalanche bulletin first. |
| 🎿 Snow quality | **Spring snow** | % | morning, lunchtime, afternoon | After a night freeze (−1 °C or less between 00:00 and 08:00), does the snow soften during the slot (+1 °C or more), without 5 cm of fresh snow on top? | Smooth "corn" snow: the best time to ski in spring. |
| 🎿 Snow quality | **Hard snow** | Yes / Possible / No | morning | After a thaw the day before (+2 °C or more) and a night freeze (−2 °C or less), does the snow stay frozen during the slot (0 °C or less), without fresh snow on top? | Hard, icy pistes: sharp edges, and wait for the sun to soften them. |
| 🎿 Snow quality | **Heavy snow** | % | lunchtime, afternoon | Will the slot be warm (+4 °C or more) or bring wet snow (1 cm or more at +0.5 °C or more)? | Heavy, sticky snow: tiring legs, ski earlier in the day. |
| 🎿 Snow quality | **Easy conditions** | % | morning, lunchtime, afternoon | Will the slot stay calm (wind under 25 km/h), not too cold (above −10 °C), visible (at most a quarter of white hours) and without a snowstorm (under 2 cm)? | A good time for beginners and children. |
| ☀️ Sky | **White day** | % | today, tomorrow (whole day) | Will the ski day (09:00–17:00) be a white day at mid-mountain? | Expect no relief and poor contrast: stay near trees and markers, take tinted goggles. |
| ☀️ Sky | **Bluebird day** | % | today, tomorrow (whole day) | Will at least 15 cm of fresh snow have fallen at mid-mountain in the 36 hours before 09:00, followed by a sunny ski day (09:00–17:00)? | The dream day: fresh snow under a deep blue sky. Sunscreen and dark goggles; powder goes fast. |
| ☀️ Sky | **Sunset** | % and the sunset time | tonight, tomorrow evening | Will the sky be mostly clear (40 % of cloud or less) near the summit around sunset, from the hour before to the hour after? The tile gives the sunset time. | A sunset to watch from the top (the time assumes a flat horizon: ridges to the west hide it earlier). |
| ☀️ Sky | **Starry night** | % | this evening | Will the evening (18:00–00:00) have at least 4 clear hours (20 % of cloud or less) near the summit? | A starry sky for a night walk or stargazing. |
| ☀️ Sky | **Full sun** | hours of sun (median) | morning, lunchtime, afternoon | How many hours of the slot will be sunny at mid-mountain (little cloud, strong sunlight; daylight hours only)? | Sunglasses and sunscreen: the light is at its best. |
| 🧣 Comfort | **Mild day** | % | today, tomorrow (whole day) | Will the ski day (09:00–17:00) reach +5 °C at mid-mountain, with wind under 20 km/h and at least 5 sunny hours? | Picnic weather on the slopes. |
| 🧣 Comfort | **Wind chill** | felt °C (median), with the wind chill risk | morning, lunchtime, afternoon | How cold will it feel near the summit at the coldest of the slot (wind chill: temperature and wind together)? With Environment Canada's risk: moderate from −10 °C, high from −28 °C (frostbite in 10 to 30 minutes)… | Cover every bit of skin: frostbite comes fast in the wind. |
| 🚗 Getting there | **Chains needed** | Yes / Possible / No | today, tomorrow (whole day) | Will at least 2 cm of snow fall on the access road, at the bottom of the resort, from 20:00 the evening before to 10:00? | Fit chains or snow socks; leave earlier. Winter equipment is compulsory in the mountains anyway. |
| 🚗 Getting there | **Lifts in the wind** | km/h of wind (median), with light / strong / closures likely | morning, lunchtime, afternoon | How strong will the mean wind be near the summit at the windiest of the slot? Gusts are often 1.5 to 2 times stronger: closures likely from 45 km/h. | Top lifts may slow down or close: plan for the lower slopes. |
| ⚠️ Safety | **Wind-blown snow** | Yes / Possible / No | today, tomorrow (whole day) | Has at least 10 cm of snow fallen near the summit in the 48 hours before 09:00, with wind reaching 30 km/h since? | Wind slabs likely off-piste. Always read the avalanche bulletin first. |

A **white day** ("jour blanc") is a day without visible relief. Hour by hour
over the ski day (09:00–17:00), Bluebird counts an hour as white when the
resort is inside the cloud (humidity of at least 98 % and low cloud of at
least 90 %), when at least 0.5 cm of snow falls per hour, or in flat light
(sunlight below 30 % of what a clear sky would give at that hour). A day with
at least 6 white hours out of 8 is a white day.

A **bluebird day** is the opposite: fresh snow and a clear sky. An hour of
the ski day is sunny when clouds cover at most 30 % of the sky and sunlight
reaches at least 60 % of what a clear sky would give at that hour (early and
late hours, when the sun is very low, only need the clear sky). It takes at
least 6 sunny hours out of 8, after at least 15 cm of snow in the 36 hours
before 09:00.

Some indicators work around missing data, so read them as estimates:
**Chains needed** places the road at the bottom of the resort and brings
the mid-mountain temperature down to it (0.65 °C warmer per 100 m lower);
**Lifts in the wind** uses the mean wind, as the scenarios have no gusts;
**Sunset** and **Starry night** use the cloud cover of the whole air column,
so a sea of clouds below the summit counts as cloud.

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

Ideas under study, not yet on the site, by category. The most likely next
ones are marked ⭐. Each will be checked against the data really available
before it is built.

- **When**: *6 h* = a probability for today and tomorrow, refreshed every 6
  hours; *Season* = a season review (Rewind); *History* = since the data
  exist (weather reanalyses back to 1950, checked against Météo-France snow
  observations; their grid is coarser than the daily model, so they compare
  resorts and decades, they are not measurements).
- **For**: the activities it matters to: alpine skiing, snowshoeing,
  cross-country skiing, village (non-skiers), or everyone.

#### ❄️ Snow

| Indicator | When | For | Question |
|---|---|---|---|
| **Rain at the resort** ⭐ | 6 h | Everyone | Chance of rain up to the summit, making a wet day and heavy snow. |
| **Snow on the ground** ⭐ | 6 h | Everyone | How deep the snow is on the slopes today, and whether it is building up or melting. |
| **Snow in the village** | 6 h | Village | Chance that the resort village wakes up white tomorrow (sledging, postcard views). |
| **Powder days** ⭐ | Season | Alpine skiing, snowshoeing | Days with 20 cm or more of new snow in 24 hours. |
| **Biggest storm** | Season | Everyone | The largest snowfall over 72 hours, with its dates. |
| **Natural snow season** | Season | Everyone | First and last day with at least 30 cm of snow on the ground, and the number of days in between. |
| **Peak snowpack** | Season | Everyone | The deepest snow on the ground and its date. |
| **Rain days at the resort** | Season | Everyone | Days of rain up to the summit in mid-season. |
| **Snow cannon nights** | Season | Alpine skiing | Nights cold and dry enough to make snow. |
| **Slopes vs off-piste gap** | Season | Alpine skiing | Resorts where the terrain around the slopes got much more snow than the slopes. |
| **This season in history** ⭐ | History | Everyone | Where the current season ranks since 1950 ("the 12th snowiest"), updated every day. |
| **Climate trend** ⭐ | History | Everyone | How the number of snow days changes per decade at each resort. |
| **Snow reliability** | History | Everyone | Share of seasons with at least 100 days of enough snow: useful to choose a season pass. |
| **When to go?** | History | Everyone | For each week of the season, the historical chance of good conditions at each resort. |
| **Snow at Christmas** | History | Everyone | Historical chance of at least 30 cm of snow on the ground on 25 December. |
| **Records** | History | Everyone | Biggest 24-hour snowfall, biggest storm, coldest season since 1950. |
| **Later openings** | History | Everyone | Average date of the first good snow cover, decade by decade. |
| **Rising rain-snow line** | History | Everyone | Average winter altitude of the 0 °C level, decade by decade. |
| **Our success rate** | History | Everyone | How well Bluebird's past probabilities matched the snow that fell ("when we say 70 %, it snows 68 % of the time"). |

#### 🎿 Snow quality

| Indicator | When | For | Question |
|---|---|---|---|
| **Wax of the day** | 6 h | Cross-country skiing | Snow temperature and humidity on the tracks, to choose the right wax. |
| **Coldest morning and freeze-thaw days** | Season | Everyone | The season's coldest morning and the number of spring-snow days. |

#### ☀️ Sky

| Indicator | When | For | Question |
|---|---|---|---|
| **Sea of clouds** ⭐ | 6 h | Everyone | Chance that the top of the resort is in the sun above a sea of clouds while the valley stays grey. |
| **Best time slot** | 6 h | Everyone | The best hours of the day per resort, combining visibility, sun and wind. |
| **Sunniest resort** ⭐ | Season | Everyone | Which resort got the most sunshine over the season (the sunlight is already stored)? |
| **Bluebird days** ⭐ | Season | Everyone | How many bluebird days each resort had. |
| **Sunset evenings** | Season | Everyone | How many evenings offered a visible sunset from the ski area. |
| **Sea-of-clouds days** | Season | Everyone | How many days the resort stood above a sea of clouds. |
| **Longest bluebird streak** | History | Everyone | The record number of sunny days in a row. |

#### 🧣 Comfort

| Indicator | When | For | Question |
|---|---|---|---|
| **UV and sunburn** | 6 h | Everyone | Peak UV at altitude, made stronger by the snow's reflection. |
| **Village weather tonight** | 6 h | Village | Rain, snow and temperature in the resort village this evening. |

#### 🚗 Getting there

| Indicator | When | For | Question |
|---|---|---|---|
| **Expected crowds** | 6 h | Everyone | Crowd index from school holidays by zone, weekends and good weather. |
| **Lifts stopped by wind** | Season | Alpine skiing | Days when the wind would have closed the top lifts. |
| **Chain days** | Season | Everyone | Mornings when chains would have been needed on the access road. |
| **Holiday luck** | Season | Everyone | Which school-holiday zone (A, B or C) had the best conditions. |
| **Weekend index** | Season | Everyone | Share of weekends with good conditions: what most skiers actually live. |

#### ⚠️ Safety

Never a replacement for the official avalanche bulletin (BERA).

| Indicator | When | For | Question |
|---|---|---|---|
| **Avalanche risk** | 6 h | Off-piste, touring, snowshoeing | Danger level (1 to 5) of the Météo-France avalanche bulletin, and whether it rises tomorrow. |
| **Ski touring and snowshoe start time** | 6 h | Touring, snowshoeing | Best start and return times for an outing (night freeze, warming, avalanche risk). |
| **High avalanche risk days** | Season | Off-piste, touring, snowshoeing | Days with an avalanche danger level of 4 or 5. |

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
- 19 indicators in six categories, for each time slot or day of today and
  tomorrow (see [Available indicators](#available-indicators)), each shown
  as an amount (cm, hours, °C, km/h), a Yes / Possible / No or a
  percentage: snow, snow alert, snow cannons; powder on piste and
  off-piste, spring snow, hard snow, heavy snow, easy conditions; white day,
  bluebird day, sunset, starry night, full sun; mild day, wind chill; chains
  needed, lifts in the wind; wind-blown snow.
- Updated every 6 hours; tiles of slots that are over disappear on their own.
- A service status page (linked from the footer), and the last valid values kept (and flagged)
  when an update fails.
- Betting-style tiles: top three resorts as odds buttons with their
  reliability dots, full ranking on demand, optional odds.
  Compact tiles without a picture for the indicators lower on the page.
- Two-sided tiles: the back explains the indicator and the reliability for its slot.
- Filters in levels, like a music app: category of indicator (Snow, Snow
  quality, Sky, Comfort, Getting there, Safety) or the Rewind, then day (Today, Tomorrow), then time slot; a home
  page led by the bluebird day, then snow, powder and white day.
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
- Weekend and week-long slots (with a matching filter level).
- **Planned filters**, one level at a time (at most five):
  1. **Activity**: alpine skiing, snowshoeing, cross-country skiing, village
     (non-skiers), next to **Rewind 25/26** (unchanged). Snowshoeing and
     cross-country need their own sites (nordic areas and trails), which
     will be added to the resort list first.
  2. **Category**: Snow, Snow quality, Sky, Comfort, Getting there, Safety
     (see [Categories](#categories); the level-1 filters until the activity
     filter arrives), only those with indicators for the activity.
  3. **Terrain**, for alpine skiing: easy pistes (green and blue), steeper
     pistes (red and black), off-piste.
  4. **Day**: today, tomorrow (and later the weekend).
  5. **Time slot**: morning to night.

  A level with a single choice is applied on its own and skipped. There will
  be no skier level (beginner to expert): the weather is the same for
  everyone, but it differs by terrain, which the piste map tells apart; the
  **Easy conditions** indicator answers beginners.
- A 7-day trend tile and a map of the ski areas (piste and lift data from
  OpenStreetMap is already collected and refreshed once a season).
- More mountain ranges: Northern and Southern Alps, Massif Central, Vosges, Jura.
- Checking past forecasts against observed snow to make the percentages more accurate.

## Limits and safety

- **Bluebird is a planning aid, not an avalanche bulletin.** Before any
  off-piste outing, read the official Météo-France avalanche bulletin (BERA),
  carry avalanche safety equipment and know how to use it. The **Wind-blown
  snow** tile is a warning sign, never a danger level.
- **Chains needed** estimates the road from the resort's own forecast; it
  does not know snow clearing nor the road's real elevation. Mountain winter
  equipment rules apply whatever it says.
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

**Why don't the tiles agree?**
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
