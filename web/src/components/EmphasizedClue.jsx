import React from "react";

export function EmphasizedClue({ text, people, areas }) {
  const names = [...people.map((p) => p.name), ...areas.map((a) => a.name)];
  const expression = new RegExp(
    `(${names
      .sort((a, b) => b.length - a.length)
      .map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join("|")})`,
    "g",
  );
  return text
    .split(expression)
    .map((part, i) =>
      names.includes(part) ? <strong key={i}>{part}</strong> : part,
    );
}
