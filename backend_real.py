from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

def carregar_dicionario():
    try:
        df = pd.read_csv("config/dicionario_faciap.csv")
        return df
    except:
        return pd.DataFrame({
            'termo': ['educação', 'tecnologia', 'inteligência artificial', 'dados'],
            'categoria': ['Educação', 'Tecnologia', 'IA', 'Dados'],
            'peso_interesse': [8, 7, 9, 6],
            'peso_risco': [3, 5, 8, 7]
        })

def calcular_score_noticia(texto, dicionario):
    if not texto:
        return 0, 0, []
    
    texto_lower = texto.lower()
    score_interesse = 0
    score_risco = 0
    categorias = []
    
    for _, row in dicionario.iterrows():
        if row['termo'].lower() in texto_lower:
            score_interesse += row['peso_interesse']
            score_risco += row['peso_risco']
            if row['categoria'] not in categorias:
                categorias.append(row['categoria'])
    
    return score_interesse, score_risco, categorias

@app.route("/api/noticias")
def get_noticias():
    try:
        conn = sqlite3.connect("clipping_faciap.db")
        cursor = conn.cursor()
        
        # Buscar notícias reais do banco
        cursor.execute("""
            SELECT id, titulo, fonte, link, data_publicacao, texto_completo, 
                   score_interesse, score_risco, favorita
            FROM noticias 
            ORDER BY data_publicacao DESC 
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({"noticias": [], "total": 0, "erro": "Nenhuma notícia encontrada"})
        
        # Carregar dicionário para recalcular scores
        dicionario = carregar_dicionario()
        
        noticias = []
        for row in rows:
            # Recalcular score baseado no dicionário
            texto_completo = (row[5] or "") + " " + (row[1] or "")
            score_interesse, score_risco, categorias = calcular_score_noticia(texto_completo, dicionario)
            
            noticia = {
                "id": row[0],
                "titulo": row[1] or "Título não disponível",
                "fonte": row[2] or "Fonte não informada",
                "link": row[3] or "#",
                "data_publicacao": row[4] or "Data não informada",
                "resumo": (row[5] or "")[:200] + "..." if row[5] and len(row[5]) > 200 else (row[5] or "Resumo não disponível"),
                "score_interesse": score_interesse,
                "score_risco": score_risco,
                "categorias": categorias,
                "favorita": bool(row[8]) if row[8] else False
            }
            noticias.append(noticia)
        
        # Ordenação
        ordenacao = request.args.get('ordenacao', 'data')
        if ordenacao == 'score_interesse':
            noticias.sort(key=lambda x: x['score_interesse'], reverse=True)
        elif ordenacao == 'score_risco':
            noticias.sort(key=lambda x: x['score_risco'], reverse=True)
        elif ordenacao == 'score_total':
            noticias.sort(key=lambda x: x['score_interesse'] + x['score_risco'], reverse=True)
        
        return jsonify({
            "noticias": noticias,
            "total": len(noticias),
            "fonte": "Dados reais coletados",
            "dicionario_termos": len(dicionario)
        })
        
    except Exception as e:
        return jsonify({
            "erro": str(e),
            "noticias": [],
            "total": 0
        }), 500

@app.route("/api/noticias/<int:noticia_id>/favoritar", methods=["POST"])
def favoritar_noticia(noticia_id):
    try:
        conn = sqlite3.connect("clipping_faciap.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE noticias SET favorita = 1 WHERE id = ?", (noticia_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Notícia {noticia_id} favoritada!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "Clipping FACIAP Real"})

if __name__ == "__main__":
    print("🚀 Backend com Dados REAIS iniciado!")
    print("📍 Health: http://localhost:5000/health" )
    print("📰 Notícias Reais: http://localhost:5000/api/noticias" )
    app.run(host="0.0.0.0", port=5000, debug=True)
