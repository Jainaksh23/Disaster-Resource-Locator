/**
 * api/client.js — Central API fetch wrapper
 * Automatically injects the Authorization header if a token exists in localStorage.
 */

export async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem("token")
  
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  })

  // Optionally handle 401 globally here (e.g., force logout event)
  if (response.status === 401) {
    // If not on login page, we might want to clear token and redirect
    if (window.location.pathname !== "/login") {
      localStorage.removeItem("token")
      window.location.href = "/login"
    }
    throw new Error("Unauthorized")
  }

  if (!response.ok) {
    let errMessage = "API Error"
    try {
      const data = await response.json()
      errMessage = data.detail || errMessage
    } catch (e) {
      // ignore JSON parse error for error response
    }
    throw new Error(errMessage)
  }

  return response.json()
}
