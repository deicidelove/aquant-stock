import { useState } from "react";
import { useQuantWeights, useSubmitBacktest, useBacktestJob } from "../hooks/queries";
import BacktestForm from "../components/BacktestForm";
import MetricsCard from "../components/MetricsCard";
import EChart from "../charts/EChart";
import { buildNavLineOption } from "../charts/options";

export default function QuantBacktest() {
  const [jobId, setJobId] = useState<string | null>(null);
  const weights = useQuantWeights();
  const submit = useSubmitBacktest();
  const job = useBacktestJob(jobId);

  const run = (params: Parameters<typeof submit.mutate>[0]) =>
    submit.mutate(params, { onSuccess: (d: { job_id: string }) => setJobId(d.job_id) });

  const status = job.data?.status;
  const result = job.data?.result;
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">回测</h1>
      {weights.isSuccess && <BacktestForm presets={weights.data} onSubmit={run} />}
      {jobId && status !== "done" && status !== "error" && <p className="text-sm text-gray-400">回测中…</p>}
      {status === "error" && <p className="text-sm text-red-600">回测失败：{job.data?.error}</p>}
      {status === "done" && result && (
        <>
          <MetricsCard metrics={result.metrics} />
          <section className="rounded-lg border border-gray-200 p-4">
            <h2 className="text-lg font-bold">净值曲线</h2>
            <EChart option={buildNavLineOption(result.nav)} height={360} />
          </section>
        </>
      )}
    </div>
  );
}
