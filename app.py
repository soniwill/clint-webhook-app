from flask import Flask, request, jsonify
import logging
from database import init_db
from webhook_handler import process_incoming_webhook, process_stage_change_webhook
from scheduler import start_scheduler
from config import Config

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar banco de dados
init_db()

# Executar migrações
try:
    from migrations import run_migrations
    run_migrations()
except Exception as e:
    logger.error(f"Erro ao executar migrações: {str(e)}")

# Inicializar agendador
scheduler = start_scheduler()

@app.route('/webhook/clint', methods=['POST'])
def receive_webhook():
    """Endpoint para receber webhooks do Clint CRM"""
    if request.method == 'POST':
        try:
            data = request.json
            logger.info(f"Webhook recebido: {data}")
            
            if process_incoming_webhook(data):
                return jsonify({"status": "success", "message": "Webhook processado com sucesso"}), 200
            else:
                return jsonify({"status": "error", "message": "Erro ao processar webhook"}), 400
        
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Método não permitido"}), 405

@app.route('/webhook/clint/stage-change', methods=['POST'])
def lead_stage_change():
    """Endpoint para receber webhooks do Clint CRM quando um lead muda de etapa"""
    if request.method == 'POST':
        try:
            data = request.json
            logger.info(f"Webhook de mudança de etapa recebido: {data}")
            
            if process_stage_change_webhook(data):
                return jsonify({"status": "success", "message": "Mudança de etapa processada com sucesso"}), 200
            else:
                return jsonify({"status": "error", "message": "Erro ao processar mudança de etapa"}), 400
        
        except Exception as e:
            logger.error(f"Erro ao processar webhook de mudança de etapa: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Método não permitido"}), 405

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificação de saúde da aplicação"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(Config.PORT) if hasattr(Config, 'PORT') else 5000)
