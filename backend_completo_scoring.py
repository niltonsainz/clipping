from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import pandas as pd
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Carregar dicionário FACIAP
def carregar_dicionario():
    try:
        df = pd.read_csv("config/dicionario_faciap.csv")
        return df
    except:
        # Dicionário de exemplo se não encontrar o arquivo
        return pd.DataFrame({
            'termo': ['educação', 'tecnologia', 'inteligência artificial', 'dados', 'startup', 'inovação'],
            'categoria': ['Educação', 'Tecnologia', 'IA', 'Dados', 'Empreendedorismo', 'Inovação'],
            'peso_interesse': [8, 7, 9, 6, 7, 8],
            'peso_risco': [3, 5, 8, 7, 4, 3]
        })

# Calcular score de uma notícia
def calcular_score(texto, dicionario):
    if not texto:
        return 0, 0, []
    
    texto_lower = texto.lower()
    score_interesse = 0
    score_risco = 0
    categorias_encontradas = []
    
    for _, row in dicionario.iterrows():
        termo = row['termo'].lower()
        if termo in texto_lower:
            score_interesse += row['peso_interesse']
            score_risco += row['peso_risco']
            if row['categoria'] not in categorias_encontradas:
                categorias_encontradas.append(row['categoria'])
    
    return score_interesse, score_risco, categorias_encontradas

@app.route("/api/noticias")
def get_noticias():
    dicionario = carregar_dicionario()
    
    # Notícias com scoring aplicado
    noticias_exemplo = [
        {
            "id": 1,
            "titulo": "Câmara aprova projeto de lei sobre educação digital",
            "fonte": "Câmara dos Deputados",
            "link": "https://www.camara.leg.br/noticias",
            "data_publicacao": "2025-08-27",
            "resumo": "Projeto estabelece diretrizes para implementação de tecnologias educacionais nas escolas públicas brasileiras.",
            "texto_completo": "O projeto de lei sobre educação digital foi aprovado pela Câmara dos Deputados, estabelecendo diretrizes para a implementação de tecnologias educacionais nas escolas públicas. A proposta inclui formação de professores, infraestrutura tecnológica e desenvolvimento de conteúdo digital.",
            "favorita": False
        },
        {
            "id": 2,
            "titulo": "Senado debate marco regulatório da inteligência artificial",
            "fonte": "Senado Federal",
            "link": "https://www12.senado.leg.br/noticias",
            "data_publicacao": "2025-08-27",
            "resumo": "Comissão discute regras para uso ético de IA no setor público e privado.",
            "texto_completo": "O Senado Federal iniciou debates sobre o marco regulatório da inteligência artificial no Brasil. A proposta visa estabelecer regras para o uso ético e responsável de IA, proteção de dados pessoais e transparência algorítmica.",
            "favorita": False
        },
        {
            "id": 3,
            "titulo": "Nova lei de proteção de dados pessoais em tramitação",
            "fonte": "Câmara dos Deputados",
            "link": "https://www.camara.leg.br/noticias",
            "data_publicacao": "2025-08-26",
            "resumo": "Proposta amplia direitos dos cidadãos e estabelece penalidades mais rigorosas.",
            "texto_completo": "A nova lei de proteção de dados pessoais em tramitação na Câmara amplia os direitos dos cidadãos e estabelece penalidades mais rigorosas para empresas que violarem a privacidade. A proposta inclui maior controle sobre dados pessoais.",
            "favorita": False
        },
        {
            "id": 4,
            "titulo": "Comissão aprova incentivos fiscais para startups",
            "fonte": "Senado Federal",
            "link": "https://www12.senado.leg.br/noticias",
            "data_publicacao": "2025-08-26",
            "resumo": "Medida visa estimular empreendedorismo e inovação tecnológica.",
            "texto_completo": "A Comissão de Assuntos Econômicos do Senado aprovou incentivos fiscais para startups brasileiras. A medida visa estimular o empreendedorismo, inovação tecnológica e desenvolvimento de novas tecnologias no país.",
            "favorita": False
        }
    ]
    
    # Aplicar scoring em cada notícia
    for noticia in noticias_exemplo:
        texto_completo = noticia.get('texto_completo', '' ) + ' ' + noticia.get('titulo', '')
        score_interesse, score_risco, categorias = calcular_score(texto_completo, dicionario)
        
        noticia['score_interesse'] = score_interesse
        noticia['score_risco'] = score_risco
        noticia['categorias'] = categorias
        noticia['score_total'] = score_interesse + score_risco
    
    # Ordenação
    ordenacao = request.args.get('ordenacao', 'data')
    if ordenacao == 'score':
        noticias_exemplo.sort(key=lambda x: x['score_total'], reverse=True)
    elif ordenacao == 'interesse':
        noticias_exemplo.sort(key=lambda x: x['score_interesse'], reverse=True)
    elif ordenacao == 'risco':
        noticias_exemplo.sort(key=lambda x: x['score_risco'], reverse=True)
    else:  # data
        noticias_exemplo.sort(key=lambda x: x['data_publicacao'], reverse=True)
    
    return jsonify({
        "noticias": noticias_exemplo, 
        "total": len(noticias_exemplo),
        "dicionario_termos": len(dicionario)
    })

@app.route("/api/noticias/<int:noticia_id>/favoritar", methods=["POST"])
def favoritar_noticia(noticia_id):
    # Aqui você salvaria no banco de dados real
    return jsonify({"success": True, "message": f"Notícia {noticia_id} favoritada!"})

@app.route("/api/categorias")
def get_categorias():
    dicionario = carregar_dicionario()
    categorias = dicionario['categoria'].unique().tolist()
    return jsonify({"categorias": categorias})

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "Clipping FACIAP"})

if __name__ == "__main__":
    print("🚀 Backend FACIAP com Scoring iniciado!")
    print("📍 Health: http://localhost:5000/health" )
    print("📰 Notícias: http://localhost:5000/api/noticias" )
    print("📊 Categorias: http://localhost:5000/api/categorias" )
    app.run(host="0.0.0.0", port=5000, debug=True)
