# Prompt for Claude in Chrome: collect @shirllevii reference data

**How to use**
1. Log in to Instagram in Chrome. Use Shir's own account if you want Insights.
2. Open https://www.instagram.com/shirllevii/
3. Open the Claude extension and paste everything inside the box below.
4. When it finishes, save its answer as `instagram-reels/references/shirllevii_profile.md` in this repo, or just paste it back to Claude Code.
5. Drag the screenshots / downloaded covers it asks for into `instagram-reels/references/media/`.

---

```text
You are helping me build a reference file about the Instagram account @shirllevii (Shir Levi, lash & brow studio in Jerusalem). I work with Shir and have her permission. Only READ — do not like, follow, comment, message, or change anything.

Work only on https://www.instagram.com/shirllevii/ and its own posts/reels. Do not visit other accounts.

Collect the following, then output ONE markdown document using exactly the structure at the end. Copy Hebrew text exactly as written (do not translate it; add an English gloss in parentheses only where useful). If something isn't visible, write "not visible" — never guess.

1. PROFILE
   - Display name, username, category, full bio text (exact), link in bio (URL + what it opens: WhatsApp / booking / linktree etc.)
   - Followers / following / posts counts
   - Story highlight names (in order) + 1 line on what each contains (open each one briefly)
   - Profile picture description

2. REELS TAB (most important)
   Open the Reels tab. For the 20 most recent reels AND any reel with noticeably higher views than the rest:
   - URL, approx post date, view count (shown on the grid), likes and comments if visible
   - Hook: the on-screen text / first thing said in the first 2 seconds (exact)
   - Format (e.g. before/after, process/ASMR, POV, talking to camera, montage, tutorial, price/deal, client reaction)
   - Service shown (lash lift, brow lamination, tint, combo...)
   - Length (approx seconds), audio used (trending song name / original audio / voice-over)
   - Caption: first 2 lines exact + hashtags used
   - CTA used (WhatsApp, link in bio, DM, none)
   Then rank the top 5 by views and write 2–3 sentences on what the top performers have in common.

3. GRID POSTS
   For the last 12 feed posts: URL, type (photo/carousel), what's shown, caption first line, likes/comments.

4. PRICES, SERVICES & DEALS
   Every price, service name, duration, discount or deal mentioned anywhere (bio, highlights, captions, story highlights, pinned posts). Quote exactly + where you found it.

5. BRAND STYLE
   Colours used in text overlays/backgrounds, fonts/style of on-screen text, logo usage, typical framing (macro eye close-up, full face, etc.), tone of voice in captions (formal/friendly, emojis used).

6. AUDIENCE SIGNALS
   The 10 most common types of comments/questions (e.g. "how much?", "how long does it last?", "where are you?") with 2–3 exact example comments each. These become future reel topics.

7. INSIGHTS (only if I'm logged in as Shir and the Professional dashboard is visible)
   Accounts reached (last 30 days), top content by reach, follower age/gender/top cities, most active days/hours.

8. MEDIA TO SAVE
   List the URLs of the top 5 reels and the 5 best close-up photos so I can download them manually.

OUTPUT FORMAT (exactly):

# @shirllevii – reference
_Collected: <date>_
## 1. Profile
## 2. Reels (table: # | URL | date | views | likes | comments | hook | format | service | length | audio | CTA)
### Top 5 by views + what they share
## 3. Grid posts (table)
## 4. Prices, services & deals (table: item | price/deal | source)
## 5. Brand style
## 6. Audience questions (topic | count | example comments)
## 7. Insights
## 8. Media to save (URL list)
## 9. 5 reel ideas based on what is working for THIS account

If the page is long, scroll slowly and keep going until the 20 reels are covered. Tell me if Instagram blocks or limits anything.
```
