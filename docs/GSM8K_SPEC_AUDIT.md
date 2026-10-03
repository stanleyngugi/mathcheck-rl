# Bounded question-to-specification audit — 2026-10-03

Scope: the five selected official training questions and one known public-test
demonstration. This review uses question-only files, quantities, units, operation
order, domains and objectives. It is a same-assistant-context audit, not an
independent review or a native/policy evaluation. Source solution fields are not
used. No expected candidate is added to a task or reward input.

| Source | Semantic model and decision |
| --- | --- |
| train:0 | The given 48 counts friends. Concluding 48 clips requires an unstated one-clip-per-friend relation. The previous `48+48//2` contract made that assumption. Exclude this item from the strict slice. |
| train:1 | Hourly earnings multiplied by duration in hours. Convert 50 minutes using the standard 60 minutes per hour: `(12*50)//60`. The product is divisible by 60, so this instance uses exact division and yields a nonnegative integer. Include. |
| train:2 | Remaining wallet cost after existing savings and both gifts. Savings are half the price; the grandparents' gift is twice the collective parents' gift: `100-100//2-15-2*15`. The objective is the shortfall, the half-price division is exact, and the shortfall is nonnegative. Include. |
| train:3 | Subtract the two reading sessions from the book length, then take half the unread pages: `(120-12-2*12)//2`. The second session is twice the first, and the outer division is exact. Include. |
| train:4 | A weekly rate is given but no exact number of weeks per year. Preserve the exclusion instead of silently introducing 52. |
| test:0 | Daily eggs minus both consumption uses, multiplied by per-egg selling price: `(16-3-4)*2`. The objective is daily sales revenue. No unstated production costs are subtracted. Include as an already known public-test demonstration. |

The refreshed development manifest admits **3 of 5** selected questions and
records **2 exclusions**. This tiny coverage figure describes this admission
policy and selection only; it is not an estimate of whole-dataset coverage.
The evaluation-demonstration manifest admits one known public-test question.
Its role remains a demonstration, not a fresh held-out measurement.

The old four-contract development manifest is preserved in Git history. Earlier
eight-control records tested those encoded contracts, not their prose fidelity;
they must not be relabeled as a completed fidelity review. The current slice
has six development candidate controls and two public-test controls. Native
completion remains a separate gate.

A data pipeline that intentionally adopts the standard intended interpretation
of train:0 can state and review its one-clip-per-friend assumption explicitly.
That would be a new admitted specification with new provenance. It is outside
this closed strict demonstration and does not extend the audit's finish line.

Independent review is required for future independent dataset-evaluation claims.
This disclosed, small, manually interpreted demonstration makes no such claim.
