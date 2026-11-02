"""Audit saved pilot contracts and render all-axis primary contrasts."""
from pathlib import Path
import csv
import hashlib
import json

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs/vector_integration_001_20261010"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(name):
    with (OUT/name).open(newline="",encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main():
    for name in ("extraction_manifest.json","analysis_manifest.json"):
        manifest = json.loads((OUT/name).read_text())
        for artifact,digest in manifest["outputs"].items():
            assert sha(OUT/artifact)==digest, artifact
        assert manifest["protocol_sha256"]==sha(HERE/"vector_integration_001_protocol_v1_20261010.yaml")
        assert manifest["runner_sha256"]==sha(HERE/"run_vector_integration_001.py")
    extraction = json.loads((OUT/"extraction_manifest.json").read_text())
    assert extraction["future_perturbation"]["passed"]
    assert len(extraction["input_qc"])==20
    assert all(r["fast_complete"]==39 and r["context_complete"]==12 for r in extraction["input_qc"])
    count = 0
    with (OUT/"measurements.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            r = json.loads(line)
            result = r["result"]
            assert result["realization"]["channel_labels"]==extraction["labels"]
            assert len(result["measurements"])==8
            assert all(row["qualified"] is False for row in result["measurements"])
            if r["window_sec"]==20:
                ar = next(row for row in result["measurements"] if row["candidate_id"]=="M3")
                assert len(ar["value"])==9
            count += 1
    assert count==1020
    predictions = read_csv("prediction_rows.csv")
    summaries = read_csv("prediction_summary.csv")
    assert len(predictions)==18000
    for summary in summaries:
        selected = [r for r in predictions if r["horizon_sec"]==summary["horizon_sec"] and r["model"]==summary["model"]
                    and (summary["axis"]=="all_raw_units" or r["axis"]==summary["axis"])]
        error = np.array([float(r["prediction"])-float(r["truth"]) for r in selected])
        np.testing.assert_allclose(np.sqrt(np.mean(error**2)),float(summary["pooled_rmse"]),rtol=1e-12)
        participants = sorted({r["participant_id"] for r in selected})
        macro = np.mean([np.sqrt(np.mean([(float(r["prediction"])-float(r["truth"]))**2 for r in selected if r["participant_id"]==p])) for p in participants])
        np.testing.assert_allclose(macro,float(summary["participant_macro_rmse"]),rtol=1e-12)
    contrasts = read_csv("paired_contrasts.csv")
    fig,axes = plt.subplots(1,2,figsize=(11,4.8),sharey=True)
    names = ["PCV","TP","OI","SC"]
    for ax,horizon in zip(axes,(4,8)):
        for base,color,shift,label in (("B_fast","#276FBF",-.10,"B fast minus C"),
                                       ("D_wrong_context","#A34E78",.10,"D stale context minus C")):
            chosen = [next(r for r in contrasts if int(r["horizon_sec"])==horizon and r["baseline"]==base and r["axis"]==name) for name in names]
            means = np.array([float(r["mean_participant_rmse_gain"]) for r in chosen])*1000
            lows = np.array([float(r["ci95_low"]) for r in chosen])*1000
            highs = np.array([float(r["ci95_high"]) for r in chosen])*1000
            ax.errorbar(means,np.arange(4)+shift,xerr=np.vstack((means-lows,highs-means)),fmt="o",color=color,label=label,capsize=3)
        ax.axvline(0,color="#666666",linewidth=1)
        ax.set_title(f"{horizon} s forecast")
        ax.set_xlabel("Participant mean RMSE gain × 1000\nPositive favors current 20 s context (C)")
        ax.grid(axis="x",alpha=.2)
        ax.spines[["top","right"]].set_visible(False)
    axes[0].set_yticks(range(4),names)
    axes[0].invert_yaxis()
    fig.legend(*axes[1].get_legend_handles_labels(),loc="upper center",bbox_to_anchor=(.5,.92),ncol=2,frameon=False,fontsize=10)
    fig.suptitle("VECTOR-INTEGRATION-001: added context did not establish forecast benefit",fontsize=12)
    fig.text(.5,.015,"20 held-out participants; paired bootstrap 95% intervals; exploratory scalp-six realization",ha="center",fontsize=9)
    fig.tight_layout(rect=(0,.055,1,.84))
    figure = OUT/"primary_contrasts.png"
    fig.savefig(figure,dpi=180)
    plt.close(fig)
    result = {"status":"passed_saved_artifact_audit","measurement_windows":count,"candidate_measurements":count*8,
              "prediction_rows":len(predictions),"summary_rows":len(summaries),
              "validator_sha256":sha(Path(__file__)),"figure_sha256":sha(figure),
              "analysis_manifest_sha256":sha(OUT/"analysis_manifest.json")}
    (OUT/"validation_manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
