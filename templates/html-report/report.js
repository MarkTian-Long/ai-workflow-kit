"use strict";

(() => {
  const nav = document.querySelector("[data-toc]");
  const sections = [...document.querySelectorAll("main section[data-section]")];
  if (!nav || sections.length === 0) return;

  const entries = [];
  sections.forEach((section, index) => {
    const heading = section.querySelector("h2");
    if (!heading) return;
    if (!section.id) {
      let id = `section-${index + 1}`;
      let suffix = 2;
      while (document.getElementById(id)) id = `section-${index + 1}-${suffix++}`;
      section.id = id;
    }
    const link = document.createElement("a");
    link.href = `#${section.id}`;
    const number = document.createElement("span");
    number.className = "toc-number";
    number.setAttribute("aria-hidden", "true");
    number.textContent = String(entries.length + 1).padStart(2, "0");
    const label = document.createElement("span");
    label.textContent = section.dataset.navLabel || heading.textContent.trim();
    link.append(number, label);
    nav.append(link);
    entries.push({ section, link });
  });

  const mark = (entry) => {
    entries.forEach((candidate) => {
      if (candidate === entry) candidate.link.setAttribute("aria-current", "location");
      else candidate.link.removeAttribute("aria-current");
    });
  };
  const update = () => {
    let current = entries[0];
    entries.forEach((entry) => {
      if (entry.section.getBoundingClientRect().top <= 150) current = entry;
    });
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) {
      current = entries[entries.length - 1];
    }
    mark(current);
  };
  let queued = false;
  window.addEventListener("scroll", () => {
    if (queued) return;
    queued = true;
    window.requestAnimationFrame(() => { update(); queued = false; });
  }, { passive: true });
  window.addEventListener("resize", update);
  window.addEventListener("hashchange", update);
  entries.forEach((entry) => entry.link.addEventListener("click", () => mark(entry)));
  update();
})();
