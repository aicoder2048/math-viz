# Musical Ulam Spiral

An animated Ulam Spiral visualization with real-time prime number sonification. Primes are mapped to piano melodies, special prime families get unique instruments and visual markers, and each run generates a different musical style.

![Musical Ulam Spiral](musical_ulam_spiral.png)

## Features

### Visual
- **Ulam Spiral** rendered with Python's turtle graphics on a dark background
- Each **prime** gets a unique color (golden-ratio HSL distribution) with its number displayed inside
- **Special prime families** highlighted with colored rings and symbols:
  | Ring Color | Meaning | Definition |
  |-----------|---------|------------|
  | Gold | Twin Prime | Gap of 2 with previous prime, e.g. (11, 13) |
  | Cyan | Cousin Prime | Gap of 4, e.g. (7, 11) |
  | Pink | Sexy Prime | Gap of 6, e.g. (5, 11) |
  | ◆ marker | Sophie Germain | Both p and 2p+1 are prime |
  | ★ marker | Palindrome Prime | Reads the same forwards and backwards, e.g. 131 |
- **Non-primes** shown as faint rings with dim numbers
- **Stats panel** (right side) with real-time counts, ring legend, and music info
- **Prime encyclopedia** (press `i`) with definitions and fun facts (in Chinese)

### Music / Sonification

Built on **FluidSynth** with the **FluidR3_GM** SoundFont (141 MB, professional GM library).

#### Instruments
| Channel | Role | Instrument |
|---------|------|-----------|
| ch0 | Regular primes | Acoustic Grand Piano (GM 0) |
| ch1 | Twin primes | Piano chord (major triad) |
| ch2 | Cousin primes | Orchestral Harp (GM 46, fifth interval) |
| ch3 | Sexy primes | String Ensemble (GM 48, fifth interval) |
| ch4 | Bass pad | String Ensemble (GM 48, sustained root) |

#### Melody Design
- **Wave pattern**: notes walk up then down the scale (do-re-mi-fa-sol-la-sol-fa-mi-re-do...) for a natural, flowing melody
- **Octave alternation**: each wave cycle alternates between C4 and C5
- **Gentle dynamics**: velocity 30-42, extremely soft and warm
- **Reverb**: light room (size 0.15, damping 0.8, level 0.1), no chorus
- **Ending**: three-voice harmonic fade (piano root + harp fifth + strings third) that decays naturally

#### Style Presets (randomly chosen each run)
| Style | Scales |
|-------|--------|
| Moonlight (月光) | Minor, Major |
| Dawn (晨曦) | Major, Pentatonic |
| Nocturne (夜想) | Minor, Dorian |
| Pastoral (田园) | Major, Mixolydian |
| Meditation (冥想) | Pentatonic, Minor |

## Requirements

- Python >= 3.14
- [FluidSynth](https://www.fluidsynth.org/) (`brew install fluid-synth`)
- [FluidR3_GM.sf2](https://member.keymusician.com/Member/FluidR3_GM/) — place in the project root

```bash
pip install pygame-ce pyfluidsynth
```

Or with [uv](https://docs.astral.sh/uv/):
```bash
uv sync
```

## Usage

```bash
# Default: 500 numbers, medium window, no sound
python ulam_spiral_mr_zou.py

# With music
python ulam_spiral_mr_zou.py --sound

# Start paused (press Space to begin)
python ulam_spiral_mr_zou.py --sound --paused

# Custom count and window size
python ulam_spiral_mr_zou.py 800 --size large --sound

# Start from a different number
python ulam_spiral_mr_zou.py --start 1000 --sound
```

### Keyboard Controls
| Key | Action |
|-----|--------|
| `Space` | Pause / Resume |
| `i` | Toggle prime encyclopedia panel |
| `q` / `Esc` | Quit (while paused) |

### CLI Options
| Option | Description | Default |
|--------|-------------|---------|
| `count` | Number of integers to draw | 200/500/1200 by size |
| `--size` | Window size: `small`, `mid`, `large` | `mid` |
| `--start` | Starting integer | 1 |
| `--sound` | Enable music | off |
| `--paused` | Start in paused state | off |
