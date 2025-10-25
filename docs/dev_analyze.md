# Dev — analyze values (p2)

## Entradas
- `--pr` (ms), `--qrs` (ms), `--qt` (ms), `--rr` (ms) ou `--fc` (bpm)
- `--lead-i` e `--avf` (mV líquidos do QRS; positivos se R>S)
- `--sexo` (M/F) para limiares de QTc (M:450, F:470); se ausente, usa 460 ms

## Saídas
- FC, QTc (Bazett, Fridericia), eixo (rótulo + ângulo aproximado), flags
- Relatórios `reports/*_analyze_values.json|.md`

> Uso educacional.
