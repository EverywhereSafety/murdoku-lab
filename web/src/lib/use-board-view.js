import { useEffect, useLayoutEffect, useRef } from "react";

export function useBoardNavigation({ zoom, setZoom, sessionId, onPinch }) {
  const pinchStart = useRef(onPinch);
  pinchStart.current = onPinch;
  const scrollRef = useRef(null);
  const zoomAnchor = useRef(null);
  const zoomRef = useRef(zoom);
  zoomRef.current = zoom;
  const changeZoom = (next, clientX, clientY) => {
    const board = scrollRef.current;
    const value = Math.max(75, Math.min(250, Math.round(next)));
    if (!board || value === zoomRef.current) return;
    const box = board.getBoundingClientRect();
    const x = clientX == null ? board.clientWidth / 2 : clientX - box.left;
    const y = clientY == null ? board.clientHeight / 2 : clientY - box.top;
    zoomAnchor.current = {
      left: ((board.scrollLeft + x) * value) / zoomRef.current - x,
      top: ((board.scrollTop + y) * value) / zoomRef.current - y,
    };
    zoomRef.current = value;
    setZoom(value);
  };
  useLayoutEffect(() => {
    if (zoomAnchor.current && scrollRef.current) {
      scrollRef.current.scrollLeft = zoomAnchor.current.left;
      scrollRef.current.scrollTop = zoomAnchor.current.top;
      zoomAnchor.current = null;
    }
  }, [zoom]);
  useEffect(() => {
    const board = scrollRef.current;
    if (!board) return;
    let pinch = null;
    const wheel = (event) => {
      if (!event.ctrlKey && !event.metaKey) return;
      event.preventDefault();
      changeZoom(
        zoomRef.current * Math.exp(-event.deltaY * 0.005),
        event.clientX,
        event.clientY,
      );
    };
    const start = (event) => {
      if (event.touches.length !== 2) return;
      pinchStart.current?.();
      const [a, b] = event.touches;
      pinch = {
        distance: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY),
        zoom: zoomRef.current,
      };
    };
    const move = (event) => {
      if (!pinch || event.touches.length !== 2) return;
      event.preventDefault();
      const [a, b] = event.touches;
      const distance = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
      if (pinch.distance > 0)
        changeZoom(
          (pinch.zoom * distance) / pinch.distance,
          (a.clientX + b.clientX) / 2,
          (a.clientY + b.clientY) / 2,
        );
    };
    const end = () => {
      pinch = null;
    };
    board.addEventListener("wheel", wheel, { passive: false });
    board.addEventListener("touchstart", start, { passive: true });
    board.addEventListener("touchmove", move, { passive: false });
    board.addEventListener("touchend", end);
    board.addEventListener("touchcancel", end);
    return () => {
      board.removeEventListener("wheel", wheel);
      board.removeEventListener("touchstart", start);
      board.removeEventListener("touchmove", move);
      board.removeEventListener("touchend", end);
      board.removeEventListener("touchcancel", end);
    };
  }, [sessionId, setZoom]);
  const fitBoard = () => {
    scrollRef.current.scrollTo(0, 0);
    zoomAnchor.current = null;
    setZoom(100);
  };
  return { scrollRef, changeZoom, fitBoard };
}

export function useBoardGuides({ sceneRef, hoverInfo, boardMarkup, state }) {
  useEffect(() => {
    const svgNode = sceneRef.current?.querySelector("svg");
    if (!svgNode) return;
    svgNode.querySelector("[data-hover-guide]")?.remove();
    svgNode
      .querySelectorAll("[data-axis-active]")
      .forEach((node) => node.removeAttribute("data-axis-active"));
    if (!hoverInfo) return;
    const hit = svgNode.querySelector(`[data-cell="${hoverInfo.cell}"] rect`);
    if (!hit) return;
    const ns = "http://www.w3.org/2000/svg";
    const group = document.createElementNS(ns, "g");
    group.setAttribute("data-hover-guide", "true");
    group.setAttribute("pointer-events", "none");
    group.setAttribute("aria-hidden", "true");
    const x = Number(hit.getAttribute("x")) - 3;
    const y = Number(hit.getAttribute("y")) - 3;
    for (const [rx, ry, width, height] of [
      [40, y, state.scene.width * 100, 100],
      [x, 40, 100, state.scene.height * 100],
    ]) {
      const rect = document.createElementNS(ns, "rect");
      for (const [key, value] of Object.entries({
        x: rx,
        y: ry,
        width,
        height,
        fill: "#527d6810",
        stroke: "#356e55",
        "stroke-width": 2,
      }))
        rect.setAttribute(key, value);
      group.append(rect);
    }
    svgNode.append(group);
    for (const node of svgNode.querySelectorAll("text")) {
      if (
        (Number(node.getAttribute("x")) === 20 &&
          node.textContent === String(hoverInfo.row + 1)) ||
        (Number(node.getAttribute("y")) === 25 &&
          node.textContent === String.fromCharCode(65 + hoverInfo.col))
      )
        node.setAttribute("data-axis-active", "true");
    }
  }, [hoverInfo, boardMarkup, state.scene, sceneRef]);
}
