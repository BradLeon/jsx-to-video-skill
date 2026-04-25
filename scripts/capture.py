#!/usr/bin/env python3
"""
JSX-to-Video Capture Script
Captures frames from a rendered HTML animation using Playwright,
then encodes them to MP4 and GIF using ffmpeg.

Usage:
  xvfb-run -a python capture.py --html animation.html --output ./output
  xvfb-run -a python capture.py --html animation.html --output ./output
  # Per-step output is DEFAULT. Use --combined for single file.

Required: playwright, ffmpeg, xvfb (all pre-installed in Claude's environment)
"""

import asyncio
import argparse
import subprocess
import os
import shutil
import json
from playwright.async_api import async_playwright


def parse_args():
    p = argparse.ArgumentParser(description="Capture HTML animation as MP4/GIF")
    p.add_argument("--html", required=True, help="Path to the HTML animation file")
    p.add_argument("--output", required=True, help="Output directory for MP4/GIF files")
    p.add_argument("--width", type=int, default=540, help="Logical viewport width (default: 540)")
    p.add_argument("--height", type=int, default=960, help="Logical viewport height (default: 960)")
    p.add_argument("--scale", type=int, default=2, help="Device scale factor (default: 2, output = width*scale x height*scale)")
    p.add_argument("--fps", type=int, default=12, help="Frames per second (default: 12)")
    p.add_argument("--step-duration", type=int, default=5, help="Seconds per step (default: 5)")
    p.add_argument("--combined", action="store_true", help="Output one combined file instead of per-step files")
    p.add_argument("--steps", type=int, default=None, help="Number of steps (auto-detected if not set)")
    p.add_argument("--step-names", type=str, default=None, help="JSON array of step names, e.g. '[\"step1\",\"step2\"]'")
    p.add_argument("--gif-only", action="store_true", help="Only produce GIF output")
    p.add_argument("--mp4-only", action="store_true", help="Only produce MP4 output")
    p.add_argument("--gif-fps", type=int, default=None, help="GIF frame rate (default: min(fps, 10))")
    p.add_argument("--crf", type=int, default=20, help="MP4 quality (lower=better, default: 20)")
    return p.parse_args()


def encode_mp4(frames_dir, output_path, fps, crf=20):
    """Encode a PNG sequence to H.264 MP4."""
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", str(crf),
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        output_path
    ], check=True, capture_output=True)
    return os.path.getsize(output_path)


def encode_gif(frames_dir, output_path, fps, gif_fps=None):
    """Encode a PNG sequence to palette-optimized GIF."""
    gif_fps = gif_fps or min(fps, 10)
    palette = os.path.join(frames_dir, "_palette.png")

    # Pass 1: Generate optimal palette
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-vf", f"fps={gif_fps},palettegen=max_colors=128",
        palette
    ], check=True, capture_output=True)

    # Pass 2: Encode with palette
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-i", palette,
        "-lavfi", f"fps={gif_fps} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3",
        output_path
    ], check=True, capture_output=True)

    os.remove(palette)
    return os.path.getsize(output_path)


async def capture_frames(page, frames_dir, num_frames, fps, logical_w, logical_h, step_idx=None):
    """Capture a sequence of PNG frames from the page."""
    os.makedirs(frames_dir, exist_ok=True)
    interval_ms = 1000 // fps

    for i in range(num_frames):
        # If capturing a specific step, keep it locked
        if step_idx is not None and i % 20 == 0:
            await page.evaluate(f"currentStep = {step_idx};")

        path = os.path.join(frames_dir, f"frame_{i:05d}.png")
        await page.screenshot(
            path=path, type="png",
            clip={"x": 0, "y": 0, "width": logical_w, "height": logical_h}
        )
        await page.wait_for_timeout(interval_ms)


async def main():
    args = parse_args()

    html_path = os.path.abspath(args.html)
    output_dir = os.path.abspath(args.output)
    frames_base = os.path.join(output_dir, "_frames")
    frames_per_step = args.step_duration * args.fps
    do_mp4 = not args.gif_only
    do_gif = not args.mp4_only

    os.makedirs(output_dir, exist_ok=True)

    # Parse step names if provided
    step_names = None
    if args.step_names:
        step_names = json.loads(args.step_names)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=args.scale
        )

        await page.goto(f"file://{html_path}")
        await page.wait_for_timeout(3000)

        # Auto-detect number of steps if not provided
        num_steps = args.steps
        if num_steps is None:
            try:
                num_steps = await page.evaluate("typeof STEPS !== 'undefined' ? STEPS.length : 1")
            except:
                num_steps = 1

        print(f"Config: {args.width}x{args.height} @{args.scale}x = {args.width*args.scale}x{args.height*args.scale}")
        print(f"Steps: {num_steps}, FPS: {args.fps}, Duration/step: {args.step_duration}s")
        print(f"Per-step output: {not args.combined}, Formats: {'MP4' if do_mp4 else ''} {'GIF' if do_gif else ''}")

        if not args.combined and num_steps > 1:
            # === Per-step capture ===
            for step_idx in range(num_steps):
                name = step_names[step_idx] if step_names and step_idx < len(step_names) else f"step_{step_idx+1:02d}"
                step_frames = os.path.join(frames_base, f"step_{step_idx:02d}")

                # Lock to this step
                await page.evaluate(f"currentStep = {step_idx}; render();")
                await page.wait_for_timeout(300)

                print(f"[{step_idx+1}/{num_steps}] {name} ({frames_per_step} frames)...")

                await capture_frames(page, step_frames, frames_per_step, args.fps,
                                     args.width, args.height, step_idx=step_idx)

                # Verify step didn't change
                cur = await page.evaluate("currentStep")
                if cur != step_idx:
                    print(f"  WARNING: step drifted to {cur}, expected {step_idx}")

                if do_mp4:
                    mp4_path = os.path.join(output_dir, f"{name}.mp4")
                    sz = encode_mp4(step_frames, mp4_path, args.fps, args.crf)
                    print(f"  MP4: {sz/1024:.0f} KB")

                if do_gif:
                    gif_path = os.path.join(output_dir, f"{name}.gif")
                    sz = encode_gif(step_frames, gif_path, args.fps, args.gif_fps)
                    print(f"  GIF: {sz/1024:.0f} KB")

                shutil.rmtree(step_frames)
        else:
            # === Combined capture ===
            total_frames = frames_per_step * num_steps
            combined_frames = os.path.join(frames_base, "combined")

            # Enable auto-advance for combined mode
            try:
                await page.evaluate("window.autoAdvance = true; currentStep = 0; render();")
            except:
                pass
            await page.wait_for_timeout(300)

            print(f"Capturing {total_frames} frames ({args.step_duration * num_steps}s total)...")
            await capture_frames(page, combined_frames, total_frames, args.fps,
                                 args.width, args.height, step_idx=None)

            if do_mp4:
                mp4_path = os.path.join(output_dir, "animation.mp4")
                sz = encode_mp4(combined_frames, mp4_path, args.fps, args.crf)
                print(f"MP4: {sz/1024:.0f} KB")

            if do_gif:
                gif_path = os.path.join(output_dir, "animation.gif")
                sz = encode_gif(combined_frames, gif_path, args.fps, args.gif_fps)
                print(f"GIF: {sz/1024:.0f} KB")

            shutil.rmtree(combined_frames)

        await browser.close()

    # Cleanup
    if os.path.exists(frames_base):
        shutil.rmtree(frames_base)

    # Summary
    outputs = [f for f in os.listdir(output_dir) if not f.startswith("_")]
    print(f"\n✅ Done! {len(outputs)} files in {output_dir}/")
    for f in sorted(outputs):
        sz = os.path.getsize(os.path.join(output_dir, f))
        print(f"  {f} ({sz/1024:.0f} KB)")


if __name__ == "__main__":
    asyncio.run(main())
