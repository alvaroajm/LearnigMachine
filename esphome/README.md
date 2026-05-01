# ESPHome — M5Stack ATOM ECHO (modelo antigo)

Projeto ESPHome para transformar o **ATOM ECHO** (ESP32-PICO-D4, sem PSRAM, sem S3) em um satélite de voz do Home Assistant via **HA Satellite Assist**.

## Hardware

| Componente | Chip | Pinos |
|---|---|---|
| MCU | ESP32-PICO-D4 | — |
| Microfone | SPM1423 (PDM) | CLK=GPIO19, DATA=GPIO23, WS=GPIO33 |
| Alto-falante | NS4168 (I2S) | BCLK=GPIO19, LRCLK=GPIO33, DIN=GPIO22 |
| LED RGB | WS2812B | GPIO27 |
| Botão | — | GPIO39 (ativo em LOW) |

## Pré-requisitos no Home Assistant

1. **Add-on ESPHome** instalado e rodando  
2. **Integração Wyoming** (já inclusa no HA 2023.10+)  
3. Pipeline de voz configurado em **Configurações → Assistente → Pipelines**  
   - STT: Whisper (local) ou serviço em nuvem  
   - TTS: Piper (local) ou serviço em nuvem  
   - Wake word: **openWakeWord** (roda no servidor HA) ← necessário para este hardware

## Configuração rápida

```bash
# 1. Clone / abra o projeto no ESPHome Dashboard
# 2. Copie secrets.yaml.example → secrets.yaml e preencha os valores
cp secrets.yaml secrets_real.yaml   # renomeie conforme preferir
# 3. Compile e grave via USB na primeira vez
esphome run atom-echo.yaml
# 4. As próximas atualizações podem ser feitas via OTA
```

## Modos de operação

| Switch "Wake Word" no HA | Comportamento |
|---|---|
| **Desligado** (padrão) | Push-to-talk: segure o botão para falar |
| **Ligado** | Streaming contínuo → HA detecta wake word via openWakeWord |

> **Nota:** O microWakeWord (on-device) exige PSRAM, não disponível neste modelo.  
> A detecção de wake word acontece no servidor HA com openWakeWord.

## Estados do LED

| Cor / Efeito | Estado |
|---|---|
| Vermelho → Verde (boot) | Inicializando |
| Azul pulsante (laranja se sem HA) | Idle / aguardando |
| Azul brilhante pulsante | Ouvindo |
| Verde pulsante | Processando fala (STT) |
| Verde estático | Reproduzindo resposta (TTS) |
| Vermelho fixo | Erro |

## Configuração do Pipeline no HA

1. Vá em **Configurações → Assistente → Pipelines → Adicionar pipeline**  
2. Selecione:
   - Wake word engine: **openWakeWord**
   - Palavra de ativação: `hey_jarvis`, `ok_nabu` ou outra disponível
3. Salve e atribua o pipeline ao dispositivo ATOM Echo

## Estrutura dos arquivos

```
esphome/
├── atom-echo.yaml   ← configuração principal
├── secrets.yaml     ← credenciais (não versionar com dados reais)
└── README.md
```
