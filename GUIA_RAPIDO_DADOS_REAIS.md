# 🚀 Guia Rápido - Dados Reais

## ✅ Passo a Passo Simplificado

### 1️⃣ Remover Dados de Exemplo

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/integrar_api_real.py
```

✅ **Resultado:** Dados de exemplo removidos

### 2️⃣ Baixar Arquivos CSV Reais

1. **Acesse:** https://comexstat.mdic.gov.br
2. **Navegue:** Dados Abertos > Download
3. **Baixe:**
   - Exportação (últimos 3 meses)
   - Importação (últimos 3 meses)
4. **Salve em:**
   ```
   C:\Users\User\Desktop\Cursor\Projetos\data\raw\
   ```

### 3️⃣ Processar Arquivos

```powershell
python scripts/process_files.py
```

✅ **Resultado:** Dados reais importados no banco

### 4️⃣ Verificar Dashboard

1. Inicie o backend: `python run.py`
2. Inicie o frontend: `npm start` (na pasta frontend)
3. Acesse: http://localhost:3000

## 🗄️ Configurar MySQL Workbench (Opcional)

### Gerar Scripts SQL

```powershell
python scripts/configurar_banco_mysql.py
```

### No MySQL Workbench

1. Abra o MySQL Workbench
2. Conecte ao servidor
3. Abra: `scripts/sql/create_tables_mysql.sql`
4. Execute o script (Ctrl+Shift+Enter)

### Configurar Conexão

Edite `backend/.env`:

```env
DATABASE_URL=mysql+pymysql://usuario:senha@localhost:3306/comex_analyzer
```

## 📋 Checklist

- [ ] Dados de exemplo removidos
- [ ] Arquivos CSV baixados do portal
- [ ] Arquivos salvos em `data/raw/`
- [ ] Arquivos processados (`process_files.py`)
- [ ] Dashboard acessível e funcionando
- [ ] MySQL configurado (opcional)

## 🎯 Próximos Passos

Após popular com dados reais:

1. ✅ Explore o dashboard com filtros
2. ✅ Exporte relatórios
3. ✅ Configure agendamento mensal
4. ✅ Use MySQL Workbench para análises avançadas

---

**Última atualização**: Janeiro 2025



