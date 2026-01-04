# 💾 Verificação de Capacidade Local

## 📊 Análise de Requisitos

### Dados Estimados:
- **Registros por operação**: ~500 bytes
- **Registros planejados**: 3.000 - 10.000 inicialmente
- **Crescimento mensal**: ~1.000 - 5.000 registros
- **Espaço necessário**: ~1.5MB - 5MB inicialmente

### Requisitos de Sistema:
- **RAM**: Mínimo 2GB (recomendado 4GB+)
- **Disco**: Mínimo 1GB livre (recomendado 5GB+)
- **CPU**: Qualquer processador moderno

---

## ✅ Verificação Automática

Execute o script para verificar capacidade:

```bash
python backend/scripts/verificar_capacidade.py
```

---

## 📋 Checklist Manual

### Espaço em Disco:
- [ ] Verificar espaço disponível: `df -h` (Linux/Mac) ou verificar propriedades do disco (Windows)
- [ ] Ter pelo menos **5GB livres** recomendado
- [ ] Banco SQLite ocupará ~1-10MB inicialmente

### Memória RAM:
- [ ] Verificar RAM disponível
- [ ] Ter pelo menos **2GB livres** durante execução
- [ ] Backend usa ~200-500MB
- [ ] Frontend usa ~100-300MB

### Processador:
- [ ] Qualquer processador moderno é suficiente
- [ ] Não precisa de alta performance para desenvolvimento

---

## ⚠️ Se Não Tiver Capacidade Suficiente

### Opções:
1. **Limpar espaço em disco**
   - Remover arquivos temporários
   - Desinstalar programas não usados
   - Limpar cache do navegador

2. **Usar hospedagem na nuvem**
   - Ver arquivo: `OPCOES_HOSPEDAGEM.md`
   - Recomendado: Render.com ou Railway.app ($5-7/mês)

3. **Reduzir quantidade de dados**
   - Gerar menos registros inicialmente
   - Usar script: `popular_banco_rapido.py` com menos registros

---

## 🚀 Próximos Passos

1. Execute verificação de capacidade
2. Se OK, execute `POPULAR_BANCO.bat`
3. Se não OK, considere hospedagem na nuvem


