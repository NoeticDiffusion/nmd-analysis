# Parkinson walking article exports

## Retained counts

- `cohort_walk_standard`: total=37, q<0.05=4, q<0.1=4
- `pd_subject_standard`: total=37, q<0.05=3, q<0.1=4
- `hc_subject_context`: total=37, q<0.05=1, q<0.1=3
- `cohort_walk_regional`: total=128, q<0.05=2, q<0.1=11
- `cohort_rest_reachability`: total=82, q<0.05=9, q<0.1=13
- `cohort_rest_trajectory`: total=24, q<0.05=4, q<0.1=7
- `cohort_rest_global_rho`: total=333, q<0.05=17, q<0.1=24
- `subject_anchor_global_rho`: total=575, q<0.05=2, q<0.1=10
- `cohort_rest_regional_rho`: total=1143, q<0.05=113, q<0.1=158
- `cohort_rest_trajectory_rho`: total=216, q<0.05=7, q<0.1=23

## Main-text focal rows

- `cohort_walk` / `Global walk d_n_mean`: d=0.7658, q=0.03018, left=0.1791, right=1.003 (Primary between-group headline row)
- `cohort_walk` / `Global walk d_n_median`: d=0.746, q=0.03018, left=0.08343, right=0.9874 (Median companion to d_n_mean)
- `cohort_walk` / `Global walk d_mean`: d=0.7109, q=0.03581, left=-0.8733, right=0.04965 (Signed family shift in walk task)
- `cohort_walk` / `Global walk d_median`: d=0.7185, q=0.03581, left=-1.021, right=-0.008324 (Median companion to d_mean)
- `pd_walk_vs_rest` / `PD paired d_n_mean`: d=0.4089, q=0.001038, left=0.003687, right=0.1101 (Primary paired headline row)
- `pd_walk_vs_rest` / `PD paired d_mean`: d=0.3506, q=0.005997, left=-0.01678, right=0.07233 (Companion paired family shift)
- `pd_walk_vs_rest` / `PD paired jac9 anisotropy`: d=0.2137, q=0.03226, left=1.763, right=1.823 (Paired Jacobian adjunct retained at q<0.05)

## Secondary/context rows

- `hc_walk_vs_rest` / `HC paired m_a_mean`: d=0.8884, q=0.01758, left=-0.146, right=0.07362 (Only HC paired row at q<0.05)
- `hc_walk_vs_rest` / `HC paired m_mean`: d=0.6822, q=0.08276, left=-0.007218, right=0.09082 (Secondary context near the q<0.1 boundary)
- `hc_walk_vs_rest` / `HC paired d_l_mean`: d=0.6563, q=0.08276, left=-0.1328, right=0.1536 (Secondary context near the q<0.1 boundary)

## Supportive supplement rows

- `cohort_walk_regional` / `Frontal walk d_n_mean`: rho=nan, q=0.004893, left=4.523, right=5.476, clinical=`nan`, network=`frontal` (Strongest regional walk replication)
- `cohort_walk_regional` / `Frontal walk d_n_median`: rho=nan, q=0.004851, left=4.465, right=5.503, clinical=`nan`, network=`frontal` (Median companion regional walk replication)
- `cohort_rest_reachability` / `Rest global pred_err_h2`: rho=nan, q=0.02347, left=2.03, right=1.759, clinical=`nan`, network=`global` (Best corrected reachability row)
- `cohort_rest_reachability` / `Rest global tube_log_det_mean`: rho=nan, q=0.02347, left=-10.56, right=-12.28, clinical=`nan`, network=`global` (Volume-style companion reachability row)
- `cohort_rest_global_rho` / `Rest age vs d_s_mean`: rho=-0.4031, q=0.0002678, left=nan, right=nan, clinical=`age` (Strongest global age association)
- `cohort_rest_global_rho` / `Rest CTT vs d_s_mean`: rho=-0.4148, q=0.00027, left=nan, right=nan, clinical=`ctt` (Strongest global executive-function association)
- `cohort_rest_global_rho` / `Rest MoCA vs d_s_mean`: rho=0.3513, q=0.005042, left=nan, right=nan, clinical=`moca` (Strongest global cognition association)
- `cohort_rest_regional_rho` / `Rest central d_s_mean vs CTT`: rho=-0.4325, q=0.0001815, left=nan, right=nan, clinical=`ctt`, network=`central` (Strongest regional executive-function association)
- `cohort_rest_regional_rho` / `Rest frontal d_s_mean vs age`: rho=-0.4094, q=0.0004884, left=nan, right=nan, clinical=`age`, network=`frontal` (Strongest regional age association)
- `subject_global_rho` / `Subject rest e_mean vs MoCA`: rho=-0.3115, q=0.02745, left=nan, right=nan, clinical=`moca` (Only subject-anchor rest global rho at q<0.05)
- `subject_global_rho` / `Subject walk jac9 spectral radius vs age`: rho=-0.3289, q=0.01311, left=nan, right=nan, clinical=`age` (Only subject-anchor walk global rho at q<0.05)

## Exploratory-only rows

- `cohort_rest_trajectory` / `Rest 3D noetic_action_kinetic`: rho=nan, q=0.01209, left=0.006168, right=0.004328, clinical=`nan`, dim=`3` (Best exploratory trajectory row)
- `cohort_rest_trajectory` / `Rest 3D path_length`: rho=nan, q=0.01209, left=32.4, right=27.8, clinical=`nan`, dim=`3` (Exploratory trajectory companion row)
- `cohort_rest_trajectory_rho` / `Rest 3D noetic_action vs CTT`: rho=-0.2476, q=0.05655, left=nan, right=nan, clinical=`ctt`, dim=`3` (Strongest exploratory trajectory rho row)
- `cohort_rest_trajectory_rho` / `Rest 9D tortuosity vs MoCA`: rho=-0.148, q=0.454, left=nan, right=nan, clinical=`moca`, dim=`9` (Strongest exploratory 9D trajectory cognition row)
