// script.js — Dashboard IoT | SENAI Ítalo Bologna — Aula 10
//
// Este arquivo faz duas coisas:
//   1. SUBSCRIBER: recebe dados dos sensores (DHT22 + LDR) do Pico
//   2. PUBLISHER: envia comandos (led:on / led:off) para o Pico
//
// Comunicação via MQTT.js usando WebSocket (ws://)
// O browser não consegue TCP puro — por isso usa WebSocket na porta 8000

// ─── CONFIGURAÇÃO ────────────────────────────────────────────────────────────
// Muda só aqui para trocar de broker (local → professor → online)
const CONFIG = {
    broker:    "ws://192.168.1.XXX:8000",  // ← IP do notebook broker + porta WebSocket
    topicSub:  "senai/grupo2/sensores",     // ← mesmo tópico que o Pico publica
    topicPub:  "senai/grupo2/comandos",     // ← tópico que o Pico assina
    clientId:  "dashboard_" + Math.random().toString(16).slice(2, 8)
    // clientId aleatório evita conflito se dois browsers abrirem ao mesmo tempo
}

// ─── VARIÁVEIS DE ESTADO ─────────────────────────────────────────────────────
let cliente = null

// ─── ELEMENTOS DO DOM ────────────────────────────────────────────────────────
const statusDot = document.getElementById("status-dot")
const statusTexto = document.getElementById("status-texto")
const ultimaAtu = document.getElementById("ultima-atualizacao")
const btnOn = document.getElementById("btn-on")
const btnOff = document.getElementById("btn-off")
const logEl = document.getElementById("log")

// ─── FUNÇÕES AUXILIARES ──────────────────────────────────────────────────────

// Adiciona linha no log com hora e cor por tipo
function log(mensagem, tipo = "info") {
    const cores = {
        info:     "#8b949e",
        sucesso:  "#00ff88",
        erro:     "#ff4444",
        recebido: "#ffaa00",
        enviado:  "#00d4ff"
    }
    const hora = new Date().toLocaleTimeString("pt-BR")
    logEl.innerHTML += `<span style="color:${cores[tipo]}">[${hora}] ${mensagem}</span>\n`
    logEl.scrollTop = logEl.scrollHeight
}

// Atualiza o indicador de status na barra superior
function setStatus(conectado, texto) {
    statusDot.className   = "status-dot" + (conectado ? " conectado" : "")
    statusTexto.textContent = texto
    btnOn.disabled  = !conectado
    btnOff.disabled = !conectado
}

// Atualiza a hora da última leitura recebida
function marcarAtualizacao() {
    ultimaAtu.textContent = "Última leitura: " + new Date().toLocaleTimeString("pt-BR")
}

// ─── PROCESSAR MENSAGEM RECEBIDA ─────────────────────────────────────────────
// Exemplo de mensagem: "temp:24.5,umid:58.0,ldr:72.3"
function processarMensagem(mensagem) {
    log(`[REC] ${mensagem}`, "recebido")

    // Separa cada par chave:valor
    const partes = mensagem.split(",")

    partes.forEach(parte => {
        const [chave, valor] = parte.split(":")

        if (chave === "temp") {
            document.getElementById("temperatura").textContent = valor

            // Alerta visual se temperatura acima de 30°C
            const cardTemp = document.querySelector(".card-temp")
            cardTemp.classList.toggle("alerta", parseFloat(valor) > 30)
        }

        if (chave === "umid") {
            document.getElementById("umidade").textContent = valor
        }

        if (chave === "ldr") {
            document.getElementById("luminosidade").textContent = valor
        }
    })

    marcarAtualizacao()
}

// ─── CONEXÃO MQTT ────────────────────────────────────────────────────────────
function conectar() {
    log(`Conectando ao broker: ${CONFIG.broker}...`)
    setStatus(false, "Conectando...")

    // mqtt.connect() — ponto de entrada da biblioteca MQTT.js
    // "ws://" indica WebSocket sem criptografia
    cliente = mqtt.connect(CONFIG.broker, {
        clientId: CONFIG.clientId,
        clean: true,
        connectTimeout: 10000
    })

    // ── Evento: conexão estabelecida ──────────────────────────────────────────
    cliente.on("connect", () => {
        setStatus(true, "Conectado ao broker")
        log("Conectado com sucesso!", "sucesso")

        // Assina o tópico onde o Pico publica os dados dos sensores
        cliente.subscribe(CONFIG.topicSub, (err) => {
            if (!err) {
                log(`[SUB] Assinando: ${CONFIG.topicSub}`, "info")
            }
        })
    })

    // ── Evento: mensagem recebida ─────────────────────────────────────────────
    // Chamado sempre que o broker entrega uma mensagem no tópico assinado
    cliente.on("message", (topico, payload) => {
        // payload chega como bytes — toString() converte para texto
        // Mesmo conceito do .decode() do MicroPython
        const mensagem = payload.toString()
        processarMensagem(mensagem)
    })

    // ── Evento: erro de conexão ───────────────────────────────────────────────
    cliente.on("error", (err) => {
        log(`[ERRO] ${err.message}`, "erro")
        setStatus(false, "Erro de conexão")
    })

    // ── Evento: desconexão ────────────────────────────────────────────────────
    cliente.on("close", () => {
        setStatus(false, "Desconectado")
        log("Conexão encerrada.", "erro")
    })
}

// ─── PUBLICAR COMANDO PARA O PICO ────────────────────────────────────────────
// Chamado pelos botões "Ligar LED" e "Desligar LED" no HTML
function publicarComando(comando) {
    if (!cliente || !cliente.connected) return

    // publish(tópico, mensagem)
    // O Pico está assinando CONFIG.topicPub e vai receber este comando
    cliente.publish(CONFIG.topicPub, comando)
    log(`[PUB] Comando enviado: "${comando}"`, "enviado")
}

// ─── INICIALIZAÇÃO ────────────────────────────────────────────────────────────
// Conecta automaticamente ao abrir o dashboard
conectar()