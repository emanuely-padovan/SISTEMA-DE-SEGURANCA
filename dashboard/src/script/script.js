const CONFIG = {
  broker: "ws://10.132.112.5:9001",
  topicSub: "senai/grupo2/sensores",
  topicPub: "senai/grupo2/comandos",
  clientId: "dashboard_" + Math.random().toString(16).slice(2, 8),
};

let cliente = null;

const logEl = document.getElementById("log");
const tempDisplay = document.getElementById("temp-display");
const gasDisplay = document.getElementById("gases-ppm");
const fillConcentracao = document.getElementById("fill-concentracao");
const fillRisco = document.getElementById("fill-risco");

function log(msg) {
  const hora = new Date().toLocaleTimeString("pt-BR");
  logEl.textContent += `[${hora}] ${msg}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

function processarMensagem(mensagem) {
  log("Recebido: " + mensagem);

  const dados = {};

  mensagem.split(",").forEach((item) => {
    const partes = item.split(":");

    if (partes.length >= 2) {
      const chave = partes[0].trim();
      const valor = partes.slice(1).join(":").trim();

      dados[chave] = valor;
    }
  });

  const badgeTemp = document.querySelector(".badge-safe");
  const alertaTexto = document.querySelector(".alert-card p");
  const alertaBadge = document.querySelector(".badge-critical");
  const statusTitle = document.querySelector(".status-title");
  const alertCard = document.querySelector(".alert-card");

  // ================= TEMPERATURA =================

  if (dados["Temperatura"]) {
    const temp = parseFloat(dados["Temperatura"]);

    tempDisplay.textContent = temp.toFixed(1) + "°C";

    if (temp >= 50) {
      badgeTemp.textContent = "EMERGÊNCIA";
      badgeTemp.style.background = "#ff0000";
    } else if (temp >= 35) {
      badgeTemp.textContent = "ATENÇÃO";
      badgeTemp.style.background = "#ffb300";
    } else {
      badgeTemp.textContent = "SEGURO";
      badgeTemp.style.background = "#00c853";
    }
  }

  // ================= GÁS =================

  if (dados["Gás"]) {
    const gas = parseInt(dados["Gás"]);

    gasDisplay.innerHTML = `${gas} <span class="unit">PPM</span>`;

    let percentual = (gas / 20000) * 100;

    if (percentual > 100) percentual = 100;

    fillConcentracao.style.width = percentual + "%";

    if (gas >= 55000) {
      fillConcentracao.style.background = "#ff0000";

      fillRisco.style.width = "100%";
      fillRisco.style.background = "#ff0000";
    } else if (gas >= 45000) {
      fillConcentracao.style.background = "#ffb300";

      fillRisco.style.width = "60%";
      fillRisco.style.background = "#ffb300";
    } else {
      fillConcentracao.style.background = "#00ff55";

      fillRisco.style.width = "20%";
      fillRisco.style.background = "#00ff55";
    }
  }

  // ================= ESTADO =================

  if (dados["Estado"]) {
    const estado = dados["Estado"];

    statusTitle.textContent = estado;

    // limpa os botões
    document
      .querySelectorAll(".action-btn")
      .forEach((btn) => btn.classList.remove("ativo"));

    switch (estado) {
      case "SEGURO":
        alertaTexto.textContent = "Ambiente operando normalmente.";

        alertaBadge.textContent = "NORMAL";

        alertCard.style.borderLeft = "8px solid #00ff55";

        alertaBadge.style.background = "#00ff55";

        break;

      case "ATENCAO":
        alertaTexto.textContent = "Possível risco detectado.";

        alertaBadge.textContent = "ATENÇÃO";

        alertCard.style.borderLeft = "8px solid #ffb300";

        alertaBadge.style.background = "#ffb300";

        document.getElementById("btn-luz").classList.add("ativo");

        break;

      case "EMERGENCIA":
        alertaTexto.textContent = "Evacuação recomendada!";

        alertaBadge.textContent = "EMERGÊNCIA";

        alertCard.style.borderLeft = "8px solid #ff0000";

        alertaBadge.style.background = "#ff0000";

        document.getElementById("btn-luz").classList.add("ativo");

        document.getElementById("btn-rotas").classList.add("ativo");

        document.getElementById("btn-luz-rotas").classList.add("ativo");

        document.getElementById("btn-energia").classList.add("ativo");

        break;

      case "MANUAL":
        alertaTexto.textContent = "Alarme manual acionado.";

        alertaBadge.textContent = "MANUAL";

        alertCard.style.borderLeft = "8px solid #ff0000";

        alertaBadge.style.background = "#ff0000";

        document.getElementById("btn-luz").classList.add("ativo");

        document.getElementById("btn-rotas").classList.add("ativo");

        document.getElementById("btn-luz-rotas").classList.add("ativo");

        document.getElementById("btn-energia").classList.add("ativo");

        break;
    }
  }
}

// ================= MQTT =================

function conectar() {
  console.log("Tentando conectar:", CONFIG.broker);

  cliente = mqtt.connect(CONFIG.broker, {
    clientId: CONFIG.clientId,
    clean: true,
    connectTimeout: 5000,
  });

  cliente.on("connect", () => {
    console.log("CONECTOU!");

    log("Conectado!");

    cliente.subscribe(CONFIG.topicSub, (erro) => {
      if (erro) {
        console.error("Erro subscribe:", erro);
      } else {
        console.log("Inscrito em:", CONFIG.topicSub);
      }
    });
  });

  cliente.on("message", (topico, payload) => {
    console.log("TOPICO:", topico);
    console.log("MSG:", payload.toString());

    processarMensagem(payload.toString());
  });

  cliente.on("error", (erro) => {
    console.error("MQTT ERRO:", erro);

    log("Erro MQTT");
  });

  cliente.on("close", () => {
    console.log("MQTT FECHADO");

    log("Desconectado");
  });
}

// ================= PUBLICAR =================

function enviarComando(comando) {
  if (!cliente || !cliente.connected) {
    log("Broker desconectado.");
    return;
  }

  cliente.publish(CONFIG.topicPub, comando);

  log("Enviado: " + comando);
}

// ================= BOTÕES =================

document.getElementById("btn-luz").addEventListener("click", () => {
  enviarComando("teste:verde");
});

document.getElementById("btn-rotas").addEventListener("click", () => {
  enviarComando("teste:amarelo");
});

document.getElementById("btn-luz-rotas").addEventListener("click", () => {
  enviarComando("teste:vermelho");
});

document.getElementById("btn-energia").addEventListener("click", () => {
  enviarComando("teste:speaker");
});

document.querySelector(".btn-alarm-local").addEventListener("click", () => {
  enviarComando("alarme:manual");
});

// ================= START =================

conectar();
