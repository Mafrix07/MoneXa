(function () {
  const root = document.documentElement;
  const saved = localStorage.getItem("monexa-theme");
  if (saved) root.setAttribute("data-theme", saved);

  document.getElementById("mx-theme")?.addEventListener("click", function () {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("monexa-theme", next);
  });

  document.getElementById("mx-collapse")?.addEventListener("click", function () {
    document.body.classList.toggle("mx-collapsed");
  });

  const side = document.getElementById("mx-sidebar");
  document.getElementById("mx-menu")?.addEventListener("click", function () {
    side?.classList.toggle("is-open");
  });

  document.querySelectorAll("[data-fill-question]").forEach(function (el) {
    el.addEventListener("click", function () {
      const input = document.querySelector("[name=question]");
      if (input) {
        input.value = el.getAttribute("data-fill-question");
        input.focus();
      }
    });
  });
})();
