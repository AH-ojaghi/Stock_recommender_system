import React, { useState } from "react";
import axios from "axios";

export default function UploadForm() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResults([]);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("لطفاً یک فایل CSV انتخاب کنید.");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file, file.name);

      // Use relative path so it works with dev proxy (package.json proxy)
      // and also works in production where nginx proxies /predict to backend.
      const res = await axios.post("/predict", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setResults(res.data.top_10 || []);
    } catch (err) {
      console.error(err);
      const msg = err?.response?.data?.detail || err.message || "خطا در ارسال فایل";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "auto", padding: 20 }}>
      <h2>آپلود CSV برای رتبه‌بندی سهام</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" accept=".csv,text/csv" onChange={handleFileChange} />
        <button type="submit" disabled={loading} style={{ marginLeft: 10 }}>
          {loading ? "در حال پردازش..." : "ارسال"}
        </button>
      </form>

      {error && <div style={{ color: "red", marginTop: 10 }}>{error}</div>}

      {results && results.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <h3>Top 10</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ border: "1px solid #ddd", padding: 8 }}>#</th>
                <th style={{ border: "1px solid #ddd", padding: 8 }}>id</th>
                <th style={{ border: "1px solid #ddd", padding: 8 }}>score</th>
                <th style={{ border: "1px solid #ddd", padding: 8 }}>extra</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, idx) => (
                <tr key={idx}>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>{idx + 1}</td>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>{r.id}</td>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>{r.score}</td>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>
                    {(() => {
                      // display the first non-id/score field as 'extra'
                      const keys = Object.keys(r).filter(k => k !== "id" && k !== "score");
                      return keys.length > 0 ? String(r[keys[0]]) : "-";
                    })()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
