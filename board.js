const body = document.querySelector("#players");
const updated = document.querySelector("#updated");

function dash(value) {
  return value === null || value === undefined || value === "" ? "—" : value;
}

function percent(rate) {
  if (rate === null || rate === undefined) return "—";
  return `${Math.round(rate * 100)}%`;
}

function when(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function fill(player) {
  const tr = document.createElement("tr");
  const values = [
    player.name,
    dash(player.matches),
    percent(player.quitRate),
    dash(player.tournaments),
    player.rating === null || player.rating === undefined ? "—" : String(player.rating),
    when(player.lastPlayed)
  ];
  values.forEach((value, index) => {
    const td = document.createElement("td");
    if (index === 0) td.className = "name";
    td.textContent = value;
    tr.append(td);
  });
  return tr;
}

fetch("stats.json", { cache: "no-store" })
  .then((response) => {
    if (!response.ok) throw new Error(String(response.status));
    return response.json();
  })
  .then((stats) => {
    const players = Array.isArray(stats.players) ? stats.players : [];
    body.replaceChildren();
    if (!players.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 6;
      td.className = "empty";
      td.textContent = "No recorded matches yet.";
      tr.append(td);
      body.append(tr);
    } else {
      players.forEach((player) => body.append(fill(player)));
    }
    if (stats.updatedAt) updated.textContent = `Updated ${when(stats.updatedAt)}`;
  })
  .catch(() => {
    body.innerHTML = '<tr><td colspan="6" class="empty">Stats are not available right now.</td></tr>';
  });
