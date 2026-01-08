const API = "/api/inventory";
const body = document.getElementById("inventory-body");

const newName = document.getElementById("new-name");
const newQty = document.getElementById("new-qty");
const newUnit = document.getElementById("new-unit");
const addBtn = document.getElementById("add-btn");
const resetBtn = document.getElementById("reset-btn");

const STANDARD_UNITS = ["pcs","cup","tbsp","tsp","g","kg","ml","L","oz","lbs","cloves","slices",""]

// Populate unit dropdowns
function fillUnitSelect(select, unit) {
    select.innerHTML = STANDARD_UNITS.map(u => {
        return `<option value="${u}" ${u === unit ? "selected" : ""}>${u}</option>`;
    }).join("");
}

fillUnitSelect(newUnit, "");

// Create one row in the table
function renderRow(name, item) {
    const tr = document.createElement("tr");

    const nameTd = document.createElement("td");
    const qtyTd = document.createElement("td");
    const unitTd = document.createElement("td");
    const actTd = document.createElement("td");

    const nameInp = document.createElement("input");
    nameInp.value = name;
    const qtyInp = document.createElement("input");
    qtyInp.type = "number";
    qtyInp.step = "0.1";
    qtyInp.value = item.quantity ?? 0;
    const unitSel = document.createElement("select");
    fillUnitSelect(unitSel, item.unit);

    nameTd.appendChild(nameInp);
    qtyTd.appendChild(qtyInp);
    unitTd.appendChild(unitSel);

    const saveBtn = document.createElement("button");
    saveBtn.textContent = "Save";
    saveBtn.onclick = () => updateItem(nameInp.value, qtyInp.value, unitSel.value);

    const delBtn = document.createElement("button");
    delBtn.textContent = "Delete";
    delBtn.onclick = () => deleteItem(name);

    actTd.appendChild(saveBtn);
    actTd.appendChild(delBtn);

    tr.append(nameTd, qtyTd, unitTd, actTd);
    body.appendChild(tr);
}

// Load full inventory
async function refresh() {
    const res = await fetch(API);
    const data = await res.json();
    body.innerHTML = "";
    Object.entries(data).forEach(([name, item]) => {
        renderRow(name, item);
    });
}

async function addItem() {
    const name = newName.value.trim();
    const qty = parseFloat(newQty.value) || 0;
    const unit = newUnit.value || "";
  
    if (!name) return alert("Name required");
  
    await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, quantity: qty, unit })
    });
  
    newName.value = "";
    newQty.value = "";
    refresh();
  }
  

async function updateItem(name, qty, unit) {
    await fetch(`${API}/${encodeURIComponent(name)}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ quantity: Number(qty), unit })
    });
    refresh();
}

async function deleteItem(name) {
    await fetch(`${API}/${encodeURIComponent(name)}`, { method: "DELETE" });
    refresh();
}


async function resetInventory() {
    await fetch(`${API}/reset`, { method: "POST" });
    refresh();
}

addBtn.onclick = addItem;
resetBtn.onclick = resetInventory;

// Initial load
refresh();
