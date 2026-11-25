# Offline feed evaluation

## Baselines

| Strategy | Mean NDCG@10 | 95% paired bootstrap interval | Users |
|---|---:|:---:|---:|
| chronological | 0.0000 | [0.0000, 0.0000] | 25 |
| popularity | 0.1012 | [0.0275, 0.1918] | 25 |
| for_you | 0.0030 | [0.0000, 0.0089] | 25 |
| learned | 0.0183 | [0.0000, 0.0421] | 25 |

## Learned minus best baseline

| Slice | Best baseline | Difference | 95% paired bootstrap interval | Verdict | Users |
|---|---|---:|:---:|:---:|---:|
| overall | popularity | -0.0829 | [-0.1592, -0.0232] | loses | 25 |
| new | popularity | -0.5032 | [-0.7467, -0.2597] | loses | 2 |
| casual | popularity | -0.0941 | [-0.2059, -0.0045] | loses | 9 |
| regular | popularity | -0.0314 | [-0.0943, 0.0000] | unclear | 7 |
| power | chronological | 0.0000 | [0.0000, 0.0000] | unclear | 7 |

## Run metadata

- Cut-off (UTC): `2016-02-04T21:34:50.000000+00:00`
- Bootstrap seed: `42`
- Evaluated users: `25`
- Database SHA-256: `8cc8cd6fc23fca777d2f88d6d9a3edd381f58e8649433164f0a04c5b5140fb51`
- Git commit: `68a3bc67d948ecfdba659a29340174e107b1e9ca`
