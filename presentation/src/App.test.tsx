import { expect, test } from "bun:test";
import { testRender } from "@opentui/react/test-utils";
import { act } from "react";
import { App } from "./App";

const curiousHeader = "█▀▀ █ █ █▀█"; // First row of the ASCII heading

test("title slide fits an 80x24 terminal", async () => {
  const setup = await testRender(<App />, { width: 80, height: 24 });
  try {
    await setup.renderOnce();
    const frame = setup.captureCharFrame();
    expect(frame).toContain("█████╗"); // Large title
    expect(frame).toContain("▟▀█"); // Ø in «første»
    expect(frame).toContain("█▀█"); // Small ASCII-font subtitle
    expect(frame.trimEnd().split("\n").length).toBeLessThanOrEqual(24);
  } finally {
    await act(async () => setup.renderer.destroy());
  }
});

test("navigate slides without entering either break screen", async () => {
  const setup = await testRender(<App />, { width: 80, height: 24 });
  try {
    await act(async () => setup.mockInput.pressArrow("right"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain(curiousHeader);
    expect(setup.captureCharFrame()).not.toContain("PAUSE");

    await act(async () => setup.mockInput.pressArrow("right"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain(curiousHeader);

    await act(async () => setup.mockInput.pressArrow("left"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("▟▀█");
  } finally {
    await act(async () => setup.renderer.destroy());
  }
});

test("break keys switch scenes and return to the current slide with the timer preserved", async () => {
  const setup = await testRender(<App />, { width: 80, height: 24, kittyKeyboard: true });
  try {
    await act(async () => setup.mockInput.pressArrow("right"));
    await setup.renderOnce();
    await act(async () => setup.mockInput.pressKey("a"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("PAUSE");
    expect(setup.captureCharFrame()).toContain("T: sett nedtelling");

    await act(async () => setup.mockInput.pressArrow("right"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("PAUSE");

    await act(async () => setup.mockInput.pressKey("t"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("MINUTTER (1–999):");
    await act(async () => setup.mockInput.pressEnter());
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("TID IGJEN 10:00");

    await act(async () => setup.mockInput.pressKey("p"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("på pause");

    await act(async () => setup.mockInput.pressKey("s"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("ROMFERD");
    expect(setup.captureCharFrame()).toContain("TID IGJEN 10:00");
    expect(setup.captureCharFrame()).toContain("|__  []   _>");

    await act(async () => setup.mockInput.pressKey("s"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain(curiousHeader);
    await act(async () => setup.mockInput.pressKey("a"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("TID IGJEN 10:00");

    await act(async () => setup.mockInput.pressKey("r"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("T: sett nedtelling");

    await act(async () => setup.mockInput.pressKey("a"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain(curiousHeader);

    await act(async () => setup.mockInput.pressKey("a"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("PAUSE");
    await act(async () => setup.mockInput.pressKey("a"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain(curiousHeader);

    await act(async () => setup.mockInput.pressKey("s"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("ROMFERD");
    await act(async () => setup.mockInput.pressEscape());
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain(curiousHeader);

    await act(async () => setup.mockInput.pressArrow("left"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("▟▀█");
  } finally {
    await act(async () => setup.renderer.destroy());
  }
});

test("a break opened from the title returns to the title", async () => {
  const setup = await testRender(<App />, { width: 80, height: 24, kittyKeyboard: true });
  try {
    await act(async () => setup.mockInput.pressKey("s"));
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("ROMFERD");
    await act(async () => setup.mockInput.pressEscape());
    await setup.renderOnce();
    expect(setup.captureCharFrame()).toContain("▟▀█");
  } finally {
    await act(async () => setup.renderer.destroy());
  }
});
