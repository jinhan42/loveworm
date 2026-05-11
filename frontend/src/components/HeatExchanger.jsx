import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function HeatExchanger() {
  const { t } = useTranslation();
  const { data: latest } = useQuery({
    queryKey: ["he-latest"],
    queryFn: () => axios.get(`${API}/api/heat-exchanger/latest`).then(r => r.data),
    refetchInterval: 10000,
  });
  const { data: history } = useQuery({
    queryKey: ["he-history"],
    queryFn: () => axios.get(`${API}/api/heat-exchanger/history?limit=60`).then(r => r.data),
    refetchInterval: 10000,
  });

  const chartData = [...(history || [])].reverse().map(r => ({
    time: new Date(r.timestamp).toLocaleTimeString("ko-KR"),
    water: r.water_lpm,
    oil: r.oil_lpm,
  }));

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">{t("heatExchanger.title")}</h2>
      <div className="card mb-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-900 rounded p-4 text-center">
            <div className="text-sm text-blue-300">{t("heatExchanger.waterFlow")}</div>
            <div className="text-3xl font-bold text-blue-200 mt-1">
              {latest?.water_lpm ?? "-"}
            </div>
            <div className="text-sm text-blue-400">{t("heatExchanger.unit")}</div>
          </div>
          <div className="bg-yellow-900 rounded p-4 text-center">
            <div className="text-sm text-yellow-300">{t("heatExchanger.oilFlow")}</div>
            <div className="text-3xl font-bold text-yellow-200 mt-1">
              {latest?.oil_lpm ?? "-"}
            </div>
            <div className="text-sm text-yellow-400">{t("heatExchanger.unit")}</div>
          </div>
        </div>
      </div>
      <div className="card h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <XAxis dataKey="time" hide />
            <YAxis width={30} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="water" name={t("heatExchanger.waterFlow")} stroke="#60a5fa" fill="#1e3a5f" strokeWidth={2} />
            <Area type="monotone" dataKey="oil"   name={t("heatExchanger.oilFlow")}  stroke="#fbbf24" fill="#422006" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
