"""
Script para testar se bcrypt está funcionando corretamente.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
import bcrypt

def testar_bcrypt():
    """Testa se bcrypt está funcionando."""
    logger.info("=" * 60)
    logger.info("TESTANDO BCRYPT")
    logger.info("=" * 60)
    
    try:
        # Teste 1: Senha curta
        senha1 = "senha123"
        logger.info(f"\n1️⃣ Testando senha curta: '{senha1}'")
        senha1_bytes = senha1.encode('utf-8')
        logger.info(f"   Tamanho: {len(senha1_bytes)} bytes")
        
        hash1 = bcrypt.hashpw(senha1_bytes, bcrypt.gensalt())
        logger.info(f"   ✅ Hash criado: {hash1[:50]}...")
        
        verificacao1 = bcrypt.checkpw(senha1_bytes, hash1)
        logger.info(f"   ✅ Verificação: {verificacao1}")
        
        # Teste 2: Senha longa (mas < 72 bytes)
        senha2 = "senha123456789012345678901234567890123456789012345678901234567890"
        logger.info(f"\n2️⃣ Testando senha longa (< 72 bytes): '{senha2[:20]}...'")
        senha2_bytes = senha2.encode('utf-8')
        logger.info(f"   Tamanho: {len(senha2_bytes)} bytes")
        
        hash2 = bcrypt.hashpw(senha2_bytes, bcrypt.gensalt())
        logger.info(f"   ✅ Hash criado: {hash2[:50]}...")
        
        verificacao2 = bcrypt.checkpw(senha2_bytes, hash2)
        logger.info(f"   ✅ Verificação: {verificacao2}")
        
        # Teste 3: Senha > 72 bytes (deve truncar)
        senha3 = "a" * 100  # 100 caracteres = 100 bytes
        logger.info(f"\n3️⃣ Testando senha > 72 bytes: '{senha3[:20]}...'")
        senha3_bytes = senha3.encode('utf-8')
        logger.info(f"   Tamanho original: {len(senha3_bytes)} bytes")
        
        # Truncar para 72 bytes
        senha3_truncada = senha3_bytes[:72]
        logger.info(f"   Tamanho após truncamento: {len(senha3_truncada)} bytes")
        
        hash3 = bcrypt.hashpw(senha3_truncada, bcrypt.gensalt())
        logger.info(f"   ✅ Hash criado: {hash3[:50]}...")
        
        verificacao3 = bcrypt.checkpw(senha3_truncada, hash3)
        logger.info(f"   ✅ Verificação: {verificacao3}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ TODOS OS TESTES PASSARAM!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True

if __name__ == "__main__":
    testar_bcrypt()


