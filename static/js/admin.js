/* admin.js — dashboard charts + table filters
   Talks to: GET /admin/stats -> { hourly: [...], top_items: [...] } */

(function () {
  "use strict";

  var config = window.CAMPUSEATS || {};

  /* ---------- Dashboard: hourly chart + top items ---------- */
  var canvas = document.getElementById("hourly-chart");
  var topItemsEl = document.getElementById("top-items");

  function renderHourly(hourly) {
    if (!canvas || typeof window.Chart === "undefined") return;

    new window.Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels: hourly.map(function (row) { return row.hour || row.label; }),
        datasets: [{
          label: "Orders",
          data: hourly.map(function (row) { return row.count || row.orders || 0; }),
          backgroundColor: "#E85D24",
          borderRadius: 6,
          barPercentage: 0.6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: "#6F6A62" } },
          y: {
            beginAtZero: true,
            ticks: { precision: 0, color: "#6F6A62" },
            grid: { color: "#E2DDD6" }
          }
        }
      }
    });
  }

  function renderTopItems(items) {
    if (!topItemsEl) return;
    topItemsEl.innerHTML = "";

    if (!items || items.length === 0) {
      topItemsEl.innerHTML = '<li class="muted small">No sales yet today.</li>';
      return;
    }

    var max = Math.max.apply(null, items.map(function (i) { return i.count || i.quantity || 0; }));

    items.forEach(function (item) {
      var value = item.count || item.quantity || 0;
      var li = document.createElement("li");

      var head = document.createElement("div");
      head.className = "bar-head";

      var name = document.createElement("span");
      name.textContent = item.name;

      var count = document.createElement("span");
      count.className = "muted";
      count.textContent = value + " sold";

      head.appendChild(name);
      head.appendChild(count);

      var track = document.createElement("div");
      track.className = "bar-track";

      var fill = document.createElement("div");
      fill.className = "bar-fill";
      fill.style.width = (max > 0 ? (value / max) * 100 : 0) + "%";

      track.appendChild(fill);
      li.appendChild(head);
      li.appendChild(track);
      topItemsEl.appendChild(li);
    });
  }

  if (config.statsUrl) {
    fetch(config.statsUrl, { headers: { Accept: "application/json" } })
      .then(function (response) { return response.ok ? response.json() : null; })
      .then(function (data) {
        if (!data) return;
        renderHourly(data.hourly || []);
        renderTopItems(data.top_items || []);
      })
      .catch(function () {
        if (topItemsEl) topItemsEl.innerHTML = '<li class="muted small">Could not load stats.</li>';
      });
  }

  /* ---------- Menu page: category tabs + add modal ---------- */
  var menuTabs = document.getElementById("admin-menu-tabs");
  var menuTable = document.getElementById("admin-menu-table");

  if (menuTabs && menuTable) {
    menuTabs.addEventListener("click", function (event) {
      var tab = event.target.closest(".tab");
      if (!tab) return;

      menuTabs.querySelectorAll(".tab").forEach(function (t) { t.classList.remove("is-active"); });
      tab.classList.add("is-active");

      var category = tab.dataset.category;
      menuTable.querySelectorAll("tbody tr[data-category]").forEach(function (row) {
        row.classList.toggle("is-hidden", category !== "all" && row.dataset.category !== category);
      });
    });
  }

  var modal = document.getElementById("add-modal");
  var openBtn = document.getElementById("open-add-modal");
  var closeBtn = document.getElementById("close-add-modal");

  if (modal && openBtn) {
    openBtn.addEventListener("click", function () { modal.hidden = false; });
    if (closeBtn) closeBtn.addEventListener("click", function () { modal.hidden = true; });
    modal.addEventListener("click", function (event) {
      if (event.target === modal) modal.hidden = true;
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") modal.hidden = true;
    });
  }

  /* ---------- Orders page: status tabs + date filter ---------- */
  var statusTabs = document.getElementById("order-status-tabs");
  var ordersTable = document.getElementById("orders-table");
  var dateFilter = document.getElementById("order-date-filter");

  function filterOrders() {
    if (!ordersTable) return;

    var activeTab = statusTabs ? statusTabs.querySelector(".tab.is-active") : null;
    var status = activeTab ? activeTab.dataset.status : "all";
    var date = dateFilter ? dateFilter.value : "";

    ordersTable.querySelectorAll("tbody tr[data-status]").forEach(function (row) {
      var statusOk = status === "all" || row.dataset.status === status;
      var dateOk = !date || row.dataset.date === date;
      row.classList.toggle("is-hidden", !(statusOk && dateOk));
    });
  }

  if (statusTabs) {
    statusTabs.addEventListener("click", function (event) {
      var tab = event.target.closest(".tab");
      if (!tab) return;
      statusTabs.querySelectorAll(".tab").forEach(function (t) { t.classList.remove("is-active"); });
      tab.classList.add("is-active");
      filterOrders();
    });
  }

  if (dateFilter) dateFilter.addEventListener("change", filterOrders);

  /* ---------- Students page: search ---------- */
  var studentSearch = document.getElementById("student-search");
  var studentsTable = document.getElementById("students-table");

  if (studentSearch && studentsTable) {
    studentSearch.addEventListener("input", function () {
      var term = studentSearch.value.trim().toLowerCase();
      studentsTable.querySelectorAll("tbody tr[data-search]").forEach(function (row) {
        row.classList.toggle("is-hidden", term && row.dataset.search.indexOf(term) === -1);
      });
    });
  }
})();
