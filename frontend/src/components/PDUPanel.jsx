import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function PDUPanel() {
  const { t } = useTranslation();
  const { data: latest } = useQuery({
    queryKey: ["pdu-latest"],
    queryFn: () => axios.get(`${API}/api/pdu/latest`).then(r => r.data),
    refetchInterval: 30000,
  });
  const { data: history } = useQuery({
    queryKey: ["pdu-history"],
    queryFn: () => axios.get(`${API}/api/pdu/history?limit=30`).then(r => r.data),
    refetchInterval: 30000,
  });

  const outlets = latest?.outlets || {};
  const outletData = Object.entries(outlets).map(([k, v]) => ({ name: k, power: v }));
  const historyData = [...(history || [])].reverse().map(r => ({
    time: new Date(r.timestamp).toLocaleTimeString("ko-KR"),
    power: r.total_power,
  }));

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">{t("pdu.title")}</h2>
      <div className="card mb-4">
        <div className="text-center">
          <div className="text-sm text-gray-400">{t("pdu.totalPower")}</div>
          <div className="text-5xl font-bold text-green-400 mt-2">
            {latest?.total_power ?? "-"}
          </div>
          <div className="text-lg text-gray-400">{t("pdu.unit")}</div>
        </div>
      </div>
      {outletData.length > 0 && (
        <div className="card mb-4 h-40">
          <div className="text-sm text-gray-400 mb-2">{t("pdu.outlet")} 별 전력</div>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={outletData}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis width={35} />
              <Tooltip formatter={v => [`${v} W`]} />
              <Bar dataKey="power" fill="#4ade80" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <div className="card h-40">
        <div className="text-sm text-gray-400 mb-2">전력 추이</div>
        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={historyData}>
            <XAxis dataKey="time" hide />
            <YAxis width={40} />
            <Tooltip />
            <Bar dataKey="power" name={t("pdu.totalPower")} fill="#34d399" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
