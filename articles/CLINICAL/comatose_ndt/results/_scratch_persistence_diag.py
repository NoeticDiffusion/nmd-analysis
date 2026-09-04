import pandas as pd, numpy as np
w = pd.read_csv(r'articles/CLINICAL/comatose_ndt/results/_scratch_subject_feature_matrix.csv', index_col=0)
core = [c for c in w.columns if 'persistence' in c and 'hysteresis' not in c and 'tau' not in c]
print("core persistence:", [c.split("::")[1] for c in core])
for c in core:
    v = w[c]
    name = c.split("::")[1]
    print(f"{name:28s} nan={v.isna().mean():.2f} nuniq={v.nunique():4d} "
          f"min={v.min():.3g} med={v.median():.3g} max={v.max():.3g}")

sub = w[core].dropna()
sub.columns = [c.split("::")[1] for c in core]
print("\nrank corr among core persistence metrics:")
print(sub.rank().corr().round(3).to_string())

print("\ncollapse check (fraction of subjects at modal rounded value):")
for c in core:
    v = w[c].dropna()
    mode = v.round(6).mode().iloc[0]
    print(f"{c.split('::')[1]:28s} modal={mode:.4g} frac_at_mode={(v.round(6)==mode).mean():.2f}")

# tau (recovery time) — does it hit the horizon ceiling?
taus = [c for c in w.columns if 'persistence_tau' in c]
print("\ntau (recovery-time) ceiling check:")
for c in taus:
    v = w[c].dropna()
    print(f"{c.split('::')[1]:32s} med={v.median():.3g} max={v.max():.3g} "
          f"frac_at_max={(v.round(3)==round(v.max(),3)).mean():.2f}")
