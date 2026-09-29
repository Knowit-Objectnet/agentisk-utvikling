import { makeCanvas, SceneFrame, useScene, type BreakSceneProps } from "./break-scene"
import { colors as c } from "./theme"

const ship = [
  "    /\\",
  " __/==\\____",
  "|__  []   _>",
  "   \\____/",
]

const planet = [
  "  .---.  ",
  " / o   \\",
  "|   o   |",
  " \\_____/ ",
]

export function SpaceScene(props: BreakSceneProps) {
  const { tick, sceneWidth: width, sceneHeight: height } = useScene(props.playing, props.fullscreen ?? false)
  const { cells, put, draw } = makeCanvas(width, height, c.background)

  // Different parallax speeds make the ship appear to travel even while it stays in view.
  const stars = Math.floor(width * height / 20)
  for (let i = 0; i < stars; i++) {
    const speed = 1 + i % 3
    const x = ((i * 47 + 13 - Math.floor(tick * speed / 2)) % width + width) % width
    const y = 1 + ((i * 29 + Math.floor(i / 5)) % Math.max(1, height - 2))
    put(x, y, i % 8 === 0 ? "+" : i % 3 === 0 ? "*" : ".", i % 3 === 0 ? c.purple : c.muted)
  }

  const planetX = width - 16 - (Math.floor(tick / 4) % (width + 10))
  const planetY = Math.max(2, Math.floor(height / 4) - 2)
  planet.forEach((line, y) => draw(planetX, planetY + y, line, c.pink))
  for (let i = 0; i < 5; i++) {
    const x = width - ((tick * 3 + i * 3) % (width + 12))
    put(x, Math.max(2, height - 6 - Math.floor(tick / 12) % 3), i === 0 ? "@" : "·", c.accent)
  }

  const shipX = Math.floor(width / 3) + Math.round(Math.sin(tick / 9) * 2)
  const shipY = Math.max(2, Math.floor(height / 2) - 2 + Math.round(Math.sin(tick / 7)))
  ship.forEach((line, y) => draw(shipX, shipY + y, line, c.accent))
  const flame = tick % 3 === 0 ? "<~~~" : tick % 3 === 1 ? " <~~" : "  <~"
  draw(shipX - 4, shipY + 2, flame, c.pink)

  return <SceneFrame {...props} cells={cells} background={c.ink} border={c.purple} title="ROMFERD" />
}
