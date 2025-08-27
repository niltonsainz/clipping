from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/noticias")
def get_noticias():
    noticias_exemplo = [
        {
            "titulo": "Câmara aprova projeto de lei sobre educação digital",
            "fonte": "Câmara dos Deputados",
            "link": "https://www.camara.leg.br/noticias",
            "data_publicacao": "2025-08-27",
            "resumo": "Projeto estabelece diretrizes para implementação de tecnologias educacionais."
        },
        {
            "titulo": "Senado debate marco regulatório da inteligência artificial",
            "fonte": "Senado Federal", 
            "link": "https://www12.senado.leg.br/noticias",
            "data_publicacao": "2025-08-27",
            "resumo": "Comissão discute regras para uso ético de IA."
        },
        {
            "titulo": "Nova lei de proteção de dados pessoais",
            "fonte": "Câmara dos Deputados",
            "link": "https://www.camara.leg.br/noticias", 
            "data_publicacao": "2025-08-26",
            "resumo": "Proposta amplia direitos dos cidadãos."
        },
        {
            "titulo": "Incentivos fiscais para startups aprovados",
            "fonte": "Senado Federal",
            "link": "https://www12.senado.leg.br/noticias",
            "data_publicacao": "2025-08-26", 
            "resumo": "Medida estimula empreendedorismo e inovação."
        }
    ]
    
    return jsonify({"noticias": noticias_exemplo, "total": len(noticias_exemplo )})

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "Clipping FACIAP"})

if __name__ == "__main__":
    print("Backend FACIAP iniciado!")
    print("Acesse: http://localhost:5000/api/noticias" )
    app.run(host="0.0.0.0", port=5000, debug=True)
