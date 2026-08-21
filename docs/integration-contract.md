# Optional integration with Citetrail

Runroom and [Citetrail](https://github.com/anonb3ll/citetrail) are independent products. An optional
integration contract lives in the third repo
[citetrail-runroom-contract](https://github.com/anonb3ll/citetrail-runroom-contract):

- Spec: [CONTRACT.md](https://github.com/anonb3ll/citetrail-runroom-contract/blob/main/CONTRACT.md)
- Demo: `examples/demo.sh` in that repository
- Evidence kind: `citetrail-reference-v1`

Neither repo lists the other as a packaging dependency. A Citetrail provenance
reference is projected into a Runroom run title/notes; the governed handoff and
review chain stays entirely in Runroom's append-only history.
