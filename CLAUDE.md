# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a static, single-page educational website: **"Shark Attack! — Scratch Game Academy"**. It teaches Year 7 students (Haute Vallée School) how to build a Scratch 3.0 ocean survival game across 6 lessons. The page is designed by Dr Galan for Coderra.je.

## Architecture

- **Single file**: `index.html` (~1600 lines) contains all HTML, CSS, and JavaScript inline — no build tools, no dependencies, no external CSS/JS files.
- **CSS**: Custom properties (CSS variables) in `:root` for theming (ocean/dark theme). Responsive via media queries at 600px breakpoint.
- **JavaScript**: Minimal — a single `go(n)` function handles accordion-style lesson toggling. Lesson 1 auto-opens on page load.
- **Design system**: Uses Fredoka One + Nunito fonts via Google Fonts. Color palette: teal/coral/ocean-dark. Scratch-style block notation (`.sb` classes) for representing Scratch blocks.

## Development

No build step. Open `index.html` directly in a browser or serve with any static server:

```
python3 -m http.server 8000
```

## Content Structure

The page has 6 lesson sections (`#l1` through `#l6`), each progressively building the game:
1. Shark movement + first fish
2. Score, lives, game over mechanics
3. Multiple fish types + golden fish
4. Enemies (jellyfish, mines, pufferfish)
5. Levels, backdrops, difficulty scaling
6. Polish — health bar, sound, particles, sharing

Each lesson uses Scratch block notation (`.sb` divs with color classes like `.sb-motion`, `.sb-ctrl`, `.sb-look`) to visually represent Scratch code blocks.

## Conventions

- Scratch blocks use indentation classes `.i1` through `.i4` for nesting depth
- Variable cards use `.vc-*` color classes matching variable purpose
- Lesson articles use `.lesson` class with `id="l{n}"` pattern
- The sticky progress nav (`.progress-nav`) links to lessons via `onclick="go(n)"`
