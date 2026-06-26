import os
import logging
from fastapi import FastAPI, Form
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from openai import AsyncOpenAI  # <-- UPGRADE: Async para velocidade extrema
from mangum import Mangum

# 1. CONFIGURAÇÃO PROFISSIONAL DE LOGS (Monitoramento)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. INICIALIZAÇÃO DO APP COM METADADOS
app = FastAPI(
    title="SaaS AI Dispatcher - Gringa",
    description="Motor de IA ultrarrápido para atendimento via SMS.",
    version="2.0 - Pro Edition"
)

# 3. SEGURANÇA E CONEXÃO COM A IA
CHAVE_API = os.getenv("GROQ_API_KEY")
if not CHAVE_API:
    logger.error("ALERTA CRÍTICO: GROQ_API_KEY não configurada na Vercel!")

# Usando o cliente Assíncrono (Alta performance em Serverless)
client = AsyncOpenAI(
    api_key=CHAVE_API,
    base_url="https://api.groq.com/openai/v1"
)

# 4. ENGENHARIA DE PROMPT AVANÇADA (O Cérebro da Operação)
PROMPT_SISTEMA = """
You are 'Alex', an expert AI dispatcher for 'Texas Cool HVAC'. 
Your personality is highly professional, empathetic, and exceptionally concise.
Your main objective is to:
1. Acknowledge the customer's HVAC issue.
2. Ask for their address.
3. Offer to schedule a technician visit.

CRITICAL RULES:
- NEVER invent pricing, wait times, or technician names.
- Keep responses under 2 short sentences (this is SMS, keep it brief).
- Always reply in English.
"""

# ROTA DE STATUS (Para você saber que está rodando)
@app.get("/", tags=["Health Check"])
async def health_check():
    return {
        "status": "operational", 
        "engine": "Groq Llama-3 70B", 
        "latency": "ultra-low"
    }

# ROTA PRINCIPAL (Onde o Twilio bate)
@app.post("/webhook", tags=["Twilio Webhook"])
async def twilio_webhook(Body: str = Form(...), From: str = Form(...)):
    logger.info(f"📨 Nova mensagem recebida de {From}: {Body}")
    
    try:
        # ⚡ Chamada assíncrona para a IA
        resposta = await client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": Body}
            ],
            temperature=0.3, # Baixa temperatura = respostas lógicas, sem "criatividade" maluca
            max_tokens=100   # Força respostas curtas para economizar $$
        )
        
        texto_ia = resposta.choices[0].message.content
        logger.info(f"🤖 Resposta gerada para {From}: {texto_ia}")
        
        # 📦 Formatação do XML para o Twilio
        resposta_twilio = MessagingResponse()
        resposta_twilio.message(texto_ia)
        
        return Response(content=str(resposta_twilio), media_type="application/xml")
        
   except Exception as e:
        logger.error(f"❌ Erro crítico no processamento da IA: {str(e)}") # <--- Adicionei o str(e) aqui
        
        # 🛟 PLANO DE CONTINGÊNCIA (Fallback)
        fallback = MessagingResponse()
        fallback.message("We are experiencing high volume right now. Please call us directly at 555-0199 for immediate service.")
        return Response(content=str(fallback), media_type="application/xml")
