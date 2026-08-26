import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const API = import.meta.env.VITE_API_URL || "";

function kw(watt) {
  if (watt == null) return "-";
  return `${(watt / 1000).toFixed(1)}kW`;
}

function PduCard({ name, unit, t }) {
  if (!unit || !unit.online) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <span className="font-bold">{name}</span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">
            {t("pdu.offline")}
          </span>
        </div>
        <div className="text-sm text-gray-500">{t("common.noData")}</div>
      </div>
    );
  }

  const normal = !unit.alarm;

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <span className="font-bold">{name}</span>
        <span
          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
            normal ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"
          }`}
        >
          {normal ? t("pdu.normalOn") : t("pdu.alarm")}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-gray-400 mb-1">{t("pdu.voltage")}</div>
          <div className="text-xl font-bold text-green-400">{unit.voltage?.toFixed?.(1) ?? unit.voltage} V</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 mb-1">{t("pdu.current")}</div>
          <div className="text-xl font-bold text-green-400">{unit.current?.toFixed?.(1) ?? unit.current} A</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 mb-1">{t("pdu.power")}</div>
          <div className="text-xl font-bold text-green-400">{kw(unit.power)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 mb-1">{t("pdu.loadRate")}</div>
          <div className="text-xl font-bold text-green-400">{unit.load_rate?.toFixed?.(0) ?? unit.load_rate}%</div>
        </div>
      </div>
    </div>
  );
}

export default function PDUPanel() {
  const { t } = useTranslation();
  const { data } = useQuery({
    queryKey: ["pdu-latest"],
    queryFn: () => axios.get(`${API}/api/pdu/latest`).then(r => r.data),
    refetchInterval: 5000,
  });

  const units = data?.units || {};
  const unitNames = Object.keys(units);

  const chartData = [
    ...unitNames.map(name => ({
      name,
      kw: units[name]?.online ? +(units[name].power / 1000).toFixed(2) : 0,
      isTotal: false,
    })),
    { name: t("pdu.grandTotal"), kw: data ? +((data.total_power ?? 0) / 1000).toFixed(2) : 0, isTotal: true },
  ];

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">{t("pdu.title")}</h2>

      <div className="text-sm text-gray-400 mb-3">
        {data ? `${data.online_count}/${data.total_count} ${t("pdu.connected")}` : t("common.loading")}
      </div>

      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="card summary-card">
          <div className="text-xs text-gray-400 mb-1">{t("pdu.serverTotal")}</div>
          <div className="text-2xl font-bold text-blue-400">{kw(data?.server_power)}</div>
        </div>
        <div className="card summary-card">
          <div className="text-xs text-gray-400 mb-1">{t("pdu.tankCduTotal")}</div>
          <div className="text-2xl font-bold text-blue-400">{kw(data?.tank_cdu_power)}</div>
        </div>
        <div className="card summary-card">
          <div className="text-xs text-gray-400 mb-1">{t("pdu.grandTotal")}</div>
          <div className="text-2xl font-bold text-blue-400">{kw(data?.total_power)}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        {unitNames.map(name => (
          <PduCard key={name} name={name} unit={units[name]} t={t} />
        ))}
      </div>

      <div className="card h-56">
        <div className="text-sm text-gray-400 mb-2">{t("pdu.powerByUnit")}</div>
        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#9ca3af" }} />
            <YAxis width={40} tick={{ fontSize: 11, fill: "#9ca3af" }} unit="kW" />
            <Tooltip formatter={v => [`${v} kW`]} contentStyle={{ background: "#1f2937", border: "none" }} />
            <Bar dataKey="kw" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.isTotal ? "#60a5fa" : "#4ade80"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
