import h5py, numpy as np, sys

f = r"data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260601_131927_part1_combat/sub-0284_post_cardiac_arrest_coma_continuous_eeg_run-001_acq-004/sub-0284_post_cardiac_arrest_coma_continuous_eeg_run-001_acq-004.h5"

def walk(g, prefix=""):
    for k in g.keys():
        item = g[k]
        path = f"{prefix}/{k}"
        if isinstance(item, h5py.Group):
            print(f"GROUP  {path}  attrs={dict(item.attrs)}")
            walk(item, path)
        else:
            print(f"DSET   {path}  shape={item.shape} dtype={item.dtype}")

with h5py.File(f, "r") as h:
    print("=== ROOT attrs ===")
    for k, v in h.attrs.items():
        print(f"  {k} = {v}")
    print("\n=== TREE ===")
    walk(h)
