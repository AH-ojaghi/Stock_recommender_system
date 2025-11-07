import React, { useState } from "react";
import axios from "axios";

// 🎨 استایل‌های شرکتی و مدرن Tailwind
const PRIMARY_TEXT_CLASS = "text-indigo-900"; // رنگ اصلی متن (آبی نیلی تیره)
const PRIMARY_BG_CLASS = "bg-indigo-700"; // رنگ اصلی پس‌زمینه (برای سربرگ‌ها و دکمه)
const ACCENT_TEXT_CLASS = "text-emerald-600"; // رنگ تاکیدی (برای امتیازات)
const HOVER_BG_CLASS = "hover:bg-indigo-600"; // حالت هاور دکمه
const ACCENT_BG_CLASS = "bg-emerald-500"; // پس‌زمینه تاکیدی ثانویه

// 🛠️ آدرس API که بدون تغییر باقی می‌ماند
const API_URL = "http://localhost:8000/recommend"; 


/**
 * تابع کمکی برای فرمت کردن اعداد بزرگ (مانند Market Cap) به صورت K, M, B
 * @param {number} num - عدد ورودی
 * @returns {string} - عدد فرمت شده به صورت فارسی با پسوندهای انگلیسی
 */
const formatNumber = (num) => {
    if (num === null || num === undefined) return "-";
    const units = ['', 'K', 'M', 'B', 'T'];
    const sign = Math.sign(num);
    num = Math.abs(num);
    let i = 0;
    while (num >= 1000 && i < units.length - 1) {
        num /= 1000;
        i++;
    }
    return sign * num.toFixed(2) + units[i];
};

export default function App() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // تابع واکشی داده‌ها از API جدید (GET)
  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);
    setResults([]);

    try {
      // استفاده از متد GET برای اندپوینت
      const res = await axios.get(API_URL);

      // ساختار پاسخ جدید: { "top_k_recommendations": [...] }
      const data = res.data.top_k_recommendations || [];
      
      // بررسی خالی بودن لیست
      if (data.length === 0) {
          setError("✅ داده‌ها از API دریافت شد، اما لیست توصیه‌ها خالی است. (آیا اسکریپت رتبه‌بندی در بک‌اند اجرا شده و خروجی مناسب داشته؟)");
      }

      setResults(data);
    } catch (err) {
      console.error("API Error:", err);
      const msg = err?.response?.data?.detail || err.message || "خطا در برقراری ارتباط با سامانه رتبه‌بندی. (آیا سرویس Backend اجرا شده است؟)";
      setError(`❌ ${msg}`);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-8 font-sans text-right rtl">
      <div 
        // کانتینر اصلی: ریسپانسیو و شرکتی
        className="max-w-6xl mx-auto bg-white shadow-2xl rounded-xl p-6 sm:p-10"
      >
        <h2 
          // سربرگ با استایل حرفه‌ای
          className={`text-2xl sm:text-3xl font-extrabold ${PRIMARY_TEXT_CLASS} border-b-4 border-emerald-500 pb-4 mb-8 flex items-center`}
        >
          {/* استفاده از آیکون فلش به جای ایموجی برای جلوه رسمی‌تر */}
          <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7 ml-3 text-emerald-500 hidden sm:block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          توصیه‌های روزانه سامانه رتبه‌بندی سهام
        </h2>

        {/* --- دکمه دریافت توصیه‌ها --- */}
        <div className="flex justify-center mb-8 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
          <button 
            type="button" 
            onClick={fetchRecommendations} 
            disabled={loading} 
            className={`
              py-3 px-10 text-white font-bold rounded-lg transition duration-300 ease-in-out w-full sm:w-auto 
              transform active:scale-95 shadow-lg
              ${loading 
                ? `${ACCENT_BG_CLASS} opacity-70 cursor-not-allowed flex items-center justify-center` 
                : `${PRIMARY_BG_CLASS} ${HOVER_BG_CLASS} focus:outline-none focus:ring-4 focus:ring-indigo-300`
              }
            `}
          >
            {loading ? (
              <div className="flex items-center">
                <svg className="animate-spin -mr-1 ml-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                در حال دریافت...
              </div>
            ) : (
              "دریافت آخرین توصیه‌های روزانه"
            )}
          </button>
        </div>

        {/* --- پیام خطا --- */}
        {error && (
          <div 
            className="bg-red-50 border-r-4 border-red-500 text-red-800 p-4 mb-8 rounded-md shadow-sm" 
            role="alert"
          >
            <p className="font-extrabold flex items-center">
              ⚠️ اطلاعیه مهم
            </p>
            <p className="mt-1 text-sm">{error}</p>
          </div>
        )}

        {/* --- نتایج --- */}
        {results && results.length > 0 && (
          <div className="mt-8">
            <h3 className={`text-xl font-semibold ${PRIMARY_TEXT_CLASS} mb-4 flex items-center`}>
              <span className="text-emerald-600 text-3xl ml-2">★</span>
              {results.length} سهم برتر امروز
            </h3>
            
            {/* ریسپانسیو کردن جدول با overflow-x-auto */}
            <div className="overflow-x-auto shadow-xl rounded-xl border border-gray-200">
              <table className="w-full text-sm text-right text-gray-700 min-w-[700px]">
                <thead className={`text-xs text-white uppercase ${PRIMARY_BG_CLASS} border-b border-indigo-600`}>
                  <tr>
                    <th scope="col" className="py-3 px-6">ردیف</th>
                    <th scope="col" className="py-3 px-6">نماد (Ticker)</th>
                    <th scope="col" className="py-3 px-6">امتیاز توصیه‌گر</th>
                    <th scope="col" className="py-3 px-6">نسبت P/E</th> 
                    <th scope="col" className="py-3 px-6">ارزش بازار (Market Cap)</th> 
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, idx) => (
                    <tr 
                      key={idx} 
                      className={`
                        ${idx % 2 === 0 ? "bg-white" : "bg-indigo-50"} 
                        border-b border-indigo-100 hover:bg-indigo-100 transition duration-150
                      `}
                    >
                      <td className="py-4 px-6 font-medium text-indigo-900 whitespace-nowrap">
                        {idx + 1}
                    </td>
                    <td className="py-4 px-6 font-extrabold text-xl text-indigo-800">
                      {r.id}
                    </td>
                    <td className={`py-4 px-6 font-mono font-bold text-base ${ACCENT_TEXT_CLASS}`}>
                      {r.score ? r.score.toFixed(4) : "-"} 
                    </td>
                    <td className="py-4 px-6 text-gray-600 font-mono">
                      {r.extra_data && r.extra_data["P/E Ratio"] !== undefined
                        ? r.extra_data["P/E Ratio"].toFixed(2)
                        : "-"}
                    </td>
                    <td className="py-4 px-6 text-gray-600 font-mono">
                      {r.extra_data && r.extra_data["Market Cap"]
                        ? formatNumber(r.extra_data["Market Cap"])
                        : "-"}
                    </td>
                  </tr>
                ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}