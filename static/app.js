const filters = document.querySelectorAll(".filter");
const featureCards = document.querySelectorAll(".feature-card");
const menuButton = document.querySelector(".menu-button");
const navLinks = document.querySelector(".nav-links");
const updatesGrid = document.querySelector("#updates-grid");
const updateStatus = document.querySelector("#update-status");
const refreshButton = document.querySelector("#refresh-updates");
const updatesEndpoint = document.body.dataset.updatesEndpoint || "/api/updates";
const header = document.querySelector(".site-header");
const progressBar = document.querySelector(".scroll-progress span");
const sections = document.querySelectorAll("main section[id]");
const sectionLinks = document.querySelectorAll("[data-nav-section]");
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

window.addEventListener("load", () => {
  window.setTimeout(() => document.body.classList.add("is-loaded"), 240);
});

filters.forEach((button) => {
  button.addEventListener("click", () => {
    filters.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    featureCards.forEach((card) => {
      const visible = button.dataset.filter === "All" || card.dataset.category === button.dataset.filter;
      card.hidden = !visible;
    });
  });
});

menuButton.addEventListener("click", () => {
  const open = menuButton.getAttribute("aria-expanded") === "true";
  menuButton.setAttribute("aria-expanded", String(!open));
  navLinks.classList.toggle("open", !open);
});

navLinks.addEventListener("click", (event) => {
  if (event.target.closest("a")) {
    menuButton.setAttribute("aria-expanded", "false");
    navLinks.classList.remove("open");
  }
});

function escapeHtml(value) {
  const span = document.createElement("span");
  span.textContent = value || "";
  return span.innerHTML;
}

function formatDate(value) {
  if (!value) return "Recently published";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function renderUpdates(items) {
  if (!items.length) {
    updatesGrid.innerHTML = `
      <div class="empty-state">
        <span>↻</span>
        <h3>Official feeds are temporarily unavailable</h3>
        <p>Please refresh shortly, or visit the GitHub Copilot changelog directly.</p>
      </div>`;
    return;
  }
  updatesGrid.innerHTML = items.slice(0, 6).map((item, index) => `
    <article class="update-card tone-${["rose", "blue", "green", "amber"][index % 4]} ${index === 0 ? "featured-update" : ""}" data-tilt-card>
      <div class="update-card-top">
        <span class="source-pill">${escapeHtml(item.kind)}</span>
        <time datetime="${escapeHtml(item.published_at)}">${formatDate(item.published_at)}</time>
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.summary)}</p>
      <div class="update-card-bottom">
        <span>${escapeHtml(item.source)}</span>
        <a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer" aria-label="Read ${escapeHtml(item.title)}">Read update <span aria-hidden="true">→</span></a>
      </div>
    </article>
  `).join("");
  initializeTilt(updatesGrid.querySelectorAll("[data-tilt-card]"));
}

async function loadUpdates() {
  refreshButton.classList.add("spinning");
  refreshButton.disabled = true;
  updateStatus.textContent = "Refreshing official sources…";
  try {
    const response = await fetch(updatesEndpoint, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    const data = await response.json();
    renderUpdates(data.items || []);
    if (data.updated_at) {
      const updated = new Date(data.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      updateStatus.textContent = data.stale ? `Updated ${updated} · Some sources unavailable` : `Updated ${updated}`;
    } else {
      updateStatus.textContent = "Waiting for official sources";
    }
  } catch (error) {
    renderUpdates([]);
    updateStatus.textContent = "Could not reach the update service";
  } finally {
    refreshButton.classList.remove("spinning");
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener("click", loadUpdates);
loadUpdates();

let lastScrollY = window.scrollY;
let ticking = false;

function updateScrollInterface() {
  const scrollY = window.scrollY;
  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  const progress = maxScroll > 0 ? (scrollY / maxScroll) * 100 : 0;
  progressBar.style.transform = `scaleX(${progress / 100})`;

  const movingDown = scrollY > lastScrollY;
  header.classList.toggle("header-hidden", movingDown && scrollY > 160);
  header.classList.toggle("header-compact", scrollY > 32);
  lastScrollY = scrollY;
  ticking = false;
}

window.addEventListener("scroll", () => {
  if (!ticking) {
    window.requestAnimationFrame(updateScrollInterface);
    ticking = true;
  }
}, { passive: true });

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("revealed");
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.14, rootMargin: "0px 0px -5% 0px" });

document.querySelectorAll(".reveal").forEach((element) => revealObserver.observe(element));

const navigationObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    sectionLinks.forEach((link) => {
      link.classList.toggle("active", link.dataset.navSection === entry.target.id);
    });
  });
}, { threshold: 0.45 });

sections.forEach((section) => navigationObserver.observe(section));

function initializeTilt(elements) {
  if (prefersReducedMotion.matches || !window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

  elements.forEach((element) => {
    if (element.dataset.tiltReady) return;
    element.dataset.tiltReady = "true";
    element.addEventListener("pointermove", (event) => {
      const bounds = element.getBoundingClientRect();
      const x = (event.clientX - bounds.left) / bounds.width - 0.5;
      const y = (event.clientY - bounds.top) / bounds.height - 0.5;
      element.style.setProperty("--tilt-x", `${x * 7}deg`);
      element.style.setProperty("--tilt-y", `${y * -7}deg`);
      element.style.setProperty("--glow-x", `${(x + 0.5) * 100}%`);
      element.style.setProperty("--glow-y", `${(y + 0.5) * 100}%`);
    });
    element.addEventListener("pointerleave", () => {
      element.style.setProperty("--tilt-x", "0deg");
      element.style.setProperty("--tilt-y", "0deg");
    });
  });
}

initializeTilt(document.querySelectorAll("[data-tilt-card], [data-tilt-scene]"));

if (!prefersReducedMotion.matches && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
  document.querySelectorAll(".button, .nav-cta").forEach((element) => {
    element.addEventListener("pointermove", (event) => {
      const bounds = element.getBoundingClientRect();
      const x = event.clientX - bounds.left - bounds.width / 2;
      const y = event.clientY - bounds.top - bounds.height / 2;
      element.style.transform = `translate(${x * 0.08}px, ${y * 0.12}px)`;
    });
    element.addEventListener("pointerleave", () => {
      element.style.transform = "";
    });
  });
}

updateScrollInterface();
