import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

const API = import.meta.env.VITE_API_URL || "";

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

  const tempData = [...(history || [])].reverse().map(r => ({
    time: new Date(r.timestamp).toLocaleTimeString("ko-KR"),
    upper: r.temp_upper,
    lower: r.temp_lower,
  }));

  const flowData = [...(history || [])].reverse().map(r => ({
    time: new Date(r.timestamp).toLocaleTimeString("ko-KR"),
    inlet: r.flow_upper,
    outlet: r.flow_lower,
  }));

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">{t("immersionTank.title")}</h2>

      {/* 온도 카드 */}
      <div className="card mb-4">
        <div className="text-sm text-gray-400 mb-3">냉각유 온도 (GS Fluid S 30)</div>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <StatBox
            label={t("immersionTank.tempUpper")}
            value={latest?.temp_upper}
            unit="°C"
            color="orange"
            warn={45} danger={55}
          />
          <StatBox
            label={t("immersionTank.tempLower")}
            value={latest?.temp_lower}
            unit="°C"
            color="cyan"
            warn={40} danger={50}
          />
        </div>
        <div className="h-36">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={tempData}>
              <XAxis dataKey="time" hide />
              <YAxis width={32} unit="°C" />
              <Tooltip formatter={(v, n) => [`${v}°C`, n]} />
              <Legend />
              <Line type="monotone" dataKey="upper" name={t("immersionTank.tempUpper")} stroke="#fb923c" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="lower" name={t("immersionTank.tempLower")} stroke="#22d3ee" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 유량 카드 */}
      <div className="card">
        <div className="text-sm text-gray-400 mb-3">냉각유 유량</div>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <StatBox
            label={t("immersionTank.flowUpper")}
            value={latest?.flow_upper}
            unit="LPM"
            color="blue"
          />
          <StatBox
            label={t("immersionTank.flowLower")}
            value={latest?.flow_lower}
            unit="LPM"
            color="purple"
          />
        </div>
        <div className="h-36">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={flowData}>
              <XAxis dataKey="time" hide />
              <YAxis width={32} unit="L" />
              <Tooltip formatter={(v, n) => [`${v} LPM`, n]} />
              <Legend />
              <Line type="monotone" dataKey="inlet"  name={t("immersionTank.flowUpper")} stroke="#60a5fa" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="outlet" name={t("immersionTank.flowLower")} stroke="#a78bfa" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, value, unit, color, warn, danger }) {
  const bg = { orange: "bg-orange-900", cyan: "bg-cyan-900", blue: "bg-blue-900", purple: "bg-purple-900" };
  const tx = { orange: "text-orange-200", cyan: "text-cyan-200", blue: "text-blue-200", purple: "text-purple-200" };
  const alertColor = danger && value >= danger ? "text-red-400" : warn && value >= warn ? "text-yellow-400" : "";
  return (
    <div className={`${bg[color]} rounded p-3 text-center`}>
      <div className={`text-xs ${tx[color]} opacity-70`}>{label}</div>
      <div className={`text-2xl font-bold mt-1 ${alertColor || tx[color]}`}>{value ?? "-"}</div>
      <div className={`text-xs ${tx[color]} opacity-70`}>{unit}</div>
    </div>
  );
}
