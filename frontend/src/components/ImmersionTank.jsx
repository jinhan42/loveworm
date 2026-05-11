import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function ImmersionTank() {
  const { t } = useTranslation();
  const { data: latest } = useQuery({
    queryKey: ["tank-latest"],
    queryFn: () => axios.get(`${API}/api/immersion-tank/latest`).then(r => r.data),
    refetchInterval: 10000,
  });
  const { data: history } = useQuery({
    queryKey: ["tank-history"],
    queryFn: () => axios.get(`${API}/api/immersion-tank/history?limit=60`).then(r => r.data),
    refetchInterval: 10000,
  });

  const chartData = [...(history || [])].reverse().map(r => ({
    time: new Date(r.timestamp).toLocaleTimeString("ko-KR"),
    upper: r.temp_upper,
    lower: r.temp_lower,
    flow: r.oil_flow,
  }));

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">{t("immersionTank.title")}</h2>
      <div className="card mb-4">
        <div className="grid grid-cols-3 gap-3">
          <StatBox
            label={t("immersionTank.tempUpper")}
            value={latest?.temp_upper}
            unit={t("immersionTank.unitTemp")}
            color="orange"
            warn={45} danger={55}
          />
          <StatBox
            label={t("immersionTank.tempLower")}
            value={latest?.temp_lower}
            unit={t("immersionTank.unitTemp")}
            color="cyan"
            warn={40} danger={50}
          />
          <StatBox
            label={t("immersionTank.oilFlow")}
            value={latest?.oil_flow}
            unit={t("immersionTank.unitFlow")}
            color="purple"
          />
        </div>
      </div>
      <div className="card h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <XAxis dataKey="time" hide />
            <YAxis width={30} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="upper" name={t("immersionTank.tempUpper")} stroke="#fb923c" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="lower" name={t("immersionTank.tempLower")} stroke="#22d3ee" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function StatBox({ label, value, unit, color, warn, danger }) {
  const colors = { orange: "bg-orange-900 text-orange-200", cyan: "bg-cyan-900 text-cyan-200", purple: "bg-purple-900 text-purple-200" };
  const textColor =
    danger && value >= danger ? "text-red-400" :
    warn && value >= warn ? "text-yellow-400" : "";
  return (
    <div className={`rounded p-3 text-center ${colors[color]}`}>
      <div className="text-xs opacity-70">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${textColor}`}>{value ?? "-"}</div>
      <div className="text-xs opacity-70">{unit}</div>
    </div>
  );
}
