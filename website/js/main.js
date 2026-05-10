/* Pi IoT Academy — student progress tracking + small UI helpers.
   Progress is stored per phase in localStorage so a student can leave
   and come back to the same place in a lesson. */

(() => {
  'use strict';

  const STORAGE_KEY = 'pi-iot-academy:progress';

  function loadProgress() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch {
      return {};
    }
  }

  function saveProgress(progress) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
    } catch {
      // Storage might be disabled (private mode). Fail quietly.
    }
  }

  /* ----------------------------- Checkpoints ---------------------------- */

  function setupCheckpoints() {
    const checks = document.querySelectorAll('.checkpoint input[type="checkbox"][data-key]');
    if (!checks.length) return;

    const phase = document.body.dataset.phase || 'unknown';
    const progress = loadProgress();
    const phaseProgress = progress[phase] || {};

    checks.forEach((box) => {
      const key = box.dataset.key;
      if (phaseProgress[key]) box.checked = true;

      box.addEventListener('change', () => {
        const current = loadProgress();
        current[phase] = current[phase] || {};
        if (box.checked) {
          current[phase][key] = true;
        } else {
          delete current[phase][key];
        }
        saveProgress(current);
        updateProgressPill();
        updateNextButton();
      });
    });

    updateProgressPill();
    updateNextButton();
  }

  function updateProgressPill() {
    const pill = document.querySelector('[data-progress-pill]');
    if (!pill) return;

    const phase = document.body.dataset.phase;
    const total = document.querySelectorAll('.checkpoint input[type="checkbox"][data-key]').length;
    if (!total) {
      pill.textContent = '';
      return;
    }

    const progress = loadProgress();
    const done = Object.keys(progress[phase] || {}).length;
    pill.textContent = `${done} / ${total} done`;
  }

  function updateNextButton() {
    const btn = document.querySelector('[data-require-all-checked]');
    if (!btn) return;

    const total = document.querySelectorAll('.checkpoint input[type="checkbox"][data-key]').length;
    const phase = document.body.dataset.phase;
    const progress = loadProgress();
    const done = Object.keys(progress[phase] || {}).length;

    if (done >= total && total > 0) {
      btn.classList.remove('disabled');
      btn.removeAttribute('aria-disabled');
    } else {
      btn.classList.add('disabled');
      btn.setAttribute('aria-disabled', 'true');
    }
  }

  /* ----------------------------- Copy buttons --------------------------- */

  function setupCopyButtons() {
    document.querySelectorAll('.copy-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const target = btn.closest('.code-block')?.querySelector('pre code');
        if (!target) return;

        const text = target.innerText;
        const original = btn.textContent;

        try {
          await navigator.clipboard.writeText(text);
          btn.textContent = 'Copied';
          btn.classList.add('copied');
        } catch {
          btn.textContent = 'Press Ctrl+C';
        }

        setTimeout(() => {
          btn.textContent = original;
          btn.classList.remove('copied');
        }, 1600);
      });
    });
  }

  /* ----------------------------- TOC active state ----------------------- */

  function setupTocHighlight() {
    const links = document.querySelectorAll('.toc a[href^="#"]');
    if (!links.length) return;

    const targets = Array.from(links)
      .map((link) => document.querySelector(link.getAttribute('href')))
      .filter(Boolean);

    if (!targets.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const id = entry.target.id;
          links.forEach((l) => l.classList.toggle('is-active', l.getAttribute('href') === `#${id}`));
        });
      },
      { rootMargin: '-40% 0px -55% 0px', threshold: 0 }
    );

    targets.forEach((t) => observer.observe(t));
  }

  /* ----------------------------- Landing page ---------------------------- */

  function setupLandingProgress() {
    const cards = document.querySelectorAll('.phase-card[data-phase-key]');
    if (!cards.length) return;

    const progress = loadProgress();
    cards.forEach((card) => {
      const key = card.dataset.phaseKey;
      const phaseProgress = progress[key];
      if (!phaseProgress) return;

      const done = Object.keys(phaseProgress).length;
      const indicator = card.querySelector('[data-progress-indicator]');
      if (indicator) indicator.textContent = `${done} step${done === 1 ? '' : 's'} done`;
    });
  }

  /* --------------------------------- Init -------------------------------- */

  document.addEventListener('DOMContentLoaded', () => {
    setupCheckpoints();
    setupCopyButtons();
    setupTocHighlight();
    setupLandingProgress();
  });
})();
