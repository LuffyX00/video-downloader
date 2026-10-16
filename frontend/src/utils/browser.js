// Starts a file download without navigating away (server sends Content-Disposition: attachment).
export function triggerBrowserDownload(url) {
  const a = document.createElement("a");
  a.href = url;
  a.rel = "noopener";
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  a.remove();
}
