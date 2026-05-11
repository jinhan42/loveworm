import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function ServerPanel() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery({
    queryKey: ["bmc-latest"],
    queryFn: () => axios.get(`${API}/api/bmc/latest`).then(r => r.data),
    refetchInterval: 30000,
  });

  if (isLoading) return <div className="card">{t("common.loading")}</div>;
  if (error) return <div className="card text-red-500">{t("common.error")}</div>;

  const grouped = {};
  (data || []).forEach(r => {
    if (!grouped[r.host]) grouped[r.host] = [];
    grouped[r.host].push(r);
  });

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">{t("bmc.title")}</h2>
      <div className="grid grid-cols-1 gap-4">
        {Object.entries(grouped).map(([host, records]) => {
          const latest = records[0];
          return (
            <div key={host} className="card">
              <div className="flex justify-between items-center mb-3">
                <span className="font-semibold text-blue-400">{t("bmc.host")}: {host}</span>
                <span className="text-xs text-gray-400">
                  {latest.timestamp ? new Date(latest.timestamp).toLocaleString("ko-KR") : "-"}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Metric label={t("bmc.cpuTemp")} value={latest.cpu_temp} unit="°C" warn={80} danger={90} />
                <Metric label={t("bmc.psuPower")} value={latest.psu_power} unit="W" />
                <Metric label={t("bmc.psuVoltage")} value={latest.psu_voltage} unit="V" />
                <Metric label={t("bmc.psuCurrent")} value={latest.psu_current} unit="A" />
              </div>
              <div className="mt-3 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={[...records].reverse()}>
                    <XAxis dataKey="timestamp" hide />
                    <YAxis domain={["auto", "auto"]} width={30} />
                    <Tooltip formatter={(v) => [`${v}°C`, t("bmc.cpuTemp")]} />
                    <Line type="monotone" dataKey="cpu_temp" stroke="#60a5fa" dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Metric({ label, value, unit, warn, danger }) {
  const color =
    danger && value >= danger ? "text-red-500" :
    warn && value >= warn ? "text-yellow-400" : "text-green-400";
  return (
    <div className="bg-gray-700 rounded p-2">
      <div className="text-xs text-gray-400">{label}</div>
      <div className={`text-lg font-bold ${color}`}>
        {value != null ? `${value} ${unit}` : "-"}
      </div>
    </div>
  );
}
