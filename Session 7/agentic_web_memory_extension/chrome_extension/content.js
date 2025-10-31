function getVisibleText() {
  try {
    return document.body?.innerText?.slice(0, 200000) || "";
  } catch (e) {
    return "";
  }
}

// On page load/idle, send text to background to store
(() => {
  const text = getVisibleText();
  const url = window.location.href;
  if (!text || !url) return;
  chrome.runtime.sendMessage({ type: "STORE_PAGE_TEXT", url, text });
})();

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&");
}

function highlightRegexOnNodes(regex, className) {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);

  nodes.forEach((textNode) => {
    try {
      if (!textNode.nodeValue || !textNode.parentElement) return;

      const tag = (textNode.parentElement.tagName || '').toUpperCase();
      // skip script/style/iframe/noscript and already highlighted content
      if (['SCRIPT', 'STYLE', 'IFRAME', 'NOSCRIPT', 'HEAD'].includes(tag)) return;
      if (textNode.parentElement.closest && textNode.parentElement.closest('mark')) return;

      if (!regex.test(textNode.nodeValue)) return;
      const span = document.createElement("span");
      const html = textNode.nodeValue.replace(regex, (m) => `<mark class="${className}">${m}</mark>`);
      span.innerHTML = html;
      const parent = textNode.parentNode;
      if (parent) parent.replaceChild(span, textNode);
    } catch (e) {
      // ignore nodes that can't be replaced
    }
  });
}

function pickBestSentence(matchedText, tokens) {
  if (!matchedText) return null;
  const sentences = matchedText.split(/(?<=[.!?])\s+/);
  for (const s of sentences) {
    for (const t of tokens) {
      if (t.length < 3) continue;
      const re = new RegExp(`\\b${escapeRegex(t)}\\b`, 'i');
      if (re.test(s)) return s.trim();
    }
  }
  // fallback to first non-empty sentence
  for (const s of sentences) {
    if (s.trim()) return s.trim();
  }
  return null;
}

function highlightPhrases(phrases, matchedText = null, searchText = null) {
  if ((!Array.isArray(phrases) || phrases.length === 0) && !matchedText && !searchText) return;

  const markClass = "agentic-highlight-mark";
  const matchedClass = "agentic-highlight-matched";
  const styleId = "agentic-highlight-style";

  if (!document.getElementById(styleId)) {
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
      .${markClass} { 
        background: yellow; 
        color: black; 
        padding: 0 2px; 
      }
      .${matchedClass} {
        background: #ffeb3b;
        border: 2px solid #ffc107;
        padding: 0 2px;
        border-radius: 2px;
      }
    `;
    document.head.appendChild(style);
  }

  // 1) Highlight phrases (short snippets) as before
  if (Array.isArray(phrases) && phrases.length > 0) {
    phrases.forEach((snippet) => {
      const term = snippet.split(/\s+/).slice(0, 3).join(" "); // heuristic
      if (!term) return;
      const re = new RegExp(escapeRegex(term), "i");
      highlightRegexOnNodes(re, markClass);
    });
  }

  // 2) Highlight tokens from the search text (fuzzy / related matches)
  if (searchText && typeof searchText === 'string') {
    const tokens = Array.from(new Set(
      searchText
        .toLowerCase()
        .split(/\W+/)
        .filter((t) => t && t.length >= 3)
    ));
    if (tokens.length > 0) {
      const union = tokens.map(escapeRegex).join('|');
      const re = new RegExp(`\\b(?:${union})\\b`, 'gi');
      highlightRegexOnNodes(re, markClass);
    }
  }

  // 3) If we have matchedText, try to find a best sentence related to the query
  const tokensForPick = (searchText && typeof searchText === 'string') ? searchText.toLowerCase().split(/\W+/) : [];
  const bestSentence = pickBestSentence(matchedText, tokensForPick);
  if (bestSentence) {
    try {
      const re = new RegExp(escapeRegex(bestSentence), 'i');
      highlightRegexOnNodes(re, matchedClass);
      // scroll to first matchedClass element
      const first = document.querySelector(`.${matchedClass}`);
      if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (e) {
      // ignore regex errors
    }
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "HIGHLIGHT_SEARCH") {
    highlightPhrases(message.highlights || [], message.matchedText, message.searchText);
    sendResponse({ ok: true });
  } else if (message?.type === "HIGHLIGHT_PHRASES") {
    highlightPhrases(message.phrases || []);
    sendResponse({ ok: true });
  }
});


