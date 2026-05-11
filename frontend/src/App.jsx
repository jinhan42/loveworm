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

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-900 text-white">
        {/* 헤더 */}
        <header className="bg-gray-800 px-4 py-3 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <span className="text-green-400 text-xl font-bold">Loveworm</span>
            <span className="text-gray-400 text-sm">모니터링 시스템</span>
          </div>
          <button
            onClick={() => i18n.changeLanguage(i18n.language === "ko" ? "en" : "ko")}
            className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
          >
            {i18n.language === "ko" ? "English" : "한국어"}
          </button>
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
