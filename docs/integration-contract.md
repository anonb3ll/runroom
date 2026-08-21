# Optional integration with Citetrail

Runroom and [Citetrail](../../citetrail) are independent products. An optional
integration contract lives in the third repo
[`integration-contract`](../../integration-contract):

- Spec: [`integration-contract/CONTRACT.md`](../../integration-contract/CONTRACT.md)
- Demo: `integration-contract/examples/demo.sh`
- Evidence kind: `citetrail-reference-v1`

Neither repo lists the other as a packaging dependency. A Citetrail provenance
reference is projected into a Runroom run title/notes; the governed handoff and
review chain stays entirely in Runroom's append-only history.
