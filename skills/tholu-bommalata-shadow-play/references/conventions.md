# Conventions, Sources and Departures

Re-check this table against the sources before each film; it may be incomplete.

## Conventions to honour

| Aspect | Convention (from sources) | In the code |
|---|---|---|
| Material | Translucent goat hide painted on both faces, so shadows fall in colour | puppets drawn into a Multiply layer over the lit cloth |
| Scale | Large figures (about 120–180 cm) on a screen about 3–4 m × 2 m; size also marks status | main figure ~560 px of an ~850 px screen; scale `s` down for minor roles |
| Faces | Profile; the central head of ten-headed Ravana is the only frontal face | `head()` is a profile with a large elongated eye |
| Ornament | Holes of varied shapes chiselled into the leather, read as jewellery when lit | `dots()` in the screen colour |
| Joints | Loosely stitched limbs (shoulders, elbows, often waist and knees); legs often one rigid piece | articulated arms with visible rivets; rigid legs |
| Handling | A central stick for the body, a separate stick for the head, sticks to the palms | body, head and two hand rods drawn below each puppet |
| Colour | Rama and Krishna blue; female characters in yellow or orange tones; exceptions exist | per-character spec |
| Divinity | Repeated U-shaped marks with a small oval at the base, on the body | `umark()`; `divine=True` on a spec |
| Screen | White cloth pulled taut on poles; the lower part covered with black cloth so puppeteers can stand | `screen()` plus the dark band in `frame()`; captions sit in the band |
| Light | Traditionally a row of castor-oil lamps giving even light | a lamp row behind the cloth; keep the central hotspot gentle |
| Opening | Puppets placed at both sides of the screen before the invocation; Ganesha appears first and dances, then Saraswati | `sc_invoc()`, about 14 s |
| Entrances | Divinities from the audience's right; other characters from the left; demons drop from above | block every entrance this way |
| Comic characters | Bangarakka, Jettupoligadu and Ketigadu step out of the story and address the audience | optional interlude; ask the user |
| Sound | The puppeteers speak and sing every line; anklet bells and stamping on boards; harmonium, mridangam or maddela, cymbals, conch, mukhaveena | synthetic stand-in in `score_shadow.py`; voice via [voice-script.md](./voice-script.md) |
| Repertoire | Mainly the Ramayana (often the Telugu Ranganatha Ramayanam), some Mahabharata and Bhagavata episodes | if the story is outside this, say so |
| Scenery | Flat cut-out trees, animals and landscape pieces, some unarticulated | `tree()`, `hut()`, `lampstand()`, `dais()`, `bush()` |

## Departures this code makes (list them in every fidelity note unless fixed)

- Seated puppets and deep bows: staging choices, not documented conventions.
- Coloured stage light for flashbacks (blue, red, gold): a modern device.
- The leaf garland along the top of the screen: a decoration of our own.
- Costumes and faces designed here, not modelled on any maker's puppets.
- Synthetic music and no voice.

## Sources to start from

- Sahapedia, *Tholu Bommalata: Telugu Shadow Puppet Theatre*: invocation order, entrances, comic characters, instruments, current state of the tradition. https://www.sahapedia.org/tholu-bommalata-telugu-shadow-puppet-theatre
- UNIMA, *World Encyclopedia of Puppetry Arts*, entry on tolu bommalata. https://wepa.unima.org/
- M. Nagabhushana Sarma, *Tolu Bommalata: The Shadow Puppet Theatre of Andhra Pradesh*, Sangeet Natak journal.
- ThePrint, excerpt *Telling mythological tales with shadow puppets*: the performing community and its sources for song and dialogue.
- Arts Illustrated, *Where the shadows speak*: a puppeteer family's account, including the language of performance.

The puppeteer families today are concentrated in Anantapur, Guntur and Nellore districts; Nimmalakunta (Anantapur) holds a Geographical Indication tag for the leather craft.
