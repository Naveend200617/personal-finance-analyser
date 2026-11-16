/* PocketWise front-end helpers */
document.addEventListener("DOMContentLoaded", function () {
  // Sidebar toggle for mobile
  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("appSidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("show");
      if (backdrop) backdrop.classList.toggle("show");
    });
    if (backdrop) {
      backdrop.addEventListener("click", function () {
        sidebar.classList.remove("show");
        backdrop.classList.remove("show");
      });
    }
  }

  // Auto-dismiss flash messages after 5s
  document.querySelectorAll(".alert-dismissible").forEach(function (el) {
    setTimeout(function () {
      const alert = bootstrap.Alert.getOrCreateInstance(el);
      alert.close();
    }, 5000);
  });

  // Delete confirmations handled via Bootstrap modal in templates.

  // Income/expense category select sync on transaction edit modal
  const txnTypeSel = document.querySelectorAll("[data-cattoggle]");
  txnTypeSel.forEach(function (sel) {
    sel.addEventListener("change", function () {
      const target = document.querySelector(sel.dataset.cattarget);
      if (!target) return;
      const incomeCats = JSON.parse(sel.dataset.income || "[]");
      const expenseCats = JSON.parse(sel.dataset.expense || "[]");
      const cats = sel.value === "income" ? incomeCats : expenseCats;
      target.innerHTML = "";
      cats.forEach(function (c) {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        target.appendChild(opt);
      });
    });
  });
});
