# Clint Webhook App

## Funcionalidades

### 1. Recebimento de Webhooks para Novos Leads
- Recebe webhooks do Clint CRM quando um lead entra na etapa 1
- Armazena informações do lead (nome, email, celular)
- Inicia monitoramento do tempo de permanência na etapa 1

### 2. Notificação de Leads Antigos
- Monitora leads que permanecem na etapa 1 por mais de 7 dias
- Envia webhook de notificação ao Clint CRM quando um lead ultrapassa o limite
- Remove leads antigos do banco de dados após 30 dias

### 3. Monitoramento de Mudança de Etapa (Nova!)
- Recebe webhooks quando um lead é movido da etapa 1
- Para de monitorar leads que saíram da etapa 1
- Remove leads movidos do banco de dados após 15 dias

## Endpoints

### 1. `/webhook/clint` (POST)
Recebe webhooks de novos leads na etapa 1.

Formato do payload:
```json
{
  "name": "Nome do Lead",
  "email": "email@do.lead",
  "phone": "11999999999"
}
