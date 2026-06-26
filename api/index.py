import os
import logging
from fastapi import FastAPI, Form
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from openai import AsyncOpenAI
from mangum import Mangum

# 1. CONFIGURAÇÃO PROFISSIONAL DE LOGS
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. INICIALIZAÇÃO DO APP FASTAPI
app = FastAPI(
    title="SaaS AI Dispatcher - Gringa",
    description="Motor de IA ultrarrápido para atendimento via SMS.",
    version="2.1 - Production Edition"
)

# 3. SEGURANÇA E CONEXÃO COM A IA (GROQ)
CHAVE_API = os.getenv("GROQ_API_KEY")
if not CHAVE_API:
    logger.error("ALERTA CRÍTICO: GROQ_API_KEY não configurada na Vercel!")

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

# ROTA DE STATUS (Health Check)
@app.get("/", tags=["Health Check"])
async def health_check():
    return {
        "status": "operational", 
        "engine": "Groq Llama-3.1 70B", 
        "latency": "ultra-low"
    }

# ROTA PRINCIPAL (Onde o Twilio bate)
@app.post("/webhook", tags=["Twilio Webhook"])
async def twilio_webhook(Body: str = Form(...), From: str = Form(...)):
    logger.info(f"📨 Nova mensagem recebida de {From}: {Body}")
    
    try:
        # Chamada assíncrona para a IA usando o modelo atualizado
        resposta = await client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": Body}
            ],
            temperature=0.3, # Mantém as respostas lógicas e diretas
            max_tokens=100   # Evita respostas longas que gastariam tokens à toa
        )
        
        texto_ia = resposta.choices[0].message.content
        logger.info(f"🤖 Resposta gerada para {From}: {texto_ia}")
        
        # Formatação do XML padrão exigido pelo Twilio
        resposta_twilio = MessagingResponse()
        resposta_twilio.message(texto_ia)
        
        return Response(content=str(resposta_twilio), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"❌ Erro crítico no processamento da IA: {str(e)}")
        
        # PLANO DE CONTINGÊNCIA (Evita que o sistema mostre erro pro cliente)
        fallback = MessagingResponse()
        fallback.message("We are experiencing high volume right now. Please call us directly at 555-0199 for immediate service.")
        return Response(content=str(fallback), media_type="application/xml")

# Adaptador Serverless obrigatório para a Vercel
handler = Mangum(app)
