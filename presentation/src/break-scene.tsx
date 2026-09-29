import { useEffect, useState } from "react"
import { useTerminalDimensions } from "@opentui/react"
import { colors as c } from "./theme"

export interface BreakSceneProps {
  playing: boolean
  fullscreen?: boolean
  remainingSeconds?: number | null
  editingMinutes?: boolean
  minutesInput?: string
  onMinutesInput?: (value: string) => void
}

export type Cell = { char: string; color: string }

export function useScene(playing: boolean, fullscreen: boolean) {
  const { width, height } = useTerminalDimensions()
  const [tick, setTick] = useState(0)
  useEffect(() => {
    if (!playing) return
    const timer = setInterval(() => setTick((value) => value + 1), 180)
    return () => clearInterval(timer)
  }, [playing])
  return {
    tick,
    sceneWidth: fullscreen ? Math.max(1, width - 4) : Math.max(1, Math.min(100, width - 10)),
    sceneHeight: fullscreen ? Math.max(1, height - 2) : Math.max(5, Math.min(14, height - 19)),
  }
}

export function makeCanvas(width: number, height: number, color: string) {
  const cells: Cell[][] = Array.from({ length: height }, () =>
    Array.from({ length: width }, () => ({ char: " ", color })))
  const put = (x: number, y: number, char: string, ink: string) => {
    const row = cells[y]
    if (x >= 0 && x < width && row) row[x] = { char, color: ink }
  }
  const draw = (x: number, y: number, text: string, ink: string) => {
    for (let i = 0; i < text.length; i++) put(x + i, y, text.charAt(i), ink)
  }
  return { cells, put, draw }
}

export function SceneFrame({ cells, background, border, fullscreen = false, playing, remainingSeconds = null,
  editingMinutes = false, minutesInput = "10", onMinutesInput, title }: BreakSceneProps & {
    cells: Cell[][]; background: string; border: string; title: string
  }) {
  const width = cells[0]?.length ?? 0
  const height = cells.length
  const header = cells[0]
  const footer = cells[height - 1]
  if (fullscreen && header && footer) {
    const clock = remainingSeconds === null ? "T: sett nedtelling" : remainingSeconds === 0 ? "PAUSEN ER OVER!" :
      `TID IGJEN ${String(Math.floor(remainingSeconds / 60)).padStart(2, "0")}:${String(remainingSeconds % 60).padStart(2, "0")}`
    const label = `  ${title} · ${clock} · ${playing ? "i bevegelse" : "på pause"}  `
    const controls = `Esc tilbake · A/S bytt · T tid · P ${playing ? "pause" : "spill"} · R nullstill · Q avslutt`
    for (let x = 0; x < width; x++) header[x] = { char: " ", color: border }
    for (let x = 0; x < label.length && x < width; x++) header[x] = { char: label.charAt(x), color: remainingSeconds === 0 ? c.error : border }
    for (let x = 0; x < controls.length && x + 2 < width; x++) footer[x + 2] = { char: controls.charAt(x), color: c.muted }
    if (remainingSeconds === 0) {
      const message = "*** PAUSEN ER OVER! ***"
      const x = Math.floor((width - message.length) / 2)
      const middle = cells[Math.floor(height / 2)]
      for (let i = 0; i < message.length; i++) {
        if (middle && x + i >= 0 && x + i < width) middle[x + i] = { char: message.charAt(i), color: c.error }
      }
    }
  }

  const rows = cells.map((row) => row.reduce<{ text: string; color: string }[]>((runs, cell) => {
    const last = runs.at(-1)
    if (last?.color === cell.color) last.text += cell.char
    else runs.push({ text: cell.char, color: cell.color })
    return runs
  }, []))

  return <box border borderStyle="rounded" borderColor={border} backgroundColor={background}
    width={width + 4} paddingX={1} flexDirection="column" flexShrink={0}>
    {rows.map((row, y) => fullscreen && editingMinutes && y === 0 ?
      <box key={y} flexDirection="row" height={1} flexShrink={0}>
        <text fg={border}>  MINUTTER (1–999): </text>
        <input value={minutesInput} onInput={onMinutesInput} focused width={5} maxLength={3}
          textColor={c.ink} backgroundColor={c.purple} cursorColor={border} />
        <text fg={c.muted}> Enter start · Esc avbryt</text>
      </box> : <text key={y} flexShrink={0}>
        {row.map((run, x) => <span key={x} fg={run.color}>{run.text}</span>)}
      </text>)}
  </box>
}
