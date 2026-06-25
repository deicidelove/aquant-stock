import { useState } from "react";
import { useSubmitFactorIc, useFactorIcJob } from "../hooks/queries";
import FactorIcPanel from "../components/FactorIcPanel";

export default function QuantFactors() {
  const [jobId, setJobId] = useState<string | null>(null);
  const submit = useSubmitFactorIc();
  const job = useFactorIcJob(jobId);
  const run = () => submit.mutate({ fwd: 5 }, { onSuccess: (d: { job_id: string }) => setJobId(d.job_id) });

  const status = job.data?.status;
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">因子</h1>
      <button onClick={run} className="rounded bg-blue-600 px-3 py-1 text-white">跑因子IC</button>
      {jobId && status !== "done" && status !== "error" && <p className="text-sm text-gray-400">计算中…</p>}
      {status === "error" && <p className="text-sm text-red-600">失败：{job.data?.error}</p>}
      {status === "done" && job.data?.result && <FactorIcPanel rows={job.data.result.rows} />}
    </div>
  );
}
