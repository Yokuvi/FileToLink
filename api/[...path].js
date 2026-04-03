// api/[...path].js
// Vercel function: redirects all paths to PythonAnywhere backend

export default function handler(req, res) {
  const { path = [] } = req.query;

  // join path segments, e.g. ["s", "abc123"] => "s/abc123"
  const joinedPath = Array.isArray(path) ? path.join("/") : path;

  // PythonAnywhere backend base URL:
  const backendBase = "https://yourname.pythonanywhere.com"; // TODO: change this

  const targetUrl = `${backendBase}/${joinedPath}`;

  res.status(302).setHeader("Location", targetUrl).end();
}
