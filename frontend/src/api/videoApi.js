import { apiUrl, request } from "./client";

export const fetchVideoInfo = (url) => request("/videos/info", { method: "POST", body: { url } });

export const createDownload = ({ url, height, profile }) =>
  request("/downloads", { method: "POST", body: { url, height, profile } });

export const getDownload = (id) => request(`/downloads/${id}`);

export const deleteDownload = (id) => request(`/downloads/${id}`, { method: "DELETE" });

export const fileUrl = (id) => apiUrl(`/downloads/${id}/file`);
