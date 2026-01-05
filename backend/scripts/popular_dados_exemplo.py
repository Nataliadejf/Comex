"""
Script para popular o banco de dados com dados de exemplo.
Útil para testes quando a API do Comex Stat não está disponível.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_db, init_db, OperacaoComex, TipoOperacao, ViaTransporte
from loguru import logger

# Dados de exemplo
NCMs_EXEMPLO = [
    ("87083090", "Partes e acessórios para veículos automóveis"),
    ("73182200", "Parafusos e porcas de ferro ou aço"),
    ("84713012", "Notebooks"),
    ("85171200", "Telefones celulares"),
    ("30049099", "Medicamentos"),
    ("27090000", "Óleo cru de petróleo"),
    ("10019000", "Trigo"),
    ("02012000", "Carne bovina"),
    ("09011100", "Café não torrado"),
    ("15091000", "Óleo de oliva"),
]

PAISES_EXEMPLO = [
    "China", "Estados Unidos", "Argentina", "Alemanha", "Japão",
    "Coreia do Sul", "Itália", "França", "Reino Unido", "México",
    "Chile", "Paraguai", "Uruguai", "Espanha", "Canadá"
]

UFS_EXEMPLO = ["SP", "RJ", "RS", "PR", "SC", "MG", "BA", "GO", "PE", "CE"]

EMPRESAS_IMPORTADORAS = [
    "Importadora ABC Ltda",
    "Comércio Exterior XYZ S.A.",
    "Importadora Global Brasil",
    "Trading Company Internacional",
    "Importadora Sul Americana",
    "Comércio Exterior Premium",
    "Importadora Nacional",
    "Trading Brasil Export",
]

EMPRESAS_EXPORTADORAS = [
    "Exportadora Brasileira S.A.",
    "Comércio Exterior Nacional",
    "Exportadora do Sul",
    "Brasil Export Trading",
    "Exportadora Premium",
    "Comércio Exterior Global",
    "Exportadora Internacional",
    "Brasil Trading Export",
]

def gerar_dados_exemplo(num_registros=1000):
    """Gera dados de exemplo para popular o banco."""
    logger.info(f"Gerando {num_registros} registros de exemplo...")
    
    # Inicializar banco
    init_db()
    db = next(get_db())
    
    registros_criados = 0
    
    # Gerar registros para os últimos 24 meses
    hoje = datetime.now()
    
    for i in range(num_registros):
        # Data aleatória nos últimos 24 meses
        dias_aleatorios = random.randint(0, 730)
        data_operacao = hoje - timedelta(days=dias_aleatorios)
        mes_referencia = data_operacao.strftime("%Y-%m")
        
        # Tipo de operação aleatório
        tipo_op = random.choice([TipoOperacao.IMPORTACAO, TipoOperacao.EXPORTACAO])
        
        # NCM aleatório
        ncm, descricao = random.choice(NCMs_EXEMPLO)
        
        # País aleatório
        pais = random.choice(PAISES_EXEMPLO)
        
        # UF aleatória
        uf = random.choice(UFS_EXEMPLO)
        
        # Valores aleatórios (entre 1.000 e 1.000.000 USD)
        valor_fob = round(random.uniform(1000, 1000000), 2)
        
        # Peso aleatório (entre 100 e 100.000 kg)
        peso_liquido = round(random.uniform(100, 100000), 2)
        
        # Empresa baseada no tipo de operação
        if tipo_op == TipoOperacao.IMPORTACAO:
            empresa_importadora = random.choice(EMPRESAS_IMPORTADORAS)
            empresa_exportadora = None
        else:
            empresa_importadora = None
            empresa_exportadora = random.choice(EMPRESAS_EXPORTADORAS)
        
        # Criar registro
        operacao = OperacaoComex(
            ncm=ncm,
            descricao_produto=descricao,
            tipo_operacao=tipo_op,
            pais_origem_destino=pais,
            uf=uf,
            porto_aeroporto=f"Porto de {uf}",
            razao_social_importador=empresa_importadora,
            razao_social_exportador=empresa_exportadora,
            via_transporte=random.choice(list(ViaTransporte)),
            valor_fob=valor_fob,
            peso_liquido_kg=peso_liquido,
            peso_bruto_kg=peso_liquido * 1.1,  # Peso bruto ~10% maior
            quantidade_estatistica=random.randint(1, 1000),
            unidade_medida_estatistica="KG",
            data_operacao=data_operacao.date(),
            mes_referencia=mes_referencia,
        )
        
        db.add(operacao)
        registros_criados += 1
        
        # Commit a cada 100 registros
        if registros_criados % 100 == 0:
            try:
                db.commit()
                logger.info(f"✓ {registros_criados} registros criados...")
            except Exception as e:
                db.rollback()
                logger.error(f"Erro ao commitar: {e}")
    
    # Commit final
    try:
        db.commit()
        logger.success(f"✅ Total de {registros_criados} registros criados com sucesso!")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao fazer commit final: {e}")
        raise
    
    db.close()
    
    return registros_criados

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("POPULANDO BANCO DE DADOS COM DADOS DE EXEMPLO")
    logger.info("=" * 60)
    
    try:
        num_registros = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
        registros = gerar_dados_exemplo(num_registros)
        
        logger.info("=" * 60)
        logger.success(f"✅ Banco populado com {registros} registros!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

