---
name: jsx-to-gif-separate
description: Convert JSX/React animation into SEPARATE GIF files — one GIF per step/page. Use when the user wants individual GIF animations for each step in a multi-step JSX component. Trigger keywords: 'JSX转GIF', '分页GIF', 'separate GIF', '每一页GIF', '逐步导出GIF', 'GIF per step', '动画转GIF分页'. Also trigger when user says 'export each step as GIF' or '每步一个GIF'.
---

# jsx-to-gif-separate

**Output: One GIF file per step.** If the JSX has N steps, produce N GIF files named `01_步骤名.gif`, `02_步骤名.gif`, etc.


## MANDATORY: Environment Setup (run FIRST)

```bash
playwright install chromium 2>&1 | tail -3
which ffmpeg xvfb-run && python3 -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

**CRITICAL:** ALWAYS use Playwright + Chromium. NEVER fall back to sharp, puppeteer-core, node-canvas, or SVG-only rendering. ALWAYS prefix scripts with `xvfb-run -a`.

---

## Pipeline

```
JSX → Analyze → Rewrite to vanilla HTML/JS (zero CDN) → Test screenshot → Capture frames → Encode
```

---

## Step 1: Analyze JSX

Identify:
- Number of steps/pages
- Dependencies to replace (see table below)
- Animation type (JS frame loop vs CSS one-shot vs CSS infinite)
- Timing per step

### Dependency Replacement Table

| Dependency | Detection | Replacement |
|-----------|-----------|-------------|
| React/JSX | `import React`, JSX syntax | Vanilla JS + `innerHTML` |
| Tailwind CSS | `className="flex items-center..."` | Inline `style=""` |
| lucide-react | `import { Zap } from 'lucide-react'` | Emoji (⚡💿📦◎▽🌧🔌📌) or inline SVG |
| Google Fonts | `@import url(fonts.googleapis.com)` | System fonts: `-apple-system, 'Segoe UI', sans-serif` |
| recharts/d3 | `import { LineChart }` | Inline SVG or canvas |

### Animation Type → Capture Strategy

| Type | Detection | Strategy |
|------|----------|---------|
| JS frame loop | `setInterval(() => { frame++; render() }, 80)` | Continuous capture |
| CSS one-shot | `@keyframes` + `forwards` | Reset innerHTML on step switch to restart |
| CSS infinite | `@keyframes` + `infinite` | Continuous capture |

---

## Step 2: Rewrite to Vanilla HTML/JS

### Template

```html
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>/* ALL CSS inline, @keyframes if needed */</style>
</head><body>
<div id="app"><!-- skeleton --></div>
<script>
var STEPS = [ /* step data */ ];
var currentStep = 0, frame = 0;

function render() {
  var step = STEPS[currentStep];
  // Update DOM; for CSS one-shot: replace innerHTML to restart animations
}

setInterval(function(){ frame++; render(); }, 80);

window.autoAdvance = false;
setInterval(function(){
  if (window.autoAdvance && currentStep < STEPS.length - 1) { currentStep++; render(); }
}, 5000);

render();
</script></body></html>
```

**Rules:** `currentStep`, `render()`, `window.autoAdvance` MUST be global. `autoAdvance` defaults to `false`.

### Tailwind Quick Reference

```
flex→display:flex  items-center→align-items:center  gap-3→gap:12px
w-full→width:100%  h-8→height:32px  p-4→padding:16px
text-xl→font-size:20px  font-bold→font-weight:700
rounded-xl→border-radius:12px  bg-slate-900→background:#0f172a
text-blue-400→color:#60a5fa  border-slate-800→border-color:#1e293b
```

Slate: `400:#94a3b8 500:#64748b 700:#334155 800:#1e293b 900:#0f172a 950:#020617`

### Layout: Convert desktop sidebar layouts to single-column portrait (540×960 logical).

---

## Step 3: Test Screenshot

```python
# Run with: xvfb-run -a python test.py
import asyncio
from playwright.async_api import async_playwright
async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width":540,"height":960}, device_scale_factor=2)
        await page.goto("file:///home/claude/animation.html")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="/home/claude/test.png", clip={"x":0,"y":0,"width":540,"height":960})
        await browser.close()
asyncio.run(test())
```

**Check:** PNG > 50KB = OK. If ~2-3KB = blank page = JS error.


---

## Step 4: Capture Frames

**Output: One GIF file per step.** If the JSX has N steps, produce N GIF files named `01_步骤名.gif`, `02_步骤名.gif`, etc.

Loop through each step separately, capturing frames for one step at a time:

```python
# Run with: xvfb-run -a python capture.py
for idx in range(num_steps):
    frames_dir = f"/home/claude/frames/step_{idx}"
    os.makedirs(frames_dir, exist_ok=True)
    
    # Switch step (restarts CSS animations)
    await page.evaluate(f"currentStep = {idx}; render();")
    await page.wait_for_timeout(300)
    
    for i in range(FPS * DURATION):
        if i % 20 == 0:
            await page.evaluate(f"currentStep = {idx};")
        await page.screenshot(path=f"{frames_dir}/frame_{i:05d}.png",
            type="png", clip={"x":0,"y":0,"width":540,"height":960})
        await page.wait_for_timeout(1000 // FPS)
    
    # Verify no drift
    assert await page.evaluate("currentStep") == idx
    
    # Encode THIS STEP's GIF
    # ... (see encoding command below)
    
    shutil.rmtree(frames_dir)
```

### Using bundled capture.py

```bash
xvfb-run -a python ${CLAUDE_PLUGIN_ROOT}/scripts/capture.py --html animation.html --output ./output --gif-only
```

### Parameters

| Parameter | Value |
|-----------|-------|
| Logical size | 540×960 (1080×1920 at 2x) |
| device_scale_factor | 2 |
| FPS | 12 (JS anim) / 15 (CSS anim) |
| Duration per step | Match original auto-advance |

---

## Step 5: Encode GIF

```bash
# Two-pass palette-optimized GIF
ffmpeg -y -framerate {FPS} -i frame_%05d.png \
  -vf "fps=10,palettegen=max_colors=128" palette.png
ffmpeg -y -framerate {FPS} -i frame_%05d.png -i palette.png \
  -lavfi "fps=10 [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3" output.gif
```

---

## Platform Guide

| Platform | Notes |
|----------|-------|
| 微信公众号 | GIF可作为图片插入 |
| 小红书 | 图文笔记中GIF自动播放 |
| X/Twitter | GIF自动循环播放 |

---

## DO NOT

- ❌ NEVER use sharp, puppeteer-core, node-canvas, or SVG-only rendering
- ❌ NEVER run Playwright without `xvfb-run -a`
- ❌ NEVER forget `playwright install chromium` at start
- ❌ NEVER rely on CDN (React, Tailwind, Babel, fonts)
- ❌ NEVER skip the test screenshot step
- ❌ NEVER output a single combined file — this skill produces SEPARATE files per step
