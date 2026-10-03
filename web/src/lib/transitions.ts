/**
 * UI transitions. Durations collapse to 0 when the user prefers reduced motion.
 */
import { cubicOut } from 'svelte/easing';
import { prefersReducedMotion } from 'svelte/motion';
import type { TransitionConfig } from 'svelte/transition';

/** Scale to use for a duration, honouring `prefers-reduced-motion`. */
export function motion(duration: number): number {
  return prefersReducedMotion.current ? 0 : duration;
}

/** A tile arriving "from the back": grows from 92 % while fading in and rising slightly. */
export function arrive(
  _node: Element,
  { delay = 0, duration = 280 }: { delay?: number; duration?: number } = {},
): TransitionConfig {
  return {
    delay: motion(delay),
    duration: motion(duration),
    easing: cubicOut,
    css: (t) =>
      `opacity: ${t}; transform: translateY(${(1 - t) * 14}px) scale(${0.92 + 0.08 * t});`,
  };
}

/** A tile leaving: quick fade and slight shrink toward the back. */
export function leave(_node: Element, { duration = 140 }: { duration?: number } = {}): TransitionConfig {
  return {
    duration: motion(duration),
    easing: cubicOut,
    css: (t) => `opacity: ${t}; transform: scale(${0.96 + 0.04 * t});`,
  };
}
