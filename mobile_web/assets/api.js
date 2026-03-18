async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch (error) {
    const networkError = new Error("Backend mobile indisponivel.");
    networkError.code = "network_error";
    throw networkError;
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const error = new Error(payload?.error || "Falha ao comunicar com o backend mobile.");
    error.status = response.status;
    error.code = payload?.code || "request_failed";
    error.payload = payload;
    throw error;
  }
  return payload;
}

export const mobileApi = {
  getSession() {
    return request("/api/mobile/session");
  },
  getBlockPages(blockId) {
    return request(`/api/mobile/blocks/${encodeURIComponent(blockId)}/pages`);
  },
  getPage(pageId) {
    return request(`/api/mobile/pages/${encodeURIComponent(pageId)}`);
  },
  setLineValue(lineId, value) {
    return request(`/api/mobile/lines/${encodeURIComponent(lineId)}/value`, {
      method: "POST",
      body: JSON.stringify({ value }),
    });
  },
  fillPage(pageId, value) {
    return request(`/api/mobile/pages/${encodeURIComponent(pageId)}/fill`, {
      method: "POST",
      body: JSON.stringify({ value }),
    });
  },
};
