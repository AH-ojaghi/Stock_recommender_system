import React, { useState } from "react";
import axios from "axios";

// تعریف رنگ‌ها بر اساس استاندارد Tailwind (به جای متغیرهای CSS)
// ما از رنگ‌های پیش‌فرض Tailwind برای حفظ سازگاری و حالت :hover استفاده می‌کنیم.
// آبی تیره (Corporate Blue): blue-900 یا blue-800
// رنگ تاکیدی (Accent Green): teal-600 یا emerald-500
const PRIMARY_COLOR = "blue-900"; 
const ACCENT_COLOR = "teal-600";
const HOVER_COLOR = "blue-800"; 

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
  // چک کن ببین ریسالت چی هست که بتونی اطلاعات جدول رو درست کنی 
    // console.log(results);

  return (
    <div 
      // کانتینر اصلی: حداکثر عرض، وسط چین، سایه، گوشه‌های گرد، RTL
      className="max-w-4xl mx-auto my-10 p-8 bg-white shadow-xl rounded-lg font-sans text-right rtl"
    >
      <h2 
        // سربرگ: متن بزرگ، رنگ اصلی، زیرخط تاکیدی
        className={`text-3xl font-bold text-${PRIMARY_COLOR} border-b-2 border-${ACCENT_COLOR} pb-3 mb-6`}
      >
        🚀 سامانه رتبه‌بندی و توصیه‌گر سهام
      </h2>

      {/* --- فرم آپلود --- */}
      <form 
        onSubmit={handleSubmit} 
        className="flex flex-col sm:flex-row gap-4 items-center mb-8 border border-gray-200 p-4 rounded-lg"
      >
        
        {/* فیلد فایل (استایل‌دهی فایل اینپوت در Tailwind دشوار است، اما کانتینر آن را استایل می‌دهیم) */}
        <div className="flex-grow p-2 border border-gray-300 rounded-md bg-gray-50">
          <input 
            type="file" 
            accept=".csv,text/csv" 
            onChange={handleFileChange} 
            className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>
        
        {/* دکمه ارسال */}
        <button 
          type="submit" 
          disabled={loading} 
          className={`
            py-3 px-8 text-white font-semibold rounded-lg shadow-md transition duration-300 ease-in-out whitespace-nowrap
            ${loading 
              ? `bg-${ACCENT_COLOR} opacity-70 cursor-not-allowed` 
              : `bg-${PRIMARY_COLOR} hover:bg-${HOVER_COLOR} focus:outline-none focus:ring-4 focus:ring-blue-300`
            }
          `}
        >
          {loading ? "در حال پردازش..." : "ارسال برای پیش‌بینی"}
        </button>
      </form>

      {/* --- پیام خطا --- */}
      {error && (
        <div 
          className="bg-red-100 border-r-4 border-red-500 text-red-700 p-4 mb-6" 
          role="alert"
        >
          <p className="font-bold">❌ خطا</p>
          <p>{error}</p>
        </div>
      )}

      {/* --- نتایج --- */}
      {results && results.length > 0 && (
        <div className="mt-8">
          <h3 className={`text-2xl font-semibold text-${PRIMARY_COLOR} mb-4`}>
            🏆 نتایج برتر (Top 10)
          </h3>
          <div className="overflow-x-auto shadow-md rounded-lg">
            <table className="w-full text-sm text-right text-gray-500">
              <thead className={`text-xs text-white uppercase bg-${PRIMARY_COLOR}`}>
                <tr>
                  <th scope="col" className="py-3 px-6">ردیف</th>
                  <th scope="col" className="py-3 px-6">شناسه سهام (ID)</th>
                  <th scope="col" className="py-3 px-6">امتیاز توصیه‌گر</th>
                  <th scope="col" className="py-3 px-6">اطلاعات تکمیلی</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, idx) => (
                  <tr 
                    key={idx} 
                    className={`
                      ${idx % 2 === 0 ? "bg-gray-50" : "bg-white"} 
                      border-b hover:bg-gray-100
                    `}
                  >
                    <td className="py-4 px-6 font-medium text-gray-900 whitespace-nowrap">
                      {idx + 1}
                    </td>
                    <td className="py-4 px-6 font-bold">
                      {r.id}
                    </td>
                    <td className={`py-4 px-6 font-semibold text-${ACCENT_COLOR}`}>
                      {r.score}
                    </td>
                    <td className="py-4 px-6 text-gray-700">
                      {(() => {
                        const keys = Object.keys(r).filter(k => k !== "id" && k !== "score");
                        return keys.length > 0 ? String(r[keys[0]]) : "-";
                      })()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}