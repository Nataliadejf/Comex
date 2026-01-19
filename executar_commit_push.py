"""
Script para executar commit e push das mudanças.
Execute: python executar_commit_push.py
"""
import subprocess
import sys
import os
from pathlib import Path

def executar_comando(cmd, descricao, cwd=None):
    """Executa um comando e retorna o resultado."""
    print(f"\n{'='*60}")
    print(f"🔄 {descricao}")
    print(f"{'='*60}")
    
    try:
        # Usar shell=True no Windows para melhor compatibilidade
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or str(Path(__file__).parent),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"⚠️ Saída de erro: {result.stderr}")
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Erro ao executar comando: {e}")
        return False

def main():
    """Executa commit e push."""
    print("\n🚀 INICIANDO COMMIT E PUSH DAS MUDANÇAS\n")
    
    projeto_dir = Path(__file__).parent
    
    # 1. Verificar status atual
    print("\n📋 Status atual do repositório:")
    executar_comando("git status --short", "Verificando status", projeto_dir)
    
    # 2. Adicionar todos os arquivos
    if not executar_comando("git add -A", "Adicionando arquivos ao stage", projeto_dir):
        print("⚠️ Aviso ao adicionar arquivos (continuando...)")
    
    # 3. Verificar o que será commitado
    print("\n📊 Arquivos que serão commitados:")
    executar_comando("git diff --cached --name-only", "Verificando mudanças", projeto_dir)
    
    # 4. Fazer commit
    commit_msg = """Remove senhas expostas, ajusta Dashboard mobile, adiciona endpoint deletar usuário

- Remove senhas expostas dos arquivos .md
- Ajusta Dashboard para mobile (cards, gráficos, tabelas responsivos)
- Adiciona endpoint POST /admin/usuarios/deletar-por-email
- Cria script deletar_usuarios.py para deletar usuários específicos
- Corrige render.yaml removendo duplicação"""
    
    # Tentar commit normal primeiro
    sucesso_commit = executar_comando(
        f'git commit -m "{commit_msg.replace(chr(10), " ")}"',
        "Fazendo commit",
        projeto_dir
    )
    
    # Se falhar, tentar commit vazio (pode já estar tudo commitado)
    if not sucesso_commit:
        print("\n⚠️ Commit normal falhou. Tentando commit vazio...")
        sucesso_commit = executar_comando(
            'git commit --allow-empty -m "Atualização: Remove senhas expostas, ajusta Dashboard mobile"',
            "Fazendo commit vazio",
            projeto_dir
        )
    
    # 5. Fazer push
    if sucesso_commit or True:  # Tentar push mesmo se commit falhou (pode já estar commitado)
        if not executar_comando("git push origin main", "Fazendo push para GitHub", projeto_dir):
            print("\n❌ Falha ao fazer push")
            return False
    
    print("\n" + "="*60)
    print("✅ PROCESSO CONCLUÍDO!")
    print("="*60)
    print("\n📡 O Render vai detectar as mudanças e fazer deploy automaticamente.")
    print("   Acompanhe o deploy em: https://dashboard.render.com")
    print("\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        sys.exit(1)
