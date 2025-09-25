// ECGiga Course JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    init();
});

function init() {
    setupNavigation();
    setupModules();
    setupModal();
    setupScrollEffects();
    setupQuiz();
    setupECGExamples();
}

// Navigation functionality
function setupNavigation() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');

    // Mobile menu toggle
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });

    // Close mobile menu when clicking on a link
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        });
    });

    // Active navigation highlighting
    window.addEventListener('scroll', () => {
        let current = '';
        const sections = document.querySelectorAll('section[id]');
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.offsetHeight;
            
            if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

// Smooth scroll function
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Module content management
function setupModules() {
    const moduleCards = document.querySelectorAll('.module-card');
    
    moduleCards.forEach(card => {
        const button = card.querySelector('.btn');
        button.addEventListener('click', () => {
            const module = card.getAttribute('data-module');
            openModule(module);
        });
    });
}

// Module content data
const moduleContent = {
    basics: {
        title: 'Fundamentos do ECG',
        content: `
            <h2>Fundamentos do ECG</h2>
            
            <h3>1. Anatomia do Sistema de Condução</h3>
            <p>O coração possui um sistema especializado para gerar e conduzir impulsos elétricos:</p>
            <ul>
                <li><strong>Nódulo Sinusal (SA):</strong> Marcapasso natural, localizado no átrio direito</li>
                <li><strong>Nódulo Atrioventricular (AV):</strong> Retarda a condução entre átrios e ventrículos</li>
                <li><strong>Feixe de His:</strong> Conecta o nódulo AV aos ramos direito e esquerdo</li>
                <li><strong>Fibras de Purkinje:</strong> Distribuem o impulso pelo miocárdio ventricular</li>
            </ul>

            <h3>2. Ondas, Intervalos e Segmentos</h3>
            <div class="ecg-explanation">
                <p><strong>Onda P:</strong> Despolarização atrial (duração normal: 0,08-0,10s)</p>
                <p><strong>Complexo QRS:</strong> Despolarização ventricular (duração normal: 0,06-0,10s)</p>
                <p><strong>Onda T:</strong> Repolarização ventricular</p>
                <p><strong>Intervalo PR:</strong> Tempo de condução AV (normal: 0,12-0,20s)</p>
                <p><strong>Intervalo QT:</strong> Duração total da despolarização e repolarização ventricular</p>
            </div>

            <h3>3. Derivações do ECG</h3>
            <p>O ECG padrão possui 12 derivações que visualizam o coração de diferentes ângulos:</p>
            
            <h4>Derivações dos Membros:</h4>
            <ul>
                <li><strong>Bipolares:</strong> I, II, III</li>
                <li><strong>Unipolares aumentadas:</strong> aVR, aVL, aVF</li>
            </ul>
            
            <h4>Derivações Precordiais:</h4>
            <ul>
                <li><strong>V1-V2:</strong> Parede septal</li>
                <li><strong>V3-V4:</strong> Parede anterior</li>
                <li><strong>V5-V6:</strong> Parede lateral</li>
            </ul>

            <div class="quiz-section">
                <h3>Teste seus conhecimentos:</h3>
                <button class="btn btn-primary" onclick="startBasicsQuiz()">Iniciar Quiz - Fundamentos</button>
            </div>
        `
    },
    rhythms: {
        title: 'Arritmias Cardíacas',
        content: `
            <h2>Arritmias Cardíacas</h2>
            
            <h3>1. Ritmo Sinusal Normal</h3>
            <p>Características do ritmo sinusal normal:</p>
            <ul>
                <li>Frequência: 60-100 bpm</li>
                <li>Onda P presente antes de cada QRS</li>
                <li>Intervalo PR constante (0,12-0,20s)</li>
                <li>QRS estreito (<0,12s)</li>
                <li>Ritmo regular</li>
            </ul>

            <h3>2. Bradicardias</h3>
            <p>Frequência cardíaca < 60 bpm:</p>
            <ul>
                <li><strong>Bradicardia sinusal:</strong> Ritmo sinusal com FC < 60 bpm</li>
                <li><strong>Bloqueio AV:</strong> Alteração na condução atrioventricular</li>
                <li><strong>Ritmo juncional:</strong> Marcapasso no nódulo AV</li>
                <li><strong>Ritmo idioventricular:</strong> Marcapasso ventricular</li>
            </ul>

            <h3>3. Taquicardias</h3>
            <p>Frequência cardíaca > 100 bpm:</p>
            
            <h4>Taquicardias Supraventriculares:</h4>
            <ul>
                <li><strong>Taquicardia sinusal:</strong> Ritmo sinusal com FC > 100 bpm</li>
                <li><strong>TSV paroxística:</strong> FC 150-250 bpm, QRS estreito</li>
                <li><strong>Flutter atrial:</strong> Ondas F em "dente de serra"</li>
                <li><strong>Fibrilação atrial:</strong> Ondas f irregulares, ritmo irregular</li>
            </ul>
            
            <h4>Taquicardias Ventriculares:</h4>
            <ul>
                <li><strong>TV sustentada:</strong> > 30 segundos ou compromisso hemodinâmico</li>
                <li><strong>TV não-sustentada:</strong> < 30 segundos</li>
                <li><strong>Fibrilação ventricular:</strong> Emergência médica</li>
            </ul>

            <div class="ecg-examples">
                <h3>Exemplos de ECG:</h3>
                <div class="example-grid">
                    <div class="ecg-example">
                        <h4>Fibrilação Atrial</h4>
                        <div class="ecg-trace" data-rhythm="afib"></div>
                        <p>Observe a ausência de ondas P e o ritmo irregular.</p>
                    </div>
                </div>
            </div>

            <div class="quiz-section">
                <button class="btn btn-primary" onclick="startRhythmsQuiz()">Quiz - Arritmias</button>
            </div>
        `
    },
    ischemia: {
        title: 'Isquemia e IAM',
        content: `
            <h2>Isquemia e Infarto Agudo do Miocárdio</h2>
            
            <h3>1. Fisiopatologia da Isquemia</h3>
            <p>A isquemia miocárdica resulta do desequilíbrio entre oferta e demanda de oxigênio:</p>
            <ul>
                <li>Redução do fluxo sanguíneo coronariano</li>
                <li>Aumento da demanda metabólica</li>
                <li>Alterações na microcirculação</li>
            </ul>

            <h3>2. Alterações Eletrocardiográficas da Isquemia</h3>
            
            <h4>Isquemia Subendocárdica:</h4>
            <ul>
                <li><strong>Infradesnivelamento de ST:</strong> ≥ 1mm em duas derivações contíguas</li>
                <li><strong>Inversão de onda T:</strong> Sinal de isquemia subepicárdica</li>
                <li>Pode estar presente em repouso ou após esforço</li>
            </ul>
            
            <h4>Lesão Subepicárdica (IAMCSST):</h4>
            <ul>
                <li><strong>Supradesnivelamento de ST:</strong> ≥ 1mm em derivações dos membros, ≥ 2mm em precordiais</li>
                <li>Presente em duas ou mais derivações contíguas</li>
                <li>Indica oclusão coronariana aguda</li>
            </ul>

            <h3>3. Localização do IAM pelas Derivações</h3>
            <div class="iam-locations">
                <div class="location-item">
                    <h4>Parede Inferior</h4>
                    <p><strong>Derivações:</strong> II, III, aVF</p>
                    <p><strong>Artéria:</strong> Coronária direita ou circunflexa</p>
                </div>
                
                <div class="location-item">
                    <h4>Parede Anterior</h4>
                    <p><strong>Derivações:</strong> V1-V6</p>
                    <p><strong>Artéria:</strong> Descendente anterior esquerda</p>
                </div>
                
                <div class="location-item">
                    <h4>Parede Lateral</h4>
                    <p><strong>Derivações:</strong> I, aVL, V5-V6</p>
                    <p><strong>Artéria:</strong> Circunflexa ou marginal</p>
                </div>
                
                <div class="location-item">
                    <h4>Parede Posterior</h4>
                    <p><strong>Derivações:</strong> Imagem especular em V1-V3</p>
                    <p><strong>Artéria:</strong> Coronária direita ou circunflexa</p>
                </div>
            </div>

            <h3>4. Cronologia do IAM</h3>
            <p>Evolução temporal das alterações no ECG:</p>
            <ol>
                <li><strong>Hiperaguda (minutos):</strong> Ondas T apiculadas</li>
                <li><strong>Aguda (horas):</strong> Supradesnivelamento de ST</li>
                <li><strong>Subaguda (dias):</strong> Onda Q patológica, inversão de T</li>
                <li><strong>Crônica (semanas-meses):</strong> Onda Q residual, normalização de ST e T</li>
            </ol>

            <div class="clinical-cases">
                <h3>Casos Clínicos:</h3>
                <button class="btn btn-secondary" onclick="loadCase('iam_inferior')">Caso 1: IAM Inferior</button>
                <button class="btn btn-secondary" onclick="loadCase('iam_anterior')">Caso 2: IAM Anterior</button>
            </div>
        `
    },
    hypertrophy: {
        title: 'Hipertrofias',
        content: `
            <h2>Hipertrofias Atriais e Ventriculares</h2>
            
            <h3>1. Hipertrofia Atrial Direita (HAD)</h3>
            <p>Critérios diagnósticos:</p>
            <ul>
                <li>Onda P ≥ 2,5mm de amplitude em II, III, aVF</li>
                <li>Onda P positiva em V1 ≥ 1,5mm</li>
                <li>Duração da onda P normal (<0,12s)</li>
                <li>Padrão "P pulmonale"</li>
            </ul>

            <h3>2. Hipertrofia Atrial Esquerda (HAE)</h3>
            <p>Critérios diagnósticos:</p>
            <ul>
                <li>Duração da onda P ≥ 0,12s</li>
                <li>Entalhe da onda P em I, II ("P mitrale")</li>
                <li>Componente negativo em V1 ≥ 1mm de profundidade</li>
                <li>Índice de Morris ≥ 0,04</li>
            </ul>

            <h3>3. Hipertrofia Ventricular Direita (HVD)</h3>
            <p>Critérios principais:</p>
            <ul>
                <li>R em V1 ≥ 7mm ou R/S em V1 ≥ 1</li>
                <li>S em V5 ou V6 ≥ 7mm</li>
                <li>Eixo à direita (≥ +90°)</li>
                <li>Padrão qR em V1</li>
            </ul>

            <h3>4. Hipertrofia Ventricular Esquerda (HVE)</h3>
            
            <h4>Critérios de Voltagem:</h4>
            <ul>
                <li><strong>Sokolow-Lyon:</strong> SV1 + (RV5 ou RV6) ≥ 35mm</li>
                <li><strong>Cornell:</strong> RaVL + SV3 ≥ 28mm (homens) ou ≥ 20mm (mulheres)</li>
                <li><strong>Romhilt-Estes:</strong> Sistema de pontuação</li>
            </ul>
            
            <h4>Alterações Secundárias:</h4>
            <ul>
                <li>Infradesnivelamento de ST em I, aVL, V5-V6</li>
                <li>Inversão de onda T em derivações laterais</li>
                <li>Aumento da duração do QRS</li>
            </ul>

            <div class="criteria-calculator">
                <h3>Calculadora de Critérios:</h3>
                <div class="calculator-section">
                    <h4>Sokolow-Lyon para HVE:</h4>
                    <label>SV1 (mm): <input type="number" id="sv1" min="0" max="50"></label>
                    <label>RV5 (mm): <input type="number" id="rv5" min="0" max="50"></label>
                    <button onclick="calculateSokolow()">Calcular</button>
                    <div id="sokolow-result"></div>
                </div>
            </div>

            <div class="quiz-section">
                <button class="btn btn-primary" onclick="startHypertrophyQuiz()">Quiz - Hipertrofias</button>
            </div>
        `
    },
    blocks: {
        title: 'Bloqueios',
        content: `
            <h2>Bloqueios de Condução</h2>
            
            <h3>1. Bloqueios Atrioventriculares</h3>
            
            <h4>Bloqueio AV de 1º Grau:</h4>
            <ul>
                <li>Intervalo PR > 0,20s</li>
                <li>Todas as ondas P são conduzidas</li>
                <li>Geralmente assintomático</li>
            </ul>
            
            <h4>Bloqueio AV de 2º Grau:</h4>
            <ul>
                <li><strong>Tipo I (Wenckebach):</strong> Prolongamento progressivo do PR até bloqueio</li>
                <li><strong>Tipo II (Mobitz II):</strong> PR fixo com bloqueios súbitos</li>
                <li><strong>2:1, 3:1:</strong> Condução com razão fixa</li>
            </ul>
            
            <h4>Bloqueio AV Total (3º Grau):</h4>
            <ul>
                <li>Dissociação AV completa</li>
                <li>Ritmo de escape juncional ou ventricular</li>
                <li>Indicação de marcapasso definitivo</li>
            </ul>

            <h3>2. Bloqueios de Ramo</h3>
            
            <h4>Bloqueio de Ramo Direito (BRD):</h4>
            <ul>
                <li>QRS ≥ 0,12s</li>
                <li>Padrão rSR' em V1-V2</li>
                <li>Onda S larga em I, V6</li>
                <li>Padrão "M" em V1, "W" em V6</li>
            </ul>
            
            <h4>Bloqueio de Ramo Esquerdo (BRE):</h4>
            <ul>
                <li>QRS ≥ 0,12s</li>
                <li>QS ou rS em V1</li>
                <li>R monofásica em I, aVL, V6</li>
                <li>Ausência de onda Q em V6</li>
            </ul>

            <h3>3. Hemibloqueios</h3>
            
            <h4>Bloqueio Fascicular Anterior Esquerdo:</h4>
            <ul>
                <li>Desvio do eixo à esquerda (< -30°)</li>
                <li>qR em I, aVL</li>
                <li>rS em II, III, aVF</li>
                <li>QRS < 0,12s (isoladamente)</li>
            </ul>
            
            <h4>Bloqueio Fascicular Posterior Esquerdo:</h4>
            <ul>
                <li>Desvio do eixo à direita (> +90°)</li>
                <li>rS em I, aVL</li>
                <li>qR em II, III, aVF</li>
                <li>Menos comum que o anterior</li>
            </ul>

            <h3>4. Bloqueios Bifasciculares e Trifasciculares</h3>
            <ul>
                <li><strong>Bifascicular:</strong> BRD + BFAE ou BRD + BFPE</li>
                <li><strong>Trifascicular:</strong> Bifascicular + prolongamento de PR</li>
                <li>Risco de progressão para bloqueio AV total</li>
            </ul>

            <div class="differential-diagnosis">
                <h3>Diagnóstico Diferencial de QRS Alargado:</h3>
                <ul>
                    <li>Bloqueios de ramo</li>
                    <li>Pré-excitação ventricular (WPW)</li>
                    <li>Taquicardia ventricular</li>
                    <li>Marcapasso ventricular</li>
                    <li>Hipercalemia severa</li>
                </ul>
            </div>
        `
    },
    advanced: {
        title: 'Tópicos Avançados',
        content: `
            <h2>Tópicos Avançados em ECG</h2>
            
            <h3>1. Síndrome de Brugada</h3>
            <p>Canalopatia com risco de morte súbita:</p>
            <ul>
                <li><strong>Tipo 1:</strong> Supradesnivelamento de ST ≥ 2mm em V1-V3 com padrão "coved"</li>
                <li><strong>Tipo 2:</strong> Padrão "saddleback" com ST ≥ 2mm</li>
                <li><strong>Tipo 3:</strong> Padrão "saddleback" com ST < 2mm</li>
                <li>Teste com procainamida ou flecainida pode desmascarar</li>
            </ul>

            <h3>2. Síndrome do QT Longo</h3>
            <p>Prolongamento do intervalo QT com risco de Torsades de Pointes:</p>
            <ul>
                <li><strong>QTc:</strong> QT corrigido pela frequência (Bazett ou Fridericia)</li>
                <li><strong>Normal:</strong> < 450ms (homens), < 470ms (mulheres)</li>
                <li><strong>Limítrofe:</strong> 450-470ms (homens), 470-480ms (mulheres)</li>
                <li><strong>Prolongado:</strong> > 470ms (homens), > 480ms (mulheres)</li>
            </ul>

            <h3>3. Síndrome do QT Curto</h3>
            <p>Encurtamento patológico do QT:</p>
            <ul>
                <li>QTc < 350ms</li>
                <li>Ondas T altas e simétricas</li>
                <li>Risco de fibrilação atrial e ventricular</li>
            </ul>

            <h3>4. Pré-excitação Ventricular</h3>
            
            <h4>Síndrome de Wolff-Parkinson-White (WPW):</h4>
            <ul>
                <li>Intervalo PR curto (< 0,12s)</li>
                <li>Onda delta (upstroke lento do QRS)</li>
                <li>QRS alargado (> 0,12s)</li>
                <li>Risco de taquicardias supraventriculares</li>
            </ul>
            
            <h4>Localização da Via Acessória:</h4>
            <ul>
                <li><strong>Posterosseptal:</strong> Onda delta positiva em II, III, aVF</li>
                <li><strong>Lateral esquerda:</strong> Onda delta positiva em I, aVL</li>
                <li><strong>Anterosseptal:</strong> Onda delta negativa em V1-V2</li>
            </ul>

            <h3>5. Ritmos de Marcapasso</h3>
            
            <h4>Tipos de Estimulação:</h4>
            <ul>
                <li><strong>AAI:</strong> Estimulação atrial</li>
                <li><strong>VVI:</strong> Estimulação ventricular</li>
                <li><strong>DDD:</strong> Estimulação dual (átrio e ventrículo)</li>
                <li><strong>CRT:</strong> Terapia de ressincronização cardíaca</li>
            </ul>
            
            <h4>Avaliação do Marcapasso:</h4>
            <ul>
                <li>Presença de espículas de estimulação</li>
                <li>Captura adequada</li>
                <li>Sensibilização apropriada</li>
                <li>Frequência programada</li>
            </ul>

            <h3>6. Alterações por Distúrbios Eletrolíticos</h3>
            
            <h4>Hipercalemia:</h4>
            <ul>
                <li>Ondas T altas e apiculadas</li>
                <li>Prolongamento de PR e QRS</li>
                <li>Achatamento da onda P</li>
                <li>Padrão sinusoidal (hipercalemia severa)</li>
            </ul>
            
            <h4>Hipocalemia:</h4>
            <ul>
                <li>Achatamento da onda T</li>
                <li>Presença de onda U</li>
                <li>Prolongamento do QT</li>
                <li>Infradesnivelamento de ST</li>
            </ul>

            <div class="advanced-calculator">
                <h3>Calculadora de QTc:</h3>
                <label>QT medido (ms): <input type="number" id="qt-measured"></label>
                <label>RR (ms): <input type="number" id="rr-interval"></label>
                <label>Sexo: 
                    <select id="gender">
                        <option value="male">Masculino</option>
                        <option value="female">Feminino</option>
                    </select>
                </label>
                <button onclick="calculateQTc()">Calcular QTc</button>
                <div id="qtc-result"></div>
            </div>
        `
    }
};

// Modal functionality
function setupModal() {
    const modal = document.getElementById('moduleModal');
    const span = document.getElementsByClassName('close')[0];

    span.onclick = function() {
        modal.style.display = 'none';
    };

    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
}

function openModule(moduleName) {
    const modal = document.getElementById('moduleModal');
    const content = document.getElementById('moduleContent');
    
    if (moduleContent[moduleName]) {
        content.innerHTML = moduleContent[moduleName].content;
        modal.style.display = 'block';
    }
}

// Scroll effects
function setupScrollEffects() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all cards and sections
    document.querySelectorAll('.module-card, .practice-card, .resource-item').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Quiz functionality
function setupQuiz() {
    window.quizData = {
        basics: [
            {
                question: "Qual é a duração normal do intervalo PR?",
                options: ["0,06-0,10s", "0,12-0,20s", "0,20-0,30s", "0,30-0,40s"],
                correct: 1,
                explanation: "O intervalo PR normal varia de 0,12 a 0,20 segundos, representando o tempo de condução atrioventricular."
            },
            {
                question: "Qual derivação melhor visualiza a parede inferior do coração?",
                options: ["V1-V2", "I, aVL", "II, III, aVF", "V5-V6"],
                correct: 2,
                explanation: "As derivações II, III e aVF visualizam a parede inferior do ventrículo esquerdo."
            }
        ],
        rhythms: [
            {
                question: "Na fibrilação atrial, qual característica é típica?",
                options: ["Ondas P regulares", "QRS alargado", "Ritmo irregular", "Bradicardia"],
                correct: 2,
                explanation: "A fibrilação atrial caracteriza-se pela ausência de ondas P e ritmo irregular."
            }
        ],
        hypertrophy: [
            {
                question: "Pelo critério de Sokolow-Lyon, HVE é diagnosticada quando:",
                options: ["SV1 + RV5/V6 ≥ 25mm", "SV1 + RV5/V6 ≥ 35mm", "RV5 ≥ 25mm", "SV1 ≥ 25mm"],
                correct: 1,
                explanation: "O critério de Sokolow-Lyon para HVE é SV1 + RV5 ou RV6 ≥ 35mm."
            }
        ]
    };
}

// Quiz functions
function startBasicsQuiz() {
    startQuiz('basics');
}

function startRhythmsQuiz() {
    startQuiz('rhythms');
}

function startHypertrophyQuiz() {
    startQuiz('hypertrophy');
}

function startQuiz(category) {
    const questions = window.quizData[category];
    let currentQuestion = 0;
    let score = 0;
    
    function showQuestion() {
        const q = questions[currentQuestion];
        const quizHTML = `
            <div class="quiz-container">
                <h3>Quiz - Questão ${currentQuestion + 1} de ${questions.length}</h3>
                <div class="question">
                    <p><strong>${q.question}</strong></p>
                    <div class="options">
                        ${q.options.map((option, index) => `
                            <label>
                                <input type="radio" name="answer" value="${index}">
                                ${option}
                            </label>
                        `).join('')}
                    </div>
                    <button class="btn btn-primary" onclick="checkAnswer(${q.correct})">Responder</button>
                </div>
                <div class="score">Pontuação: ${score}/${questions.length}</div>
            </div>
        `;
        
        document.getElementById('moduleContent').innerHTML = quizHTML;
    }
    
    window.checkAnswer = function(correct) {
        const selected = document.querySelector('input[name="answer"]:checked');
        if (!selected) {
            alert('Selecione uma resposta!');
            return;
        }
        
        const isCorrect = parseInt(selected.value) === correct;
        if (isCorrect) score++;
        
        const q = questions[currentQuestion];
        const resultHTML = `
            <div class="quiz-result">
                <p class="${isCorrect ? 'correct' : 'incorrect'}">
                    ${isCorrect ? '✓ Correto!' : '✗ Incorreto'}
                </p>
                <p><strong>Explicação:</strong> ${q.explanation}</p>
                <button class="btn btn-primary" onclick="nextQuestion()">
                    ${currentQuestion + 1 < questions.length ? 'Próxima Questão' : 'Ver Resultado'}
                </button>
            </div>
        `;
        
        document.querySelector('.question').innerHTML = resultHTML;
    };
    
    window.nextQuestion = function() {
        currentQuestion++;
        if (currentQuestion < questions.length) {
            showQuestion();
        } else {
            const percentage = Math.round((score / questions.length) * 100);
            document.getElementById('moduleContent').innerHTML = `
                <div class="quiz-final">
                    <h2>Quiz Finalizado!</h2>
                    <p>Você acertou ${score} de ${questions.length} questões (${percentage}%)</p>
                    <div class="performance-msg">
                        ${percentage >= 80 ? 'Excelente! Você domina o conteúdo.' : 
                          percentage >= 60 ? 'Bom trabalho! Revise alguns conceitos.' : 
                          'Continue estudando. A prática leva à perfeição!'}
                    </div>
                    <button class="btn btn-primary" onclick="startQuiz('${category}')">Refazer Quiz</button>
                </div>
            `;
        }
    };
    
    showQuestion();
}

// Calculator functions
function calculateSokolow() {
    const sv1 = parseFloat(document.getElementById('sv1').value) || 0;
    const rv5 = parseFloat(document.getElementById('rv5').value) || 0;
    const total = sv1 + rv5;
    
    const result = document.getElementById('sokolow-result');
    result.innerHTML = `
        <p><strong>Resultado:</strong> ${total}mm</p>
        <p class="${total >= 35 ? 'positive' : 'negative'}">
            ${total >= 35 ? '✓ Critério positivo para HVE' : '✗ Critério negativo para HVE'}
        </p>
    `;
}

function calculateQTc() {
    const qt = parseFloat(document.getElementById('qt-measured').value);
    const rr = parseFloat(document.getElementById('rr-interval').value);
    const gender = document.getElementById('gender').value;
    
    if (!qt || !rr) {
        alert('Preencha todos os campos!');
        return;
    }
    
    // Bazett formula
    const qtc = qt / Math.sqrt(rr / 1000);
    
    let interpretation = '';
    const maleLimit = gender === 'male' ? 450 : 470;
    const femaleLimit = gender === 'male' ? 470 : 480;
    
    if (qtc < 350) {
        interpretation = 'QT curto';
    } else if (qtc < maleLimit) {
        interpretation = 'Normal';
    } else if (qtc < femaleLimit) {
        interpretation = 'Limítrofe';
    } else {
        interpretation = 'Prolongado';
    }
    
    document.getElementById('qtc-result').innerHTML = `
        <p><strong>QTc (Bazett):</strong> ${Math.round(qtc)}ms</p>
        <p><strong>Interpretação:</strong> ${interpretation}</p>
    `;
}

// ECG examples setup
function setupECGExamples() {
    // Placeholder for interactive ECG examples
    const ecgTraces = document.querySelectorAll('.ecg-trace');
    ecgTraces.forEach(trace => {
        const rhythm = trace.getAttribute('data-rhythm');
        trace.innerHTML = `<div class="loading-ecg"></div><p>Carregando exemplo de ${rhythm}...</p>`;
        
        // Simulate loading ECG example
        setTimeout(() => {
            trace.innerHTML = generateECGTrace(rhythm);
        }, 1000);
    });
}

function generateECGTrace(rhythm) {
    // This would generate different ECG patterns based on rhythm type
    // For now, returning a placeholder
    return `
        <div class="ecg-strip">
            <svg viewBox="0 0 800 150" class="ecg-example-svg">
                <path d="M0,75 L100,75 L110,45 L120,105 L130,15 L140,75 L300,75" 
                      stroke="#ff6b6b" stroke-width="2" fill="none"/>
            </svg>
            <p class="ecg-description">Exemplo de traçado de ${rhythm}</p>
        </div>
    `;
}

// Clinical cases
function loadCase(caseId) {
    const cases = {
        iam_inferior: {
            title: 'Caso Clínico: IAM Inferior',
            content: `
                <h3>Paciente de 65 anos com dor precordial há 2 horas</h3>
                <p><strong>História:</strong> Homem, 65 anos, diabético, hipertenso, dor precordial tipo aperto, irradiando para mandíbula.</p>
                <p><strong>ECG:</strong> Supradesnivelamento de ST em II, III, aVF. Infradesnivelamento recíproco em I, aVL.</p>
                <p><strong>Diagnóstico:</strong> IAM inferior com ST elevado</p>
                <p><strong>Conduta:</strong> Terapia de reperfusão urgente (trombolítico ou cateterismo)</p>
            `
        },
        iam_anterior: {
            title: 'Caso Clínico: IAM Anterior',
            content: `
                <h3>Mulher de 58 anos com dor torácica intensa</h3>
                <p><strong>História:</strong> Mulher, 58 anos, fumante, dor precordial súbita e intensa.</p>
                <p><strong>ECG:</strong> Supradesnivelamento de ST em V1-V6, ondas Q em V2-V4.</p>
                <p><strong>Diagnóstico:</strong> IAM anterior extenso com ST elevado</p>
                <p><strong>Conduta:</strong> Cateterismo emergencial, provável oclusão de DA proximal</p>
            `
        }
    };
    
    if (cases[caseId]) {
        document.getElementById('moduleContent').innerHTML = `
            <div class="clinical-case">
                ${cases[caseId].content}
                <button class="btn btn-secondary" onclick="history.back()">Voltar</button>
            </div>
        `;
    }
}

// Practice section functionality
document.addEventListener('DOMContentLoaded', function() {
    const practiceButtons = document.querySelectorAll('.practice-card .btn');
    
    practiceButtons.forEach(button => {
        button.addEventListener('click', function() {
            const cardTitle = this.parentElement.querySelector('h3').textContent;
            
            if (cardTitle.includes('Casos Clínicos')) {
                openClinicalCases();
            } else if (cardTitle.includes('Quiz')) {
                openInteractiveQuiz();
            } else if (cardTitle.includes('Biblioteca')) {
                openECGLibrary();
            }
        });
    });
});

function openClinicalCases() {
    const modal = document.getElementById('moduleModal');
    const content = document.getElementById('moduleContent');
    
    content.innerHTML = `
        <h2>Casos Clínicos</h2>
        <div class="cases-grid">
            <div class="case-item" onclick="loadCase('iam_inferior')">
                <h3>Caso 1: Dor Precordial</h3>
                <p>Homem, 65 anos, com dor precordial há 2 horas</p>
            </div>
            <div class="case-item" onclick="loadCase('iam_anterior')">
                <h3>Caso 2: Dor Torácica Intensa</h3>
                <p>Mulher, 58 anos, fumante, dor súbita</p>
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
}

function openInteractiveQuiz() {
    const modal = document.getElementById('moduleModal');
    const content = document.getElementById('moduleContent');
    
    content.innerHTML = `
        <h2>Quiz Interativo</h2>
        <div class="quiz-categories">
            <button class="btn btn-primary" onclick="startQuiz('basics')">Fundamentos</button>
            <button class="btn btn-primary" onclick="startQuiz('rhythms')">Arritmias</button>
            <button class="btn btn-primary" onclick="startQuiz('hypertrophy')">Hipertrofias</button>
        </div>
    `;
    
    modal.style.display = 'block';
}

function openECGLibrary() {
    const modal = document.getElementById('moduleModal');
    const content = document.getElementById('moduleContent');
    
    content.innerHTML = `
        <h2>Biblioteca de ECGs</h2>
        <div class="ecg-library-grid">
            <div class="ecg-library-item">
                <h3>Ritmo Sinusal Normal</h3>
                <div class="ecg-trace" data-rhythm="normal"></div>
            </div>
            <div class="ecg-library-item">
                <h3>Fibrilação Atrial</h3>
                <div class="ecg-trace" data-rhythm="afib"></div>
            </div>
            <div class="ecg-library-item">
                <h3>Bloqueio de Ramo Direito</h3>
                <div class="ecg-trace" data-rhythm="rbbb"></div>
            </div>
        </div>
    `;
    
    // Initialize ECG examples
    setupECGExamples();
    modal.style.display = 'block';
}

// CSS classes for quiz results
const style = document.createElement('style');
style.textContent = `
    .quiz-container { padding: 20px; }
    .quiz-result .correct { color: #27ae60; font-weight: bold; }
    .quiz-result .incorrect { color: #e74c3c; font-weight: bold; }
    .quiz-final { text-align: center; padding: 20px; }
    .performance-msg { 
        margin: 20px 0; 
        padding: 15px; 
        background: #f8f9fa; 
        border-radius: 8px; 
        font-weight: 500;
    }
    .options { margin: 20px 0; }
    .options label { 
        display: block; 
        margin: 10px 0; 
        padding: 10px; 
        background: #f8f9fa; 
        border-radius: 5px; 
        cursor: pointer;
    }
    .options label:hover { background: #e9ecef; }
    .cases-grid, .ecg-library-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
        gap: 20px; 
        margin: 20px 0; 
    }
    .case-item, .ecg-library-item { 
        padding: 20px; 
        background: #f8f9fa; 
        border-radius: 8px; 
        cursor: pointer;
        transition: background 0.3s;
    }
    .case-item:hover { background: #e9ecef; }
    .calculator-section { 
        background: #f8f9fa; 
        padding: 20px; 
        border-radius: 8px; 
        margin: 20px 0; 
    }
    .calculator-section label { 
        display: block; 
        margin: 10px 0; 
    }
    .calculator-section input, .calculator-section select { 
        margin-left: 10px; 
        padding: 5px; 
        border: 1px solid #ddd; 
        border-radius: 4px; 
    }
    #sokolow-result, #qtc-result { 
        margin: 15px 0; 
        padding: 10px; 
        background: white; 
        border-radius: 5px; 
    }
    .positive { color: #27ae60; font-weight: bold; }
    .negative { color: #e74c3c; }
`;
document.head.appendChild(style);