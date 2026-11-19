"""Original, royalty-free soundtrack + synced sound effects for each reel.

Everything here is synthesised from scratch with numpy (no samples, no copyrighted music),
so the finished videos are safe to share and post.

Music: warm, soft "beauty reel" groove - electric-piano chords, plucked arpeggio, sub bass,
kick / clap / hats at 109 BPM (one beat = one 0.55 s montage cut).
SFX:   whoosh on every transition, pops when badges / numbers / captions appear,
       sparkle on deals, riser + impact on the "wait for it" reveal, ticks on montage cuts.
"""
import wave

import numpy as np

SR = 44100
BPM = 60 / 0.55
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(11)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def add(buf, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n] * gain


def lowpass(x, alpha):
    """Cheap one-pole low-pass, vectorised via cumulative filtering in blocks."""
    y = np.empty_like(x)
    acc = 0.0
    a = float(alpha)
    for k in range(len(x)):  # only used on short sounds
        acc += a * (x[k] - acc)
        y[k] = acc
    return y


# ------------------------------------------------------------- instruments
def epiano(f, dur, bright=1.0):
    t = tt(dur)
    env = np.exp(-t * 2.2) * (1 - np.exp(-t * 300))
    trem = 1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)
    s = np.sin(2 * np.pi * f * t) + 0.35 * bright * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 5)
    s += 0.12 * bright * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 9)
    rel = np.clip((dur - t) / 0.08, 0, 1)
    return s * env * trem * rel


def pluck(f, dur=0.35):
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 4 * f * t)
    return s * np.exp(-t * 9) * (1 - np.exp(-t * 500))


def pad(freqs, dur):
    t = tt(dur)
    env = np.clip(t / 0.5, 0, 1) * np.clip((dur - t) / 0.5, 0, 1)
    s = np.zeros_like(t)
    for f in freqs:
        for d in (-0.004, 0.0, 0.004):
            s += np.sin(2 * np.pi * f * (1 + d) * t + rng.random() * 6.28)
    return s * env / (len(freqs) * 3)


def bass(f, dur):
    t = tt(dur)
    env = (1 - np.exp(-t * 200)) * np.exp(-t * 1.5) * np.clip((dur - t) / 0.05, 0, 1)
    return (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)) * env


def kick():
    t = tt(0.4)
    f = 42 + 95 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) * (1 - np.exp(-t * 2000))


def clap():
    t = tt(0.25)
    n = rng.standard_normal(len(t))
    n = lowpass(n, 0.3) - lowpass(n, 0.06)  # band-pass ~0.5-2.5 kHz: warm snap, no hiss
    env = np.zeros_like(t)
    for k, d in enumerate((0.0, 0.011, 0.022)):
        env += (t >= d) * np.exp(-(t - d).clip(0) * (60 if k < 2 else 28))
    return n * env * 0.9


def hat(open_=False):
    t = tt(0.18 if open_ else 0.05)
    n = rng.standard_normal(len(t))
    n = np.diff(np.diff(n, prepend=0), prepend=0)  # crude high-pass
    return n * np.exp(-t * (18 if open_ else 80)) * 0.07


# ------------------------------------------------------------- sfx
def whoosh(dur=0.5):
    t = tt(dur)
    n = rng.standard_normal(len(t))
    # sweep a low-pass upward then down
    out = np.empty_like(n)
    acc = 0.0
    for k in range(len(n)):
        x = k / len(n)
        a = 0.01 + 0.12 * np.sin(np.pi * x) ** 2
        acc += a * (n[k] - acc)
        out[k] = acc
    env = np.sin(np.pi * t / dur) ** 2
    return out * env * 1.4


def pop(f0=520, f1=1100, dur=0.11):
    t = tt(dur)
    f = f0 + (f1 - f0) * (1 - np.exp(-t * 60))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 38) * (1 - np.exp(-t * 3000))


def sparkle(n=7, spread=0.35):
    out = np.zeros(int((spread + 0.6) * SR))
    for k in range(n):
        f = rng.uniform(2200, 5200)
        t = tt(0.5)
        s = np.sin(2 * np.pi * f * t) * np.exp(-t * 10) * (1 - np.exp(-t * 4000))
        add(out, s, k * spread / n, rng.uniform(0.25, 0.5))
    return out


def tick():
    t = tt(0.04)
    return np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 160) * 0.6


def riser(dur):
    t = tt(dur)
    n = rng.standard_normal(len(t))
    n = lowpass(n, 0.05)
    f = 220 + 660 * (t / dur) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return (n * 0.6 + tone * 0.35) * (t / dur) ** 2.2


def impact():
    t = tt(1.2)
    f = 30 + 70 * np.exp(-t * 14)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3)
    n = rng.standard_normal(len(t))
    return boom * 1.1 + lowpass(n, 0.1) * np.exp(-t * 6) * 0.6


# ------------------------------------------------------------- music bed
PROG = [  # (bass midi, chord voicing midi) - Am9, Fmaj9, Cmaj7, G6
    (45, [60, 64, 67, 71]),
    (41, [57, 60, 64, 67]),
    (48, [52, 55, 59, 64]),
    (43, [55, 59, 62, 64]),
]


def music(total, loop=False):
    buf = np.zeros(int((total + 1.5) * SR))
    keys, arp, low, drums = (np.zeros_like(buf) for _ in range(4))
    nbars = int(np.ceil(total / BAR)) + 1
    for b in range(nbars):
        t0 = b * BAR
        root, chord = PROG[b % 4]
        for n in chord:
            add(keys, epiano(midi(n), BAR * 0.98, 0.8), t0, 0.24)
        add(keys, pad([midi(n) for n in chord], BAR + 0.3), t0, 0.35)
        add(low, bass(midi(root), BEAT * 1.9), t0, 0.55)
        add(low, bass(midi(root), BEAT * 1.4), t0 + 2.5 * BEAT, 0.45)
        pattern = [0, 2, 1, 3, 2, 1, 3, 2]
        for k, p in enumerate(pattern):
            add(arp, pluck(midi(chord[p] + 12)), t0 + k * BEAT / 2, 0.17 if k % 2 == 0 else 0.12)
        for beat in range(4):
            bt = t0 + beat * BEAT
            if beat in (0, 2) or (beat == 3 and b % 2 == 1):
                add(drums, kick(), bt if beat != 3 else bt + BEAT / 2, 0.6)
            if beat in (1, 3):
                add(drums, clap(), bt, 0.35)
            for h in range(2):
                swing = 0.03 if h == 1 else 0.0
                add(drums, hat(open_=(h == 1 and beat == 3)), bt + h * BEAT / 2 + swing, 0.9 if h == 0 else 0.6)
    # sidechain-style pump on keys/pad from the kick pattern
    pump = np.ones_like(buf)
    t = np.arange(len(buf)) / SR
    phase = (t % (2 * BEAT)) / (2 * BEAT)
    pump = 0.75 + 0.25 * np.clip(phase * 6, 0, 1)
    mix = (keys + arp) * pump + low + drums
    mix = mix + echo(keys + arp, 0.21, 0.28, 4)
    mix = mix[: int(total * SR)]
    if not loop:
        fo = int(0.8 * SR)
        mix[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    fi = int(0.02 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)
    return mix


def echo(x, delay, fb, taps):
    out = np.zeros_like(x)
    d = int(delay * SR)
    for k in range(1, taps + 1):
        if d * k < len(x):
            out[d * k:] += x[: len(x) - d * k] * fb ** k
    return out


# ------------------------------------------------------------- per-reel cue sheet
def cues(scenes, starts, total):
    """Place SFX exactly where the visuals animate (timings mirror make_reels.py)."""
    ev = []
    for i, sc in enumerate(scenes):
        s, t0, d = sc.s, starts[i], sc.duration
        typ = s["type"]
        if i > 0 and typ != "montage":
            ev.append(("whoosh", t0 - 0.25, 0.32))
        if typ == "photo":
            if "number" in s:
                ev.append(("pop", t0 + 0.2, 0.5))
            if s.get("style") == "native":
                for k, _ in enumerate(s.get("lines", [])):
                    ev.append(("popsoft", t0 + 0.1 + k * 0.35 + 0.08, 0.28))
                if s.get("footer"):
                    ev.append(("popsoft", t0 + 0.68, 0.25))
        elif typ == "deal":
            ev += [("pop", t0 + 0.42, 0.6), ("sparkle", t0 + 0.45, 0.55), ("popsoft", t0 + 0.8, 0.25)]
        elif typ == "end":
            ev += [("sparkle", t0 + 0.1, 0.35), ("pop", t0 + 0.78, 0.5)]
        elif typ == "split":
            ev += [("whoosh", t0 - 0.05, 0.3), ("popsoft", t0 + 0.6, 0.3), ("popsoft", t0 + 0.8, 0.3)]
        elif typ == "choice":
            ev += [("whoosh", t0 - 0.05, 0.35), ("pop", t0 + 0.7, 0.45), ("pop", t0 + 0.95, 0.45),
                   ("popsoft", t0 + 0.4, 0.25), ("popsoft", t0 + 0.75, 0.25), ("popsoft", t0 + 1.3, 0.25)]
        elif typ == "reveal":
            ra = s.get("reveal_at", 0.65) * d
            ev += [("popsoft", t0 + 0.18, 0.28), ("riser", t0 + ra - 2.2, 0.5),
                   ("impact", t0 + ra, 0.75), ("sparkle", t0 + ra + 0.05, 0.6)]
            for k, _ in enumerate(s.get("lines_after", [])):
                ev.append(("popsoft", t0 + ra + 0.1 + k * 0.35 + 0.08, 0.28))
        elif typ == "montage":
            cut = s.get("cut", 0.55)
            for k in range(1, len(s["images"])):
                ev.append(("tick", t0 + k * cut, 0.35))
            for k, _ in enumerate(s.get("lines", [])):
                ev.append(("pop", t0 + 0.4 + k * 0.6 + 0.2, 0.5))
    return ev


SFX = {
    "whoosh": lambda: whoosh(0.5),
    "pop": lambda: pop(),
    "popsoft": lambda: pop(700, 1250, 0.07),
    "sparkle": lambda: sparkle(),
    "tick": tick,
    "riser": lambda: riser(2.2),
    "impact": impact,
}


def build(reel, scenes, starts, total, path):
    loop = bool(reel.get("loop"))
    m = music(total, loop)
    fx = np.zeros_like(m)
    for name, t, g in cues(scenes, starts, total):
        add(fx, SFX[name](), t, g)
    m = m / (np.abs(m).max() + 1e-9) * 0.55
    mix = m + fx * 0.45
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.8
    # gentle stereo: slight delay on the right channel
    d = int(0.008 * SR)
    left, right = mix, np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([left, right], axis=1)
    pcm = (st * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
