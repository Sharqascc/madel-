# Evaluation Framework

This document describes how the speed safety screening model can be validated, stress-tested, and calibrated against empirical transport safety evidence.

## Objective

The goal is not only to generate plausible scores, but to demonstrate that lower scores and more urgent labels correspond to locations with higher observed crash severity, greater VRU exposure, or stronger evidence of unsafe speed environments.

## Recommended validation path

1. Join scored road segments with crash records using segment ID, linear referencing, or nearest-link spatial matching.
2. Aggregate crashes by severity, mode, and time period.
3. Test whether lower `speed_safety_score` values are associated with higher severe-crash density or higher VRU crash incidence.
4. Compare label groups (`aligned`, `monitor`, `review`, `high_priority_review`) against observed safety outcomes.
5. Recalibrate thresholds and weights where regional evidence suggests different sensitivities.

## Suggested metrics

- Severe crashes per km per year.
- VRU crashes per km per year.
- Fatal and serious injury share.
- Mean operating speed exceedance.
- Rank-order correlation between score and crash density.
- Lift in high-risk capture among the bottom-scoring segments.

## Calibration guidance

Calibration should prioritize interpretability. Weights, score transforms, and escalation rules should only be modified when empirical evidence and domain review both support the change.

A practical approach is:
- hold out one geography or time period for validation;
- tune thresholds on the development subset;
- confirm that performance generalizes on the holdout subset.

## Reviewer note

Because the challenge dataset may be access-restricted, the repository includes a synthetic pipeline for functional demonstration. Final calibration should be conducted only after secure access to the official or partner crash and road-network data.
