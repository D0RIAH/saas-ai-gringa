import os
import logging
from fastapi import FastAPI, Form
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from openai import AsyncOpenAI
from mangum import Mangum

# 1. CONFIGURAÇÃO DE LOGS
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. INICIALIZAÇÃO DO APP
app = FastAPI(
    title="SaaS AI Dispatcher - Gringa",
    description="Motor de IA ultrarrápido para atendimento via SMS.",
    version="2.0 - Pro Edition"
)

# 3. SEGURANÇA E CONEXÃO COM A IA
CHAVE_API = os.getenv("GROQ_API_KEY")
if not CHAVE_API:
    logger.error("ALERTA CRÍTICO: GROQ_API_KEY não configurada na Vercel!")

client = AsyncOpenAI(
    api_key=CHAVE_API,
    base_url="https://api.groq.com/openai/v1"
)

# 4. ENGENHARIA DE PROMPT (O Cérebro)
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

@app.get("/", tags=["Health Check"])
async def health_check():
    return {
        "status": "operational", 
        "engine": "Groq Llama-3 70B", 
        "latency": "ultra-low"
    }

@app.post("/webhook", tags=["Twilio Webhook"])
async def twilio_webhook(Body: str = Form(...), From: str = Form(...)):
    logger.info(f"📨 Nova mensagem recebida de {From}: {Body}")
    
    try:
        # Chamada para a IA
        resposta = await client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": Body}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        texto_ia = resposta.choices[0].message.content
        logger.info(f"🤖 Resposta gerada para {From}: {texto_ia}")
        
        # XML para o Twilio
        resposta_twilio = MessagingResponse()
        resposta_twilio.message(texto_ia)
        
        return Response(content=str(resposta_twilio), media_type="application/xml")
        
    except Exception as e:
        # AQUI ESTÁ O NOSSO DETETIVE DE ERROS
        logger.error(f"❌ Erro crítico no processamento da IA: {str(e)}")
        
        fallback = MessagingResponse()
        fallback.message("We are experiencing high volume right now. Please call us directly at 555-0199 for immediate service.")
        return Response(content=str(fallback), media_type="application/xml")

# ATENÇÃO: Esta linha é o que a Vercel procura. Não pode ter espaço antes dela.
handler = Mangum(app)
