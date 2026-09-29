import { makeCanvas, SceneFrame, useScene, type BreakSceneProps } from "./break-scene"
import { colors as c } from "./theme"

const swimmers = [
  ["><(((°>", "<°)))><"],
  ["><>", "<><"],
  [">==°>", "<°==<"],
]

export function FishTank(props: BreakSceneProps) {
  const { tick, sceneWidth: width, sceneHeight: height } = useScene(props.playing, props.fullscreen ?? false)
  const { cells, put } = makeCanvas(width, height, c.ink)

  const plants = Math.max(3, Math.floor(width / 15))
  for (let i = 0; i < plants; i++) {
    const x = Math.floor((i + 0.5) * width / plants)
    for (let j = 0; j < 4; j++) {
      const y = height - 1 - j
      put(x + (j === 3 ? Math.round(Math.sin(tick / 5 + i)) : 0), y, j === 3 ? "Y" : "|", c.success)
    }
    for (let j = 0; j < 4; j++) {
      const y = height - 5 - ((tick * (1 + i % 2) + j * 5 + i * 3) % Math.max(1, height - 5))
      put(x + (j % 2 ? 1 : -1), y, j % 3 ? "°" : "o", c.muted)
    }
  }

  const fishCount = Math.max(7, Math.min(18, Math.floor(width * height / 190)))
  for (let i = 0; i < fishCount; i++) {
    const direction = i % 2
    const shape = swimmers[i % swimmers.length]?.[direction] ?? "><>"
    const speed = 1 + i % 3
    const path = width + shape.length
    const offset = (tick * speed + i * Math.floor(path / fishCount)) % path
    const x = direction ? width - offset : offset - shape.length
    const baseY = 2 + Math.floor(i * Math.max(1, height - 5) / fishCount)
    const y = Math.max(1, Math.min(height - 3, baseY + Math.round(Math.sin(tick / (4 + i % 5) + i) * 2)))
    for (let j = 0; j < shape.length; j++) put(x + j, y, shape.charAt(j), i % 3 === 1 ? c.pink : c.accent)
  }

  const crab = tick % (2 * width)
  const crabX = crab < width ? crab : 2 * width - crab
  const crabShape = tick % 2 ? "\\(°)/" : "\\(o)/"
  for (let i = 0; i < crabShape.length; i++) put(crabX + i, height - 2, crabShape.charAt(i), c.pink)

  return <SceneFrame {...props} cells={cells} background={c.panel} border={c.accent} title="PAUSE" />
}
