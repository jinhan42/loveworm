import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import "./i18n";
import ServerPanel from "./components/ServerPanel";
import HeatExchanger from "./components/HeatExchanger";
import ImmersionTank from "./components/ImmersionTank";
import PDUPanel from "./components/PDUPanel";

const queryClient = new QueryClient();

const TABS = [
  { key: "servers",       nav: "nav.servers" },
  { key: "heatExchanger", nav: "nav.heatExchanger" },
  { key: "immersionTank", nav: "nav.immersionTank" },
  { key: "pdu",           nav: "nav.pdu" },
];

function App() {
  const { t, i18n } = useTranslation();
  const [tab, setTab] = useState("servers");

  async function goToDesktop() {
    await fetch("/api/system/show-desktop", { method: "POST" });
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-900 text-white">
        {/* 헤더 */}
        <header className="bg-gray-800 px-4 py-3 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <span className="text-green-400 text-xl font-bold">UniTank</span>
            <span className="text-gray-400 text-sm">모니터링 시스템</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={goToDesktop}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition flex items-center gap-1"
              title="바탕화면으로 이동"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="3" width="20" height="14" rx="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
                <line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
              바탕화면
            </button>
            <button
              onClick={() => i18n.changeLanguage(i18n.language === "ko" ? "en" : "ko")}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
            >
              {i18n.language === "ko" ? "English" : "한국어"}
            </button>
          </div>
        </header>

        {/* 탭 네비게이션 (터치 최적화) */}
        <nav className="bg-gray-800 border-t border-gray-700 flex overflow-x-auto">
          {TABS.map(({ key, nav }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex-1 py-3 px-2 text-sm font-medium whitespace-nowrap transition
                ${tab === key
                  ? "text-green-400 border-b-2 border-green-400 bg-gray-700"
                  : "text-gray-400 hover:text-white"}`}
            >
              {t(nav)}
            </button>
          ))}
        </nav>

        {/* 컨텐츠 */}
        <main className="p-4 max-w-4xl mx-auto">
          {tab === "servers"       && <ServerPanel />}
          {tab === "heatExchanger" && <HeatExchanger />}
          {tab === "immersionTank" && <ImmersionTank />}
          {tab === "pdu"           && <PDUPanel />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
