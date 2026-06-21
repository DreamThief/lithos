const statusBar      = document.getElementById("status-bar");
const scanBtn        = document.getElementById("scan-btn");
const topResult      = document.getElementById("top-result");
const topImg         = document.getElementById("top-img");
const topName        = document.getElementById("top-name");
const topId          = document.getElementById("top-id");
const confidenceFill = document.getElementById("confidence-fill");
const confidencePct  = document.getElementById("confidence-pct");
const altResults     = document.getElementById("alt-results");
const altList        = document.getElementById("alt-list");
const errorBox       = document.getElementById("error-box");
const noResult       = document.getElementById("no-result");
const scanFlash      = document.getElementById("scan-flash");

function setStatus(text, type = "idle") {
  statusBar.textContent = text;
  statusBar.className = `status-bar status-${type}`;
}

function showTopResult(item) {
  topImg.src = item.img_url || "";
  topImg.alt = item.name;
  topName.textContent = item.name;
  topId.textContent = item.id;

  const pct = Math.round(item.score * 100);
  confidenceFill.style.width = pct + "%";
  confidencePct.textContent = pct + "%";

  topResult.classList.remove("hidden");
}

function showAltResults(items) {
  if (items.length === 0) {
    altResults.classList.add("hidden");
    return;
  }
  altList.innerHTML = items.map(item => {
    const pct = Math.round(item.score * 100);
    return `
      <li class="alt-item">
        <img class="alt-item-img" src="${item.img_url || ""}" alt="${item.name}" />
        <span class="alt-item-name">${item.name}</span>
        <span class="alt-item-id">#${item.id}</span>
        <span class="alt-item-score">${pct}%</span>
      </li>`;
  }).join("");
  altResults.classList.remove("hidden");
}

function clearResults() {
  topResult.classList.add("hidden");
  altResults.classList.add("hidden");
  errorBox.classList.add("hidden");
  noResult.classList.add("hidden");
}

function triggerFlash() {
  scanFlash.classList.remove("hidden");
  scanFlash.classList.remove("flash");
  // Force reflow to restart animation
  void scanFlash.offsetWidth;
  scanFlash.classList.add("flash");
  setTimeout(() => scanFlash.classList.add("hidden"), 400);
}

async function handleResult(data) {
  if (data.error) {
    setStatus("Error: " + data.error, "error");
    errorBox.textContent = data.error;
    errorBox.classList.remove("hidden");
    return;
  }

  const items = data.items || [];
  if (items.length === 0) {
    setStatus("No match found", "error");
    noResult.classList.remove("hidden");
    return;
  }

  const [top, ...rest] = items;
  showTopResult(top);
  showAltResults(rest);

  const pct = Math.round(top.score * 100);
  setStatus(`Identified: ${top.name}  (#${top.id})  — ${pct}% confidence`, "success");
}

async function scan() {
  clearResults();
  triggerFlash();
  setStatus("Scanning…", "scanning");
  scanBtn.disabled = true;

  try {
    const res = await fetch("/scan", { method: "POST" });
    const data = await res.json();
    await handleResult(data);
  } catch (err) {
    setStatus("Network error — is the server running?", "error");
    errorBox.textContent = err.message;
    errorBox.classList.remove("hidden");
  } finally {
    scanBtn.disabled = false;
  }
}

async function uploadImage(event) {
  const file = event.target.files[0];
  if (!file) return;

  clearResults();
  setStatus("Identifying uploaded image…", "scanning");
  scanBtn.disabled = true;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();
    await handleResult(data);
  } catch (err) {
    setStatus("Upload error", "error");
    errorBox.textContent = err.message;
    errorBox.classList.remove("hidden");
  } finally {
    scanBtn.disabled = false;
    // Reset input so the same file can be re-uploaded if needed
    event.target.value = "";
  }
}

// Keyboard shortcut: spacebar triggers scan
document.addEventListener("keydown", (e) => {
  if (e.code === "Space" && !scanBtn.disabled) {
    e.preventDefault();
    scan();
  }
});
