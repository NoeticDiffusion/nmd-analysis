// Keep Langell (2026) year letters aligned with the main manuscript in every
// supplement. The letters follow the main manuscript's APA bibliography.
#let langell-year = (
  "langell2025ndt": "2026a",
  "langell2026_dandi000458": "2026b",
  "langell2026_ibl2": "2026c",
  "langell2026_truth_known": "2026d",
  "langell2026_thalamic_access": "2026e",
  "langell2026_trn_geometry": "2026f",
  "langell2026_ta_rolon": "2026g",
  "langell2026_hels_a": "2026h",
  "langell2026_slow_branch": "2026i",
  "langell2026_rvc_spindles": "2026j",
  "langell2026_coma_v011": "2026k",
  "langell2026_avb_omission": "2026l",
  "langell2026_dandi000574": "2026m",
  "langell2026_ndt_theories": "2026n",
)

#let langell-cite = it => {
  let k = str(it.key)
  if k.starts-with("<") { k = k.slice(1, k.len() - 1) }
  if k in langell-year {
    [#hide(it) (Langell, #langell-year.at(k))]
  } else {
    it
  }
}
