# Guia de Contexto Robusto do Projeto: Megaprojeto ECG

Este documento serve como um guia de contexto aprofundado para a IA (Gemini) e para desenvolvedores, detalhando a arquitetura, fluxos de dados, estruturas de dados, convenções e guias de análise do Megaprojeto ECG.

## 1. Resumo do Projeto (Missão)

O objetivo é construir o maior curso open-source, interativo e clínico de Eletrocardiografia (ECG) para médicos. A plataforma combina uma **CLI didática**, uma **aplicação web dinâmica**, **IA assistiva** para laudos e tutoria, **quizzes com feedback** e **simulações fisiológicas**. O projeto evolui de forma iterativa, com cada "Parte" (p0, p1, p2...) adicionando funcionalidades significativas.

**Pilares:**
- **Precisão Clínica:** Conteúdo revisado e baseado em evidências.
- **Didática Pragmática:** Foco na aplicação prática e na tomada de decisão.
- **Interatividade Pesada:** Aprendizagem ativa através de quizzes, simulações e casos.
- **Automação e IA:** Uso de Computer Vision e LLMs para analisar imagens de ECG e gerar conteúdo.
- **Transparência e Open Source:** Código e conteúdo abertos para a comunidade.

## 2. Arquitetura, Tecnologias e Fluxo de Dados

### 2.1. Componentes Principais
- **CLI (`cli_app/`):** Com **Typer** e **Rich**, é a porta de entrada para análises, gerenciamento de assets e quizzes.
- **Web App (`web_app/`):** Usa **Plotly Dash** para dashboards interativos e um **Case Player** estático (HTML/JS) para portabilidade e deploy no GitHub Pages.
- **Módulo de Computer Vision (`cv/`):** O núcleo analítico, usando **OpenCV**, **scipy**, e **numpy** para extrair dados clínicos de imagens.
- **Motor de Quiz (`quiz/`):** Valida e executa quizzes a partir de um banco de questões em JSON.
- **Relatórios (`reporting/`):** Gera laudos em JSON, Markdown e HTML a partir dos dados extraídos.
- **CI/CD (`.github/workflows/`):** Automação com GitHub Actions para pipeline de assets e deploy.

### 2.2. Fluxo de Dados Principal
O fluxo de análise de uma imagem de ECG segue uma sequência lógica:

```
Imagem (PNG/JPG) -> [CLI: `ecgcourse ingest image`] -> Pipeline de CV (`cv/`) -> Laudo Estruturado (JSON) -> [Saídas]
                                                                                                           |
                                                                                                           +-> Relatório (HTML/MD)
                                                                                                           +-> Dashboard (Dash)
                                                                                                           +-> Quiz Gerado (JSON)
```

## 3. Guia de Análise de ECG (Ordem Lógica)

O software emula a abordagem sistemática de um cardiologista para interpretar um ECG:

1.  **Calibração e Qualidade:** Verifica a calibração (N, 10 mm/mV; 25 mm/s) e a qualidade da imagem (deskew, remoção de ruído).
2.  **Ritmo e Frequência Cardíaca (FC):** Determina o ritmo (sinusal, etc.) e calcula a FC a partir dos intervalos R-R. (Origem: `cv/rhythm.py`, `cv/rpeaks_robust.py`)
3.  **Intervalos e Durações:** Mede os intervalos PR, a duração do QRS e o intervalo QT. Calcula o QTc para corrigir pela FC. (Origem: `cv/intervals_refined.py`)
4.  **Eixo Elétrico:** Calcula o eixo do QRS no plano frontal para determinar sua posição. (Origem: `cv/axis_hexaxial.py`)
5.  **Análise Morfológica:** Avalia a morfologia de ondas P, complexos QRS e alterações de ST-T (a ser aprofundado em partes futuras).
6.  **Sobrecargas e Hipertrofias:** Aplica critérios de voltagem para detectar hipertrofia ventricular esquerda (HVE). (Origem: `cv/hypertrophy_extended.py`)
7.  **Distúrbios de Condução:** Analisa a duração e morfologia do QRS para identificar bloqueios de ramo. (Origem: `cv/blocks.py`)
8.  **Síntese e Laudo:** Agrega todos os achados em um laudo estruturado com interpretações sugeridas. (Origem: `reporting/export.py`)

## 4. Estrutura de Dados Detalhada: Laudo ECG (`report.schema.v0.5.json`)

Esta é a estrutura central do projeto.

- **`intervals_refined`**
    - **Origem:** `cv/intervals_refined.py`
    - **Descrição:** Medidas robustas dos intervalos e FC.
    - **Campos Chave:**
        - `heart_rate_bpm`: (number) Frequência cardíaca mediana. Ex: `75.0`
        - `pr_interval_ms`: (number) Intervalo PR mediano. Ex: `160.0`
        - `qrs_duration_ms`: (number) Duração do QRS mediano. Ex: `94.0`
        - `qt_interval_ms`: (number) Intervalo QT mediano. Ex: `400.0`
        - `qtc_bazett_ms`: (number) QT corrigido por Bazett. Ex: `430.0`
        - `qtc_fridericia_ms`: (number) QT corrigido por Fridericia. Ex: `425.0`

- **`axis_hex`**
    - **Origem:** `cv/axis_hexaxial.py`
    - **Descrição:** Eixo elétrico calculado pelo sistema hexaxial.
    - **Campos Chave:**
        - `angle_deg`: (number) Ângulo do eixo em graus. Ex: `55.0`
        - `label`: (string) Classificação do eixo. Ex: `"Eixo normal"`

- **`rhythm`**
    - **Origem:** `cv/rhythm.py`
    - **Descrição:** Análise do ritmo cardíaco.
    - **Campos Chave:**
        - `mean_hr_bpm`: (number) FC média. Ex: `78.2`
        - `sdnn_ms`: (number) Desvio padrão dos intervalos NN, um marcador de variabilidade. Ex: `55.4`
        - `label`: (string) Heurística de classificação do ritmo. Ex: `"Ritmo sinusal com arritmia sinusal"`

- **`hypertrophy_extended`**
    - **Origem:** `cv/hypertrophy_extended.py`
    - **Descrição:** Critérios para Hipertrofia Ventricular Esquerda (HVE).
    - **Campos Chave:**
        - `sokolow_lyon_mm`: (number) Soma de S em V1 + R em V5/V6. Ex: `34.0`
        - `cornell_voltage_mm`: (number) Soma de R em aVL + S em V3. Ex: `27.0`
        - `cornell_product_mms`: (number) Produto de Cornell (voltagem x duração QRS). Ex: `2538.0`
        - `positive_criteria`: (array of strings) Lista de critérios positivos. Ex: `["cornell_voltage_men"]`

- **`conduction`**
    - **Origem:** `cv/blocks.py`
    - **Descrição:** Detecção de bloqueios de ramo.
    - **Campos Chave:**
        - `qrs_duration_ms`: (number) Duração do QRS. Ex: `130.0`
        - `is_complete_block`: (boolean) Se a duração do QRS >= 120ms. Ex: `true`
        - `suggested_block_type`: (string) Classificação do bloqueio. Ex: `"Bloqueio de Ramo Direito"`

- **`flags`**
    - **Origem:** Múltiplos módulos, agregados no pipeline principal.
    - **Descrição:** Resumo de achados importantes.
    - **Tipo:** `array` de `string`
    - **Exemplo:** `["BRADICARDIA_SINUSAL", "QTC_LONGO", "HVE_PROVAVEL"]`

## 5. Fluxos de Trabalho e Comandos Essenciais (CLI)

- **Analisar uma imagem de ECG (pipeline completo):**
  ```bash
  python -m ecgcourse ingest image samples/ecg_images/synthetic_12lead.png --deskew --normalize --auto-grid --auto-leads --rpeaks-robust --intervals-refined --axis-hex --rhythm --hypertrophy --blocks --report
  ```

- **Executar um quiz:**
  ```bash
sh
  python -m ecgcourse quiz run quiz/bank/p2/p2_0001.json
  ```

- **Gerar um quiz a partir de um laudo:**
  ```bash
  python -m ecgcourse quiz from-report <caminho_para_o_laudo.json>
  ```

- **Exportar um laudo para HTML com overlay:**
  ```bash
  python -m ecgcourse report export <caminho_para_o_laudo.json> --format html --overlay
  ```

- **Usar um módulo de CV específico:**
  ```bash
  python -m ecgcourse cv axis-hex samples/ecg_images/synthetic_12lead.png --layout 3x4 --json
  ```

## 6. Convenções de Desenvolvimento

- **Estilo de Código:** **Black** (formatação) e **Ruff** (linting), configurados em `pyproject.toml`.
- **Validação de Dados:** Uso mandatório de **JSON Schemas** (`quiz/schema/`, `reporting/schema/`) para garantir a integridade dos dados.
- **Commits:** Estilo de commit convencional (ex: `feat(cv): add hexaxial axis calculation`).
- **CI/CD:** O workflow `assets-pipeline.yml` processa e valida os assets. O `pages.yml` faz o deploy do `case_player` e outros conteúdos estáticos para o GitHub Pages.
- **Testes:** A robustez é garantida por testes unitários e de integração. A adição de testes é esperada para novas funcionalidades.
