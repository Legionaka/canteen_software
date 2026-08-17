/* menu.js — student cart state + order submission
   Talks to: POST /order  ->  { "order_id": <id> } */

(function () {
  "use strict";

  var SERVICE_FEE = 2.0;
  var config = window.CAMPUSEATS || {};
  var cart = []; // [{ id, name, price, quantity }]

  var grid = document.getElementById("menu-grid");
  var search = document.getElementById("menu-search");
  var tabs = document.getElementById("category-tabs");
  var list = document.getElementById("cart-list");
  var empty = document.getElementById("cart-empty");
  var subtotalEl = document.getElementById("cart-subtotal");
  var totalEl = document.getElementById("cart-total");
  var slotEl = document.getElementById("pickup-slot");
  var placeBtn = document.getElementById("place-order");
  var errorEl = document.getElementById("cart-error");

  function money(value) {
    return "R" + value.toFixed(2);
  }

  /* ---------- Filtering ---------- */
  var activeCategory = "all";

  function applyFilters() {
    var term = (search && search.value ? search.value : "").trim().toLowerCase();

    Array.prototype.forEach.call(grid.querySelectorAll(".item-card"), function (card) {
      var matchesCategory = activeCategory === "all" || card.dataset.category === activeCategory;
      var matchesSearch = !term || card.dataset.name.indexOf(term) !== -1;
      card.classList.toggle("is-hidden", !(matchesCategory && matchesSearch));
    });
  }

  if (tabs) {
    tabs.addEventListener("click", function (event) {
      var tab = event.target.closest(".tab");
      if (!tab) return;
      tabs.querySelectorAll(".tab").forEach(function (t) { t.classList.remove("is-active"); });
      tab.classList.add("is-active");
      activeCategory = tab.dataset.category;
      applyFilters();
    });
  }

  if (search) search.addEventListener("input", applyFilters);

  /* ---------- Cart ---------- */
  function addItem(id, name, price) {
    var existing = cart.find(function (line) { return line.id === id; });
    if (existing) {
      existing.quantity += 1;
    } else {
      cart.push({ id: id, name: name, price: price, quantity: 1 });
    }
    renderCart();
  }

  function changeQty(id, delta) {
    var line = cart.find(function (l) { return l.id === id; });
    if (!line) return;
    line.quantity += delta;
    if (line.quantity <= 0) {
      cart = cart.filter(function (l) { return l.id !== id; });
    }
    renderCart();
  }

  function renderCart() {
    list.innerHTML = "";

    if (cart.length === 0) {
      var placeholder = document.createElement("li");
      placeholder.className = "muted small";
      placeholder.textContent = "Your cart is empty.";
      list.appendChild(placeholder);
    } else {
      cart.forEach(function (line) {
        var li = document.createElement("li");
        li.className = "cart-item";

        var label = document.createElement("span");
        label.textContent = line.name;

        var right = document.createElement("span");
        right.className = "cart-item-qty";

        var minus = document.createElement("button");
        minus.type = "button";
        minus.className = "qty-btn";
        minus.textContent = "−";
        minus.addEventListener("click", function () { changeQty(line.id, -1); });

        var qty = document.createElement("span");
        qty.textContent = line.quantity;

        var plus = document.createElement("button");
        plus.type = "button";
        plus.className = "qty-btn";
        plus.textContent = "+";
        plus.addEventListener("click", function () { changeQty(line.id, 1); });

        var amount = document.createElement("span");
        amount.textContent = money(line.price * line.quantity);

        right.appendChild(minus);
        right.appendChild(qty);
        right.appendChild(plus);
        right.appendChild(amount);

        li.appendChild(label);
        li.appendChild(right);
        list.appendChild(li);
      });
    }

    var subtotal = cart.reduce(function (sum, line) { return sum + line.price * line.quantity; }, 0);
    subtotalEl.textContent = money(subtotal);
    totalEl.textContent = money(subtotal > 0 ? subtotal + SERVICE_FEE : 0);
    placeBtn.disabled = cart.length === 0;
  }

  if (grid) {
    grid.addEventListener("click", function (event) {
      var button = event.target.closest(".add-to-cart");
      if (!button) return;
      addItem(
        parseInt(button.dataset.id, 10),
        button.dataset.name,
        parseFloat(button.dataset.price)
      );
    });
  }

  /* ---------- Submit ---------- */
  function showError(message) {
    if (!errorEl) return;
    errorEl.textContent = message;
    errorEl.hidden = false;
  }

  if (placeBtn) {
    placeBtn.addEventListener("click", function () {
      if (cart.length === 0) return;

      placeBtn.disabled = true;
      placeBtn.textContent = "Placing order…";
      if (errorEl) errorEl.hidden = true;

      fetch(config.orderUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({
          cart: cart.map(function (line) {
            return { menu_item_id: line.id, quantity: line.quantity };
          }),
          pickup_slot: slotEl.value
        })
      })
        .then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) throw new Error(data.error || "Could not place your order.");
            return data;
          });
        })
        .then(function (data) {
          window.location.href = config.trackUrlTemplate.replace(/0(\/status)?$/, data.order_id + "$1");
        })
        .catch(function (err) {
          showError(err.message);
          placeBtn.disabled = false;
          placeBtn.textContent = "Place order";
        });
    });
  }

  renderCart();
})();
