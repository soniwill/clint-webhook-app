from sqlalchemy import inspect
from database import engine, Base, Lead, get_db
from sqlalchemy import Column, Boolean, DateTime
from sqlalchemy.sql import text

def run_migrations():
    """Executa migrações necessárias no banco de dados"""
    db = get_db()
    
    # Verificar se a coluna in_stage_one já existe
    inspector = inspect(engine)
    columns = [column['name'] for column in inspector.get_columns('leads')]
    
    # Adicionar coluna in_stage_one se não existir
    if 'in_stage_one' not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE leads ADD COLUMN in_stage_one BOOLEAN DEFAULT TRUE"))
            print("Coluna 'in_stage_one' adicionada com sucesso")
    
    # Adicionar coluna moved_at se não existir
    if 'moved_at' not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE leads ADD COLUMN moved_at TIMESTAMP"))
            print("Coluna 'moved_at' adicionada com sucesso")
    
    # Atualizar todos os leads existentes para in_stage_one = True
    try:
        db.query(Lead).filter(Lead.in_stage_one.is_(None)).update({Lead.in_stage_one: True})
        db.commit()
        print("Leads existentes atualizados com sucesso")
    except Exception as e:
        db.rollback()
        print(f"Erro ao atualizar leads existentes: {str(e)}")
    
    print("Migrações concluídas com sucesso")

if __name__ == "__main__":
    run_migrations()
