SC2001 Project 1 - Hybrid Merge/Insertion Sort
===============================================

This folder contains the SC2001 Project 1 implementation and experiment
scripts. The project compares a hybrid merge sort/insertion sort algorithm
against the original recursive merge sort and measures key comparisons and
CPU time for different threshold values S.

Files
-----
project1_hybrid_sort.py
    Sorting algorithms, correctness tests, experiment runners, timing, and
    CSV output.

plot_results.py
    Reads results.csv, creates summary.csv and optimal_thresholds.csv, and
    generates presentation charts in the figures folder.

Lab1.py
    Small 20-element teaching/demo pipeline with comparison tracing.

results.csv
    Raw experiment results. Each timing trial is stored as one row.

summary.csv
    Median results grouped by experiment, algorithm, n, and S.

optimal_thresholds.csv
    Lowest measured median CPU time for each c(iii) input size, among the
    tested threshold values.

figures/
    Generated PNG charts.

*_preliminary_one_trial.csv
    Backups of the preliminary one-trial outputs, when available.

Requirements
------------
- Python 3.10 or newer is recommended.
- Python standard library modules are used by project1_hybrid_sort.py.
- plot_results.py requires numpy, pandas, and matplotlib.

Setup
-----
Open a terminal in this directory:

    cd SchoolWork/SC2001/Lab/Lab1

Create and activate an optional virtual environment:

Windows PowerShell:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

Install plotting dependencies:

    python -m pip install -r requirement.txt

Quick validation
----------------
Run the built-in correctness tests:

    python project1_hybrid_sort.py test

Print timing and trial diagnostics:

    python project1_hybrid_sort.py diagnostics

Run the small c(iii) experiment with three trials:

    python project1_hybrid_sort.py optimal --small --trials 3

Generate the charts from the current results.csv:

    python plot_results.py

The small c(iii) run tests:
- n = 5,000, 20,000, 100,000
- S = 4, 8, 12, 16, 24, 32, 48, 64, 96
- 3 timing trials for every (n, S) pair

Experiment commands
-------------------
Run only c(iii) using the full input sizes:

    python project1_hybrid_sort.py optimal --full --trials 3

Run only the threshold sweep c(ii):

    python project1_hybrid_sort.py threshold --full --trials 3

Run only the growth experiment c(i):

    python project1_hybrid_sort.py growth --full --trials 3

Run only the merge-sort comparison using hybrid S = 12:

    python project1_hybrid_sort.py compare --full --trials 3 --S 12

Run every experiment:

    python project1_hybrid_sort.py all --full --trials 3
    python plot_results.py

The full run performs 138 timed sorts:
- Growth: 5 input sizes x 3 trials = 15
- Threshold sweep: 12 thresholds x 3 trials = 36
- c(iii): 3 input sizes x 9 thresholds x 3 trials = 81
- Comparison: 2 algorithms x 3 trials = 6

Full input sizes include 10,000,000 elements. The full experiment may take a
long time and requires substantial memory. Do not start it if the computer
cannot accommodate a large Python list and temporary merge arrays.

Outputs and interpretation
--------------------------
The experiment writes results.csv in this directory. Running a new experiment
replaces that file. The script preserves existing preliminary outputs using
these names when those backups do not already exist:

- results_preliminary_one_trial.csv
- summary_preliminary_one_trial.csv
- optimal_thresholds_preliminary_one_trial.csv

Run plot_results.py after changing results.csv. It regenerates summary.csv,
optimal_thresholds.csv, and the charts.

Generated charts include:

- figures/01_comparisons_vs_n.png
- figures/02_effect_of_S.png
- figures/03_optimal_S.png
- figures/03b_relative_slowdown.png
- figures/04_merge_vs_hybrid.png

The c(iii) threshold is reported as the lowest measured median among the
tested S values for this implementation and environment. It is not a universal
optimal threshold. The charts also show near-optimal tested ranges within the
configured 2 percent tolerance.

Timing notes
------------
- Each trial receives a fresh unsorted copy of the same seeded base array.
- Data generation, copying, sortedness validation, CSV writing, and plotting
  are outside the timed sorting region.
- CPU timing varies with operating-system scheduling, background processes,
  CPU frequency, cache state, and timer resolution.
- Key comparison counts should remain deterministic for the same n, seed, and
  S. The experiment prints a warning if repeated comparison counts differ.
- CPU time is not determined only by key comparisons. It also includes
  recursion overhead, merge/copy operations, insertion-sort shifts, memory
  effects, and Python interpreter overhead.

Raw CSV schema
--------------
experiment,algorithm,n,S,seed,trial,comparisons,cpu_seconds,wall_seconds,sorted

The plotting summary additionally includes trial_count. All reported results
must have sorted=True.

Platform notes
--------------
The scripts use paths relative to their own directory and should run on
Windows, macOS, and Linux. Use python3 instead of python on systems where
python points to an older interpreter.
