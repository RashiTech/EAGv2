const BACKEND_URL = "http://127.0.0.1:8000";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "STORE_PAGE_TEXT") {
    const payload = { url: message.url, text: message.text };
    fetch(`${BACKEND_URL}/api/store_page`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => sendResponse({ ok: true, data }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true; // async
  }

  if (message?.type === "SEARCH_QUERY") {
    const payload = { query: message.query };
    fetch(`${BACKEND_URL}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        console.log('Search result:', data);  // Debug log
        if (data.status === "ok" && data.url) {
          // Open the URL in a new tab
          console.log('Opening URL:', data.url);  // Debug log
          chrome.tabs.create({ url: data.url, active: true }, (tab) => {
            if (chrome.runtime.lastError) {
              console.error('Error creating tab:', chrome.runtime.lastError);
              return;
            }
            console.log('Created tab:', tab.id);  // Debug log
            
            // Wait for the page to load before sending highlight info
            chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
              console.log('Tab updated:', tabId, info.status);  // Debug log
              if (info.status === 'complete' && tabId === tab.id) {
                chrome.tabs.onUpdated.removeListener(listener);
                chrome.tabs.sendMessage(tab.id, {
                  type: 'HIGHLIGHT_SEARCH',
                  searchText: message.query,
                  matchedText: data.matchedText,
                  highlights: data.highlights
                }, (response) => {
                  if (chrome.runtime.lastError) {
                    console.error('Error sending message:', chrome.runtime.lastError);
                  }
                });
              }
            });
          });
        } else {
          console.log('No valid URL in search result');  // Debug log
        }
        sendResponse({ ok: true, data });
      })
      .catch((e) => {
        console.error('Search error:', e);  // Debug log
        sendResponse({ ok: false, error: String(e) });
      });
    return true; // async
  }
});


