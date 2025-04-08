from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

# Configuração do banco de dados
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)
    in_stage_one = Column(Boolean, default=True)  # Novo campo para rastrear se o lead está na etapa 1
    moved_at = Column(DateTime, nullable=True)    # Quando o lead foi movido da etapa 1
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
            "notified": self.notified,
            "in_stage_one": self.in_stage_one,
            "moved_at": self.moved_at.isoformat() if self.moved_at else None
        }

# Criar tabelas
def init_db(db_engine=None):
    if db_engine:
        Base.metadata.create_all(bind=db_engine)
    else:
        Base.metadata.create_all(bind=engine)

# Obter sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
