# ECGiga — Guia do Usuário

## Sumário

1. [Instalação](#instalação)
2. [Uso via CLI](#uso-via-cli)
3. [Aplicação Web (Dashboard)](#aplicação-web-dashboard)
4. [Sistema de Quiz](#sistema-de-quiz)
5. [Analogia da Câmera](#analogia-da-câmera)
6. [Datasets](#datasets)
7. [Geração de Laudos](#geração-de-laudos)
8. [Simulação de ECG](#simulação-de-ecg)
9. [Efeitos de Drogas](#efeitos-de-drogas)
10. [Dúvidas Frequentes](#dúvidas-frequentes)

---

## Instalação

### Requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Git (para clonar o repositório)

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/ecgiga/ecgiga.git
cd ecgiga

# 2. Crie um ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou: .venv\Scripts\activate  # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Instale o projeto em modo de desenvolvimento
pip install -e .

# 5. Verifique a instalação
ecgcourse --help
```

### Instalação via Docker

```bash
# Construir e iniciar todos os serviços
docker-compose up --build

# O dashboard estará disponível em: http://localhost:8050
# A API estará disponível em: http://localhost:8000
```

---

## Uso via CLI

O ECGiga oferece uma interface de linha de comando completa.

### Comandos principais

```bash
# Ajuda geral
ecgcourse --help

# Analisar uma imagem de ECG
ecgcourse analyze caminho/para/ecg.png

# Analisar com saída detalhada
ecgcourse analyze ecg.png --verbose --output resultado.json

# Iniciar o quiz interativo
ecgcourse quiz

# Quiz de um tópico específico
ecgcourse quiz --topic arritmias
ecgcourse quiz --topic intervalos
ecgcourse quiz --topic eixo

# Gerar um ECG sintético
ecgcourse generate --hr 80 --pathology stemi_anterior --output ecg_stemi.json

# Verificar interações de drogas
ecgcourse drugs --check amiodarona fluoroquinolona

# Iniciar o servidor web
ecgcourse serve
```

### Exemplos práticos

**Analisar um ECG e gerar laudo:**

```bash
ecgcourse analyze meu_ecg.png --report --format pdf
```

**Quiz com pontuação salva:**

```bash
ecgcourse quiz --user dr_silva --save-results
```

**Simular efeito de hipercalemia:**

```bash
ecgcourse simulate --condition hyperkalemia --level severe
```

---

## Aplicação Web (Dashboard)

### Iniciando

```bash
# Opção 1: Via CLI
ecgcourse serve

# Opção 2: Diretamente
python web_app/dash_app/app.py

# Opção 3: Via Docker
docker-compose up web
```

Acesse: **http://localhost:8050**

### Funcionalidades do Dashboard

1. **Upload de ECG:** Arraste e solte imagens de ECG para análise automática
2. **Visualização interativa:** Zoom, pan e medição de intervalos diretamente no traçado
3. **Simulador de ECG:** Gere ECGs sintéticos ajustando parâmetros em tempo real
4. **Efeitos de drogas:** Selecione medicamentos e veja o impacto no ECG
5. **Distúrbios iônicos:** Simule hiper/hipocalemia, hiper/hipocalcemia
6. **Quiz interativo:** Pratique interpretação com feedback imediato
7. **Histórico:** Veja seus resultados anteriores e evolução

### Navegação

- **Aba Análise:** Upload e interpretação de ECGs reais
- **Aba Simulação:** Geração de ECGs sintéticos e simulação de condições
- **Aba Quiz:** Prática com questões de múltipla escolha
- **Aba Relatórios:** Geração e exportação de laudos

---

## Sistema de Quiz

O sistema de quiz contém centenas de questões organizadas por tópico e dificuldade.

### Tópicos disponíveis

- **Ritmo e frequência:** Identificação de ritmos sinusais, taquicardias, bradicardias
- **Arritmias:** FA, flutter, TSV, TV, FV, bloqueios AV
- **Intervalos:** PR, QRS, QT/QTc — valores normais e anormais
- **Eixo elétrico:** Cálculo e interpretação do eixo cardíaco
- **Isquemia/Infarto:** Padrões de STEMI, NSTEMI, angina
- **Hipertrofia:** SVE, SVD, SAE, SAD
- **Bloqueios de ramo:** BRE, BRD, hemibloqueios
- **Distúrbios eletrolíticos:** Hiper/hipocalemia, hiper/hipocalcemia
- **Efeitos de drogas:** Padrões farmacológicos no ECG
- **Emergências:** Red flags que exigem ação imediata

### Como funciona

1. Selecione um tópico ou modo aleatório
2. Leia a questão e analise o ECG apresentado (quando aplicável)
3. Escolha sua resposta
4. Receba feedback com:
   - Explicação clínica detalhada
   - Analogia da câmera para facilitar a memorização
   - Referências bibliográficas
5. Acompanhe sua pontuação e evolução ao longo do tempo

### Modos de estudo

- **Prática livre:** Sem limite de tempo, com dicas disponíveis
- **Simulado:** Tempo limitado, sem dicas (simula prova)
- **Revisão:** Veja apenas questões que errou anteriormente

---

## Analogia da Câmera

O ECGiga utiliza uma analogia inovadora para ensinar ECG: **o coração como uma câmera fotográfica**.

### Conceito central

| Elemento da câmera | Equivalente cardíaco |
|---------------------|----------------------|
| **Obturador** | Canais iônicos (velocidade de repol./despol.) |
| **Exposição** | Duração do potencial de ação (QT) |
| **Frame rate** | Frequência cardíaca |
| **Foco/Resolução** | Condução ventricular (QRS) |
| **Filtros** | Medicamentos que alteram canais iônicos |
| **Flash** | Estimulação simpática |
| **Pause/Freeze** | Bloqueio AV |
| **Contraste** | Alterações do segmento ST |
| **Lente** | Derivações (diferentes ângulos de visão) |

### Exemplos práticos

**Hipercalemia severa:**
> "A câmera está com obturador tão rápido que distorce a imagem — T apiculadas (repolarização rápida) e QRS largo (despolarização lenta)."

**Betabloqueador:**
> "Frame rate reduzido — a câmera dispara menos vezes por segundo (bradicardia)."

**Digoxina:**
> "Ajuste manual de contraste — ST em 'bigode de Dalí', exposição curta."

---

## Datasets

O ECGiga inclui acesso a datasets de ECG para estudo e pesquisa.

### Datasets incluídos

- **Banco de questões:** 500+ questões com imagens de ECG anotadas
- **ECGs de exemplo:** Casos clássicos de cada patologia
- **Valores de referência:** Intervalos normais por idade e sexo

### Importando dados externos

```bash
# Importar do PhysioNet
ecgcourse import --source physionet --dataset ptbxl

# Importar arquivo WFDB
ecgcourse import --file registro.hea

# Importar imagem de ECG
ecgcourse import --image ecg_paciente.png
```

---

## Geração de Laudos

### Laudo automático

```bash
# Gerar laudo a partir de imagem
ecgcourse report ecg.png --output laudo.pdf

# Laudo com dados do paciente
ecgcourse report ecg.png --patient "João Silva" --age 65 --sex M
```

### Estrutura do laudo

1. **Dados do paciente** (quando disponíveis)
2. **Dados técnicos** (derivações, calibração, qualidade)
3. **Ritmo e frequência**
4. **Intervalos** (PR, QRS, QT/QTc)
5. **Eixo elétrico**
6. **Morfologia** (ondas P, QRS, T, ST)
7. **Conclusão**
8. **Alertas** (flags de emergência, se aplicável)

### Formatos de exportação

- **PDF:** Laudo formatado para impressão
- **JSON:** Dados estruturados para integração
- **HTML:** Visualização interativa no navegador

---

## Simulação de ECG

O módulo de simulação permite gerar ECGs sintéticos com parâmetros controláveis.

### Parâmetros ajustáveis

| Parâmetro | Padrão | Faixa |
|-----------|--------|-------|
| FC (bpm) | 72 | 30–200 |
| PR (ms) | 160 | 80–300 |
| QRS (ms) | 90 | 60–200 |
| QT (ms) | 380 | 250–600 |
| Eixo (°) | 60 | -180 a +180 |
| Ruído | 0.02 | 0–0.5 |

### Patologias simuláveis

- ECG normal
- STEMI anterior
- STEMI inferior
- Bloqueio de ramo esquerdo (BRE)
- Bloqueio de ramo direito (BRD)
- Fibrilação atrial (FA)
- Wolf-Parkinson-White (WPW)
- Hipercalemia
- QT longo

---

## Efeitos de Drogas

O banco de dados inclui 18+ medicamentos com seus efeitos no ECG.

### Verificação de interações

```bash
# Verificar combinação de medicamentos
ecgcourse drugs --check amiodarona sotalol metadona
```

**Saída:**
```
⚠ ALTO RISCO: Múltiplas drogas que prolongam o QT em uso simultâneo:
  amiodarona, sotalol, metadona.
  Risco elevado de Torsades de Pointes.
  Monitorar ECG e eletrólitos (K⁺, Mg²⁺).
```

---

## Dúvidas Frequentes

**P: Preciso de internet para usar?**
R: Não. O ECGiga funciona completamente offline. Internet é necessária apenas para importar datasets externos.

**P: Os laudos gerados podem ser usados clinicamente?**
R: Os laudos são para fins educacionais. Sempre valide com um profissional qualificado.

**P: Como atualizo o banco de questões?**
R: Execute `git pull` e `pip install -e .` para atualizar.

**P: Posso adicionar minhas próprias questões?**
R: Sim! Consulte o Guia do Desenvolvedor para instruções sobre o formato de questões.

**P: O sistema funciona com ECGs de qualquer equipamento?**
R: O sistema aceita imagens PNG, JPEG e TIFF. A qualidade da análise depende da resolução e nitidez da imagem.
