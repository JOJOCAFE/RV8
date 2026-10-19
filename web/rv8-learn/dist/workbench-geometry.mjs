export const WIDTH = 880;
export const HEIGHT = 440;

export function constrainPartPosition(x, y, { snap = false } = {}) {
  if (snap) {
    x = Math.round(x / 10) * 10;
    y = Math.round(y / 10) * 10;
  }
  return {
    x: Math.max(24, Math.min(WIDTH - 176, x)),
    y: Math.max(28, Math.min(HEIGHT - 140, y)),
  };
}
