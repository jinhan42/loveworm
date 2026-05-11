import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "";

const STATUS_COLOR = {
  OK:      "text-green-400",
  Error:   "text-red-500",
  Absent:  "text-gray-500",
  Unknown: "text-yellow-400",
};

function StatusBadge({ value }) {
  const color = STATUS_COLOR[value] || "text-gray-400";
  return <span className={`font-bold ${color}`}>{value ?? "-"}</span>;
}

export default function ServerPanel() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery({
    queryKey: ["bmc-latest"],
    queryFn: () => axios.get(`${API}/api/bmc/latest`).then(r => r.data),
    refetchInterval: 30000,
  });

  if (isLoading) return <div className="card">{t("common.loading")}</div>;
  if (error)     return <div className="card text-red-500">{t("common.error")}</div>;

  const grouped = {};
  (data || []).forEach(r => {
    if (!grouped[r.host]) grouped[r.host] = r;
  });

  if (Object.keys(grouped).length === 0) {
    return <div className="card text-gray-400 text-center py-8">{t("common.noData")}</div>;
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">{t("bmc.title")}</h2>
      <div className="grid grid-cols-1 gap-4">
        {Object.entries(grouped).map(([host, r]) => (
          <div key={host} className="card">
            <div className="flex justify-between items-center mb-4">
              <span className="font-semibold text-blue-400 text-lg">{host}</span>
              <span className="text-xs text-gray-400">
                {r.timestamp ? new Date(r.timestamp).toLocaleString("ko-KR") : "-"}
              </span>
            </div>

            {/* CPU 상태 */}
            <div className="mb-3">
              <div className="text-xs text-gray-400 mb-2">CPU 상태</div>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-xs text-gray-400">CPU 0</div>
                  <StatusBadge value={r.cpu0_status} />
                </div>
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-xs text-gray-400">CPU 1</div>
                  <StatusBadge value={r.cpu1_status} />
                </div>
              </div>
            </div>

            {/* PSU 상태 */}
            <div className="mb-3">
              <div className="text-xs text-gray-400 mb-2">PSU 상태</div>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-xs text-gray-400">PSU 1</div>
                  <StatusBadge value={r.psu1_status} />
                </div>
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-xs text-gray-400">PSU 2</div>
                  <StatusBadge value={r.psu2_status} />
                </div>
              </div>
            </div>

            {/* 전력 정보 */}
            <div>
              <div className="text-xs text-gray-400 mb-2">전력 정보</div>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-xs text-gray-400">최대 전력</div>
                  <div className="text-lg font-bold text-green-400">
                    {r.power_capacity_watts != null ? `${r.power_capacity_watts} W` : "-"}
                  </div>
                </div>
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-xs text-gray-400">누적 에너지</div>
                  <div className="text-lg font-bold text-cyan-400">
                    {r.accumulated_energy_joules != null
                      ? `${(r.accumulated_energy_joules / 3600).toFixed(1)} Wh`
                      : "-"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
