# ECG Course CLI Reference
*This documentation is auto-generated from CLI help output.*
*Generated on: 2025-09-26 19:04:00*
## Main Command

```
[1m                                                                                                                        [0m
[1m [0m[1;33mUsage: [0m[1mpython [0m[1;32m-m[0m[1m ecgcourse.cli [OPTIONS] COMMAND [ARGS]...[0m[1m                                                            [0m[1m [0m
[1m                                                                                                                        [0m
 ECGCourse CLI — quizzes, análises e utilitários.

[2m╭─[0m[2m Options [0m[2m───────────────────────────────────────────────────────────────────────────────────────────────────────────[0m[2m─╮[0m
[2m│[0m [1;36m-[0m[1;36m-install[0m[1;36m-completion[0m          Install completion for the current shell.                                              [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-show[0m[1;36m-completion[0m             Show completion for the current shell, to copy it or customize the installation.       [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-help[0m                        Show this message and exit.                                                            [2m│[0m
[2m╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯[0m
[2m╭─[0m[2m Commands [0m[2m──────────────────────────────────────────────────────────────────────────────────────────────────────────[0m[2m─╮[0m
[2m│[0m [1;36mquiz    [0m[1;36m [0m                                                                                                            [2m│[0m
[2m│[0m [1;36manalyze [0m[1;36m [0m Análises de valores estruturados de ECG (p2).                                                              [2m│[0m
[2m╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯[0m


```

## Command: analyze

```
[1m                                                                                                                        [0m
[1m [0m[1;33mUsage: [0m[1mpython [0m[1;32m-m[0m[1m ecgcourse.cli analyze [OPTIONS] COMMAND [ARGS]...[0m[1m                                                    [0m[1m [0m
[1m                                                                                                                        [0m
 Análises de valores estruturados de ECG (p2).

[2m╭─[0m[2m Options [0m[2m───────────────────────────────────────────────────────────────────────────────────────────────────────────[0m[2m─╮[0m
[2m│[0m [1;36m-[0m[1;36m-help[0m          Show this message and exit.                                                                          [2m│[0m
[2m╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯[0m
[2m╭─[0m[2m Commands [0m[2m──────────────────────────────────────────────────────────────────────────────────────────────────────────[0m[2m─╮[0m
[2m│[0m [1;36mvalues [0m[1;36m [0m                                                                                                             [2m│[0m
[2m╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯[0m


```

## Command: quiz

```
[1m                                                                                                                        [0m
[1m [0m[1;33mUsage: [0m[1mpython [0m[1;32m-m[0m[1m ecgcourse.cli quiz [OPTIONS] ACTION PATH[0m[1m                                                             [0m[1m [0m
[1m                                                                                                                        [0m
[2m╭─[0m[2m Arguments [0m[2m─────────────────────────────────────────────────────────────────────────────────────────────────────────[0m[2m─╮[0m
[2m│[0m [31m*[0m    action      [1;33mTEXT[0m  run|validate|bank [2;31m[required][0m                                                                  [2m│[0m
[2m│[0m [31m*[0m    path        [1;33mTEXT[0m  arquivo .json (run/validate) ou diretório (bank) [2;31m[required][0m                                   [2m│[0m
[2m╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯[0m
[2m╭─[0m[2m Options [0m[2m───────────────────────────────────────────────────────────────────────────────────────────────────────────[0m[2m─╮[0m
[2m│[0m [1;36m-[0m[1;36m-report[0m                     [1;33m       [0m  salva relatórios em reports/                                                   [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-shuffle[0m    [1;35m-[0m[1;35m-no[0m[1;35m-shuffle[0m    [1;33m       [0m  embaralhar ordem no modo bank [2m[default: shuffle][0m                               [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-seed[0m                       [1;33mINTEGER[0m  seed para reprodutibilidade (0 = auto) [2m[default: 0][0m                            [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-help[0m                       [1;33m       [0m  Show this message and exit.                                                    [2m│[0m
[2m╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯[0m


```

## Command: ingest

*Error capturing help*

## Command: assets

*Error capturing help*

## Command: cv

*Error capturing help*

## Command: report

*Error capturing help*

## Command: checklist

*Error capturing help*

## Command: rhythm

*Error capturing help*

## Command: precordials

*Error capturing help*

