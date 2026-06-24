const CONFIG = {
  broker: "ws://10.132.112.5:9001",
  topicSub: "senai/grupo2/sensores", // Tópico onde a Raspberry publica
  topicPub: "senai/grupo2/comandos", // Tópico onde o Dashboard publica comandos
  clientId: "dashboard_" + Math.random().toString(16).slice(2, 8),
};

let cliente = null;

// Elementos do DOM
const logContainer = document.getElementById("log-container");
const logCount = document.getElementById("log-count");
const tempDisplay = document.getElementById("temp-display");
const gasDisplay = document.getElementById("gases-ppm");
const fillConcentracao = document.getElementById("fill-concentracao");
const fillRisco = document.getElementById("fill-risco");

// Estado do botão visual de alarme no Dashboard
let alarmeDashboardAtivo = false;

// Função de Log adaptada para renderizar os Cards Organizáveis
function log(msg, tipo = "info") {
  const agora = new Date();
  const hora = agora.toLocaleTimeString("pt-BR");

  const icones = {
    info: "fa-circle-info",
    success: "fa-circle-check",
    warning: "fa-triangle-exclamation",
    danger: "fa-radiation"
  };

  if (!logContainer) return;

  // Limpa o card estático inicial se houver
  if (logContainer.children.length === 1 && logContainer.querySelector(".log-timestamp")?.innerText === "--:--:--") {
    logContainer.innerHTML = "";
  }

  const novoCard = document.createElement("div");
  novoCard.className = `log-card log-${tipo}`;
  novoCard.innerHTML = `
    <div class="log-icon"><i class="fa-solid ${icones[tipo]}"></i></div>
    <div class="log-body">
      <span class="log-timestamp">${hora}</span>
      <p class="log-message">${msg}</p>
    </div>
  `;

  logContainer.insertBefore(novoCard, logContainer.firstChild);
  if (logCount) {
    logCount.innerText = `${logContainer.children.length} mensagens`;
  }
}

function processarMensagem(mensagem) {
  let tipoLog = "success";
  if (mensagem.includes("Estado:ATENCAO")) tipoLog = "warning";
  if (mensagem.includes("Estado:EMERGENCIA") || mensagem.includes("Estado:MANUAL")) tipoLog = "danger";

  log("Recebido: " + mensagem, tipoLog);

  const dados = {};
  // Processamento limpo removendo espaços indesejados
  mensagem.split(",").forEach((item) => {
    const partes = item.split(":");
    if (partes.length >= 2) {
      const chave = partes[0].trim();
      const valor = partes.slice(1).join(":").trim();
      dados[chave] = valor;
    }
  });

  // Captura dinâmica de elementos tolerante a variações de IDs ou Classes
  const badgeTemp = document.getElementById("temp-badge") || document.querySelector(".badge-safe");
  const alertaTexto = document.getElementById("alert-text") || document.querySelector(".alert-card p");
  const alertaBadge = document.getElementById("alert-badge") || document.querySelector(".badge-critical");
  const statusTitle = document.getElementById("lcd-display") || document.querySelector(".status-title");
  const alertCard = document.getElementById("alert-card-panel") || document.querySelector(".alert-card");
  const btnAlarmLocal = document.getElementById("btn-toggle-alarme") || document.querySelector(".btn-alarm-local");
  const txtAlarmeLocal = document.getElementById("txt-alarme-local");

  // ================= 1. TRATAMENTO DE TEMPERATURA =================
  if (dados["Temperatura"]) {
    const temp = parseFloat(dados["Temperatura"]);
    if (tempDisplay) tempDisplay.textContent = temp.toFixed(1) + "°C";

    if (badgeTemp) {
      badgeTemp.textContent = temp >= 50 ? "EMERGÊNCIA" : temp >= 35 ? "ATENÇÃO" : "SEGURO";
      badgeTemp.style.backgroundColor = temp >= 50 ? "#ff0000" : temp >= 35 ? "#ffb300" : "#00c853";
      badgeTemp.style.color = temp >= 35 && temp < 50 ? "#000000" : "#ffffff";
    }
  }

  // ================= 2. TRATAMENTO DE GÁS =================
  if (dados["Gás"]) {
    const gas = parseInt(dados["Gás"]);
    if (gasDisplay) gasDisplay.innerHTML = `${gas} <span class="unit">ADC</span>`;

    let percentual = Math.min(Math.max((gas / 65535) * 100, 0), 100);

    if (fillConcentracao) {
      fillConcentracao.style.width = percentual.toFixed(0) + "%";
      fillConcentracao.style.backgroundColor = gas >= 55000 ? "#ff0000" : gas >= 45000 ? "#ffb300" : "#00ff55";
    }

    if (fillRisco) {
      fillRisco.style.width = gas >= 55000 ? "100%" : gas >= 45000 ? "60%" : "20%";
      fillRisco.style.backgroundColor = gas >= 55000 ? "#ff0000" : gas >= 45000 ? "#ffb300" : "#00ff55";
    }
  }

  // ================= 3. TRATAMENTO DOS ESTADOS GERAIS =================
  if (dados["Estado"]) {
    const estado = dados["Estado"];
    if (statusTitle) statusTitle.textContent = estado === "MANUAL" ? "ALARME MANUAL" : estado;

    document.querySelectorAll(".action-btn").forEach((btn) => {
      btn.classList.remove("active");
    });

    switch (estado) {
      case "SEGURO":
        if (statusTitle) statusTitle.style.color = "#47ff33";
        if (alertaTexto) alertaTexto.textContent = "Ambiente operando dentro dos limites de segurança.";
        if (alertaBadge) {
          alertaBadge.textContent = "NORMAL";
          alertaBadge.style.backgroundColor = "transparent";
          alertaBadge.style.color = "#47ff33";
          alertaBadge.style.borderColor = "#47ff33";
        }
        if (alertCard) alertCard.className = "card alert-card status-safe";

        // Desativa o alarme visual do dashboard caso a placa relate normalidade
        alarmeDashboardAtivo = false;
        if (btnAlarmLocal) btnAlarmLocal.classList.remove("active-alarm");
        if (txtAlarmeLocal) txtAlarmeLocal.innerText = "ACIONAR ALARME LOCAL";
        break;

      case "ATENCAO":
        if (statusTitle) statusTitle.style.color = "#ffb300";
        if (alertaTexto) alertaTexto.textContent = "Possível risco detectado nas dependências.";
        if (alertaBadge) {
          alertaBadge.textContent = "ATENÇÃO";
          alertaBadge.style.backgroundColor = "transparent";
          alertaBadge.style.color = "#ffb300";
          alertaBadge.style.borderColor = "#ffb300";
        }
        if (alertCard) alertCard.className = "card alert-card status-warning";

        const btnRotas = document.getElementById("btn-rotas");
        if (btnRotas) btnRotas.classList.add("active");
        break;

      case "EMERGENCIA":
      case "MANUAL":
        if (statusTitle) statusTitle.style.color = "#ff3333";
        if (alertaTexto) alertaTexto.textContent = (estado === "MANUAL") ? "Alarme manual acionado. Evacue o prédio!" : "Evacuação imediata recomendada!";
        if (alertaBadge) {
          alertaBadge.textContent = estado;
          alertaBadge.style.backgroundColor = "transparent";
          alertaBadge.style.color = "#ff3333";
          alertaBadge.style.borderColor = "#ff3333";
        }
        if (alertCard) alertCard.className = "card alert-card status-danger";

        // Acende todos os botões de apoio em perigo
        ["btn-luz", "btn-rotas", "btn-luz-rotas", "btn-energia"].forEach(id => {
          document.getElementById(id)?.classList.add("active");
        });

        // Sincroniza o clique do painel com o estado atualizado retornado da Pico
        if (estado === "MANUAL") {
          alarmeDashboardAtivo = true;
          if (btnAlarmLocal) btnAlarmLocal.classList.add("active-alarm");
          if (txtAlarmeLocal) txtAlarmeLocal.innerText = "DESATIVAR ALARME LOCAL";
        }
        break;
    }
  }
}

// ================= CONEXÃO MQTT =================
function conectar() {
  console.log("Tentando conectar ao Broker:", CONFIG.broker);

  cliente = mqtt.connect(CONFIG.broker, {
    clientId: CONFIG.clientId,
    clean: true,
    connectTimeout: 5000,
  });

  cliente.on("connect", () => {
    console.log("Conectado com sucesso!");
    log("Conectado ao Broker MQTT.", "info");

    cliente.subscribe(CONFIG.topicSub, (erro) => {
      if (erro) {
        console.error("Erro ao assinar:", erro);
        log("Erro ao assinar canal de sensores.", "danger");
      } else {
        console.log("Inscrito no canal de telemetria:", CONFIG.topicSub);
      }
    });
  });

  cliente.on("message", (topico, payload) => {
    processarMensagem(payload.toString());
  });

  cliente.on("error", (erro) => {
    console.error("MQTT Erro:", erro);
    log("Erro na conexão MQTT.", "danger");
  });

  cliente.on("close", () => {
    console.log("Conexão MQTT encerrada.");
    log("Desconectado do Broker.", "info");
  });
}

// ================= PUBLICAÇÃO DE COMANDOS =================
function enviarComando(comando) {
  if (!cliente || !cliente.connected) {
    log("Erro: Broker desconectado. Impossível enviar.", "danger");
    return;
  }
  cliente.publish(CONFIG.topicPub, comando);
  log("Comando Enviado: " + comando, comando === "alarme:manual" ? "warning" : "info");
}

// ================= EVENTOS DOS BOTÕES (INTERFACE) =================
document.getElementById("btn-luz")?.addEventListener("click", () => enviarComando("teste:verde"));
document.getElementById("btn-rotas")?.addEventListener("click", () => enviarComando("teste:amarelo"));
document.getElementById("btn-luz-rotas")?.addEventListener("click", () => enviarComando("teste:vermelho"));
document.getElementById("btn-energia")?.addEventListener("click", () => enviarComando("teste:speaker"));

// Lógica de acionamento Manual Corrigida
const btnAlarmLocalElement = document.getElementById("btn-toggle-alarme") || document.querySelector(".btn-alarm-local");
if (btnAlarmLocalElement) {
  btnAlarmLocalElement.addEventListener("click", () => {
    enviarComando("alarme:manual");
    
    alarmeDashboardAtivo = !alarmeDashboardAtivo;
    const txtAlarmeLocal = document.getElementById("txt-alarme-local");
    if (txtAlarmeLocal) {
      if (alarmeDashboardAtivo) {
        btnAlarmLocalElement.classList.add("active-alarm");
        txtAlarmeLocal.innerText = "DESATIVAR ALARME LOCAL";
      } else {
        btnAlarmLocalElement.classList.remove("active-alarm");
        txtAlarmeLocal.innerText = "ACIONAR ALARME LOCAL";
      }
    }
  });
}

const btnDespacho = document.getElementById("btn-despacho");
if (btnDespacho) {
  btnDespacho.addEventListener("click", () => {
    alert("Contatando central de despacho de emergência do SENAI...");
    log("Chamada de emergência enviada para a central de despacho.", "danger");
  });
}

// Inicialização automática do Dashboard
conectar();