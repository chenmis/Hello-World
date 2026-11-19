# Shir Levi – Instagram Reels deal generator

Turns the logo and the studio photos into ready-to-post **Instagram Reels** (1080×1920, 30 fps, H.264 MP4), plus a cover image for each.

| File | What it is | Length |
|---|---|---|
| `output/01_lash_lift_deal.mp4` | Lash-lift hook, results, **15% off first treatment**, CTA | 13.8 s |
| `output/02_brow_lamination_deal.mp4` | "Still filling in your brows with pencil?" hook, process, **₪149 instead of ₪199**, CTA | 13.8 s |
| `output/03_combo_deal.mp4` | Lashes / brows split screen, "Why choose?", **combo saves ₪50**, CTA | 12.0 s |
| `output/04_every_detail_montage.mp4` | Fast-cut "כל פרט חשוב" montage with a punch-in on every cut and an urgency CTA | 7.1 s |

### Viral-format reels (built from what's getting the most views)

| File | Viral format | Why it works |
|---|---|---|
| `output/05_viral_pov_loop.mp4` | **POV + seamless loop.** "POV: קמת בבוקר והריסים כבר מסולסלים", with the end flowing back into the start | Loops get rewatched, and **watch time** is Instagram's #1 ranking signal |
| `output/06_viral_wait_for_reveal.mp4` | **"Wait for it" reveal.** An extreme lash close-up with a progress bar slowly pulls back to the full face | The suspense keeps viewers to the end; transformation reveals are the top lash/brow format |
| `output/07_viral_3_signs_listicle.mp4` | **"3 signs you need a lash lift."** Numbered listicle ending in "save this video" | Lists get **saved**, and saves rank higher than likes |
| `output/08_viral_send_a_friend.mp4` | **Comment and send bait.** "Which one are you? Comment 1 or 2" plus "Send to a friend who should come with you" (with a bring-a-friend deal) | **Sends** are the strongest signal for reaching non-followers |

These use **native-style captions** (black text on white boxes, like text added inside Instagram). This looks like a real post, not an ad.

> ⚠️ **The prices and discounts are examples.** Change them in `deals.json` before posting.

## Change the deals and re-render

1. Edit `deals.json`: texts, prices, durations, and which photo goes in each scene.
2. Run:
   ```bash
   pip install pillow          # needs Pillow built with libraqm (for Hebrew right-to-left text) + ffmpeg
   python3 make_reels.py       # all reels
   python3 make_reels.py 02    # only reels whose id contains "02"
   ```
3. To add photos, put them in `assets/photos/` and refer to them by file name.

Scene types: `photo` (Ken Burns zoom + animated text), `split` (two photos side by side), `deal` (badge that pops in, plus title), `end` (logo, CTA button, handle), `montage` (fast cuts).

## Why this tool, and not an online "AI reel maker" or an AI-agent framework?

- **Hebrew is shaped correctly.** In the current stories (screenshots), parts of the Hebrew show up as empty boxes `□□□□`. The app's font has no Hebrew glyphs. This generator uses Heebo, a font built for Hebrew, with full right-to-left shaping.
- **The look stays on-brand and repeatable.** It uses the same cream logo plate, cocoa text box, and mauve button as the existing stories, every time.
- **It's free and runs offline.** No subscription, no watermark, no API keys. A new deal takes about 1 minute to render.
- On GitHub, the closest thing to an AI-agent ("Strands Agents") Instagram tool is a [video-ad demo built on AWS Strands + Nova](https://dev.to/debadattap/building-an-ai-powered-video-ad-creator-with-aws-nova-and-strands-agents-2ogn). It needs AWS Bedrock access and generates *AI* footage. For a lash/brow studio, **real client results beat AI footage**, so a template renderer over your own photos is the more efficient route. This script can later be wrapped as a Strands tool if automation is wanted.

## What's working for lash and brow accounts (built into these reels)

1. **A hook in the first 1–2 seconds:** a question or bold statement on screen ("עדיין ממלאת גבות בעיפרון?").
2. **Results first, talking later:** close-ups of curled lashes and laminated brows carry the video.
3. **Short:** 7–15 seconds, so people rewatch, which the algorithm rewards.
4. **One clear offer plus urgency:** "for a limited time", "spots left this week".
5. **One CTA:** WhatsApp via the link in bio.
6. **Fast-cut montage (reel 04)** synced to trending audio.
7. **Combo / bundle offers** (lashes + brows) raise the value of each booking.

## Posting checklist

- **Add a trending sound inside Instagram.** The videos have a silent audio track on purpose. Pick a trending audio in the Reels editor and keep its volume low. Instagram's own music is licence-safe and gives more reach.
- Use the `_cover.jpg` file as the Reel cover so the grid looks consistent.
- Caption formula: hook → offer → "שלחי הודעה בוואטסאפ, לינק בביו", plus 3–5 local hashtags such as `#הרמתריסים #למינציהלגבות #ירושלים #עיצובגבות #lashlift`.
- Post 3–4 Reels a week, between about 19:00 and 21:00. Share each one to your Story with a link sticker to WhatsApp.
- Repost the best performer (most shares and saves) with a new hook after about 2 weeks.
- Film real **before/after** clips (same light, same angle). They are the strongest format in this niche. Add them to `assets/photos/` and to a `split` scene.

Fonts: Heebo and Rubik (SIL Open Font License, Google Fonts).
