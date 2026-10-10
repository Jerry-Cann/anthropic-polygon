# Panel, Brick, Glass

An animated, side-by-side explainer comparing three kinds of apartment building:

- **Panelka**: Soviet and Eastern Bloc large-panel prefab blocks, 1959–1990s
- **Brick block**: load-bearing masonry such as the Stalinka, 1930s–1950s
- **Glass & panel**: a modern concrete frame with a curtain wall and cladding panels, 2000s to today

Nine chapters animate the same three buildings on one street:

1. Meet the buildings
2. Construction speed
3. Load paths
4. Winter heat loss (thermal camera)
5. Summer overheating
6. Sound between flats
7. Floor plans and ceiling heights
8. Ageing over 120 years
9. Earthquake response

A comparison table and lists of strengths and weaknesses follow below the animation.

## Run it

Open `index.html` in a browser. It is a single file with no build step. It loads Google Fonts and falls back to system fonts when offline.

The file is written as a page body without `<!doctype>`/`<html>` tags so it can be published as a claude.ai Artifact. Browsers render it as-is.

Controls:

- The chapter tabs, or ← / → when the tab bar has focus, switch chapters.
- **Pause** / **Play** stops and restarts the animation.
- The slider scrubs within a chapter.
- **Play all chapters** runs the whole tour.

You can link to a chapter with a hash, for example `index.html#winter`. The page respects `prefers-reduced-motion` and follows the light/dark theme. Dark mode turns the street scene into evening.

## About the numbers

Figures are typical ranges for buildings as originally built, rounded for teaching. Build speeds, sound values, cost indices and embodied-carbon ranges are indicative estimates. The summer temperatures come from an illustrative model, not from measurements. Sources and caveats are listed at the bottom of the page.
