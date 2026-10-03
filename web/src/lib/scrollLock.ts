/**
 * Lock page scrolling while a modal (the menu) is open, including on iOS
 * Safari where `overflow: hidden` on <body> alone does not stop scrolling:
 * the body is fixed at the current offset and restored on unlock.
 */
let lockedAt: number | null = null;

export function lockScroll(): void {
  if (lockedAt !== null) return;
  lockedAt = window.scrollY;
  const { style } = document.body;
  style.position = 'fixed';
  style.top = `-${lockedAt}px`;
  style.left = '0';
  style.right = '0';
  style.overflow = 'hidden';
}

export function unlockScroll(): void {
  if (lockedAt === null) return;
  const { style } = document.body;
  style.position = '';
  style.top = '';
  style.left = '';
  style.right = '';
  style.overflow = '';
  window.scrollTo(0, lockedAt);
  lockedAt = null;
}
