import { useEffect, useState } from "react";
import { useKeyboard, useRenderer, useTerminalDimensions } from "@opentui/react";
import { FishTank } from "./fish-tank";
import { SpaceScene } from "./space-scene";

function TitleSlide() {
  return (
    <box width="100%" height="100%" flexDirection="column" alignItems="center">
      <box flexGrow={1} flexDirection="column" alignItems="center" justifyContent="center">
        <box flexDirection="column" alignItems="center" gap={1}>
          <ascii-font font="block" text="Agentisk" color="#F2F5FA" />
          <ascii-font font="block" text="utvikling" color="#F2F5FA" />
        </box>
        <box flexDirection="column" alignItems="center" marginTop={1} gap={1}>
          <box flexDirection="row">
            <ascii-font font="tiny" text="Fra f" color="#66D9EF" />
            {/* The bundled ASCII fonts have no Ø glyph. */}
            <text fg="#66D9EF" width={5} height={2} content={" ▟▀█ \n █▄▜ "} />
            <ascii-font font="tiny" text="rste agent til" color="#66D9EF" />
          </box>
          <ascii-font font="tiny" text="parallelle" color="#66D9EF" />
          <ascii-font font="tiny" text="arbeidsflyter" color="#66D9EF" />
        </box>
      </box>
      <text fg="#8993A4">→/Space neste · A akvarium · S romferd · Q avslutt</text>
    </box>
  );
}

function CuriousSlide({ width, height }: { width: number; height: number }) {
  const imageWidth = Math.max(1, Math.min(Math.floor(width * 0.55), Math.floor((height - 11) * 8 / 3)));
  const imageHeight = Math.max(1, Math.min(height - 11, Math.round(imageWidth * 3 / 8)));
  return (
    <box width="100%" height="100%" flexDirection="column" alignItems="center">
      <box flexGrow={1} flexDirection="column" alignItems="center" justifyContent="center" gap={1}>
        <box flexDirection="column" alignItems="center">
          <ascii-font font="tiny" text="Curious, Not" color="#F2F5FA" />
          <ascii-font font="tiny" text="Converted" color="#F2F5FA" />
        </box>
        <image source={new URL("../images/absolutes.JPG", import.meta.url).pathname}
          width={imageWidth} height={imageHeight} fit="fit" />
      </box>
      <text fg="#8993A4">← forrige · A akvarium · S romferd · Q avslutt</text>
    </box>
  );
}

export function App() {
  const renderer = useRenderer();
  const { width, height } = useTerminalDimensions();
  const [slide, setSlide] = useState(0); // Title, Curious
  const [breakScene, setBreakScene] = useState<"aquarium" | "spaceship" | null>(null);
  const [playing, setPlaying] = useState(false);
  const [editingMinutes, setEditingMinutes] = useState(false);
  const [minutesInput, setMinutesInput] = useState("10");
  const [deadline, setDeadline] = useState<number | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null);

  useEffect(() => {
    if (deadline === null) return;
    const update = () => {
      const seconds = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
      setRemainingSeconds(seconds);
      if (seconds === 0) clearInterval(timer);
    };
    const timer = setInterval(update, 250);
    update();
    return () => clearInterval(timer);
  }, [deadline]);

  function toggleBreak(scene: "aquarium" | "spaceship") {
    setBreakScene(breakScene === scene ? null : scene);
    setPlaying(breakScene !== scene);
    setEditingMinutes(false);
  }

  useKeyboard((key) => {
    if (editingMinutes) {
      if (key.name === "escape") {
        key.preventDefault();
        setEditingMinutes(false);
      } else if (key.name === "return" || key.name === "enter") {
        key.preventDefault();
        const minutes = Number(minutesInput);
        if (Number.isInteger(minutes) && minutes >= 1 && minutes <= 999) {
          setDeadline(Date.now() + minutes * 60_000);
          setRemainingSeconds(minutes * 60);
          setEditingMinutes(false);
        }
      }
      return; // Leave digit and backspace input to the focused input.
    }
    if (key.name === "q") {
      key.preventDefault();
      renderer.destroy();
    } else if (key.name === "a" || key.name === "s") {
      key.preventDefault();
      toggleBreak(key.name === "a" ? "aquarium" : "spaceship");
    } else if (breakScene !== null && key.name === "escape") {
      key.preventDefault();
      setBreakScene(null);
      setPlaying(false);
    } else if (breakScene !== null && key.name === "p") {
      key.preventDefault();
      setPlaying((value) => !value);
    } else if (breakScene !== null && key.name === "t") {
      key.preventDefault();
      setEditingMinutes(true);
    } else if (breakScene !== null && key.name === "r") {
      key.preventDefault();
      setDeadline(null);
      setRemainingSeconds(null);
      setMinutesInput("10");
      setPlaying(true);
    } else if (breakScene === null && (key.name === "right" || key.name === "space" || key.name === "return" || key.name === "enter")) {
      key.preventDefault();
      setSlide((value) => Math.min(1, value + 1));
    } else if (breakScene === null && key.name === "left") {
      key.preventDefault();
      setSlide((value) => Math.max(0, value - 1));
    }
  });

  if (breakScene === null && slide === 0) return <TitleSlide />;
  if (width < 40 || height < 10) {
    return <text>Gjør terminalen større (minst 40 × 10).</text>;
  }
  if (breakScene === null) return <CuriousSlide width={width} height={height} />;

  const props = {
    playing,
    fullscreen: true,
    remainingSeconds,
    editingMinutes,
    minutesInput,
    onMinutesInput: (value: string) => setMinutesInput(value.replace(/\D/g, "").slice(0, 3)),
  };
  return breakScene === "aquarium" ? <FishTank {...props} /> : <SpaceScene {...props} />;
}
