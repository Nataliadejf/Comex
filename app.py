import os
from flask import Flask, jsonify
from google.cloud import bigquery
import pandas as pd
from utils.google_cloud import carregar_credenciais_google_temp
import psycopg2
from psycopg2.extras import execute_values

app = Flask(__name__)


@app.route('/api/coletar-empresas-base-dados', methods=['POST'])
def coletar_empresas_base_dados():
    try:
        # 1. Carrega credenciais do Google Cloud (arquivo temporário usado apenas no contexto)
        # 2. Conecta no BigQuery dentro do contexto para garantir limpeza imediata
        query = """
            SELECT cnpj, razao_social, municipio, uf
            FROM `basedosdados.br_bd_diretorios_brasil.empresa`
            LIMIT 1000
        """

        with carregar_credenciais_google_temp():
            client = bigquery.Client(project=os.getenv('GCP_PROJECT') or 'liquid-receiver-483923-n6')
            df = client.query(query).to_dataframe()

        if df.empty:
            return jsonify({"success": True, "message": "Nenhuma empresa encontrada", "total": 0}), 200

        # normalize columns (garante colunas esperadas e valores None para NaN)
        cols = ['cnpj', 'razao_social', 'municipio', 'uf']
        for c in cols:
            if c not in df.columns:
                df[c] = None
        df = df[cols].where(pd.notnull(df), None)

        # 5. Conecta no PostgreSQL
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(dsn=db_url)
        else:
            conn = psycopg2.connect(
                host=os.getenv("DATABASE_HOST"),
                database=os.getenv("DATABASE_NAME"),
                user=os.getenv("DATABASE_USER"),
                password=os.getenv("DATABASE_PASSWORD")
            )
        cursor = conn.cursor()

        # 6. Insere em batch usando execute_values (mais eficiente)
        records = df.to_records(index=False)
        values = [tuple(r) for r in records]

        insert_sql = """
            INSERT INTO empresas (cnpj, razao_social, municipio, uf)
            VALUES %s
            ON CONFLICT (cnpj) DO NOTHING
        """

        execute_values(cursor, insert_sql, values, template=None, page_size=100)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"{len(values)} empresas carregadas com sucesso",
            "total": len(values)
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
