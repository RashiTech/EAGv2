function activeTabId() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      resolve(tabs?.[0]?.id);
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("query");
  const btn = document.getElementById("searchBtn");
  const result = document.getElementById("result");

  // Handle search
  searchBtn.addEventListener("click", async () => {
    const query = input.value.trim();
    if (!query) return;
    result.textContent = "Searching...";

    chrome.runtime.sendMessage({ type: "SEARCH_QUERY", query }, async (resp) => {
      if (!resp?.ok) {
        result.textContent = "Error performing search";
        return;
      }
      const data = resp.data || {};
      if (data.status !== "ok" || !data.url) {
        result.textContent = "No results found";
        return;
      }
      result.textContent = "Opening matched page...";
    });
  });
});


