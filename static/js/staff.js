/* staff.js — kitchen board auto-refresh
   Talks to: GET /staff/orders/live
   Status changes and sold-out toggles use plain form POSTs (see dashboard.html). */

(function () {
  "use strict";

  var config = window.CAMPUSEATS || {};
  var REFRESH_MS = 10000;

  var counts = {
    new: document.querySelectorAll(".kanban-col")[0],
    preparing: document.querySelectorAll(".kanban-col")[1],
    ready: document.querySelectorAll(".kanban-col")[2]
  };

  function currentSignature() {
    return Array.prototype.map
      .call(document.querySelectorAll(".order-card .pickup-code-sm"), function (el) {
        return el.closest(".kanban-col").querySelector(".h-sub").firstChild.textContent.trim() +
          ":" + el.textContent.trim();
      })
      .sort()
      .join("|");
  }

  function incomingSignature(orders) {
    return orders
      .map(function (order) {
        var column = order.status.charAt(0).toUpperCase() + order.status.slice(1);
        return column + ":" + order.pickup_code;
      })
      .sort()
      .join("|");
  }

  function refresh() {
    if (!config.liveUrl) return;

    fetch(config.liveUrl, { headers: { Accept: "application/json" } })
      .then(function (response) { return response.ok ? response.json() : null; })
      .then(function (data) {
        if (!data) return;
        var orders = Array.isArray(data) ? data : data.orders || [];
        // Only reload when the board actually changed — avoids losing scroll position.
        if (incomingSignature(orders) !== currentSignature()) {
          window.location.reload();
        }
      })
      .catch(function () { /* offline: try again on the next tick */ });
  }

  // Pause polling when the tab is hidden.
  var timer = setInterval(refresh, REFRESH_MS);
  document.addEventListener("visibilitychange", function () {
    clearInterval(timer);
    if (!document.hidden) {
      refresh();
      timer = setInterval(refresh, REFRESH_MS);
    }
  });

  // Optimistic feedback on sold-out chips.
  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      chip.disabled = true;
      chip.style.opacity = "0.6";
    });
  });

  void counts;
})();
