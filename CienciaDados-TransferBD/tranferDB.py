import psycopg2
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONEXÕES
# =========================
origem = psycopg2.connect(
    dbname=os.getenv("DB_ORIGEM_NAME"),
    user=os.getenv("DB_ORIGEM_USER"),
    password=os.getenv("DB_ORIGEM_PASSWORD"),
    host=os.getenv("DB_ORIGEM_HOST"),
    port=os.getenv("DB_ORIGEM_PORT")
)

destino = psycopg2.connect(
    dbname=os.getenv("DB_DESTINO_NAME"),
    user=os.getenv("DB_DESTINO_USER"),
    password=os.getenv("DB_DESTINO_PASSWORD"),
    host=os.getenv("DB_DESTINO_HOST"),
    port=os.getenv("DB_DESTINO_PORT")
)

cur_origem = origem.cursor()
cur_destino = destino.cursor()

map_plano = {"GRÁTIS": 1, "MENSAL": 2, "ANUAL": 3}

# =========================
# FUNÇÃO DE LOG
# =========================
def log_insert(tabela, dados):
    cur_destino.execute("""
        INSERT INTO Log (schema, Tabela, Operacao, Autor, Usuario, Dados_novoa)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, ("migração_rpa", tabela, "INSERT", "rpa_script", None, json.dumps(dados)))

# =========================
# INSERE SE NÃO EXISTE
# =========================
def inserir_unico(query_check, params_check, query_insert, params_insert, tabela, dados_log):
    cur_destino.execute(query_check, params_check)
    existe = cur_destino.fetchone()
    if not existe:
        cur_destino.execute(query_insert, params_insert)
        log_insert(tabela, dados_log)
        return True
    else:
        print(f"Registro duplicado ignorado em '{tabela}': {params_check}")
        return False

# =========================
# GARANTE PLANOS EXISTENTES
# =========================
cur_destino.execute("SELECT id FROM Planos;")
planos_existentes = {row[0] for row in cur_destino.fetchall()}

planos_para_inserir = [
    (1, 'GRÁTIS', 0.00, 0.00, 'Acesso básico gratuito'),
    (2, 'MENSAL', 49.90, 499.00, 'Assinatura mensal com recursos premium'),
    (3, 'ANUAL', 499.00, 499.00, 'Plano anual com desconto e vantagens exclusivas')
]

for plano in planos_para_inserir:
    if plano[0] not in planos_existentes:
        cur_destino.execute("""
            INSERT INTO Planos (ID, Nome, Preco_Mensal, Preco_Anual, Recursos)
            VALUES (%s, %s, %s, %s, %s);
        """, plano)
        log_insert("Planos", {
            "ID": plano[0],
            "Nome": plano[1],
            "Preco_Mensal": plano[2],
            "Preco_Anual": plano[3],
            "Recursos": plano[4]
        })

# =========================
# MIGRA EMPRESAS
# =========================
cur_origem.execute("""
    SELECT id, cnpj, nome, email_corporativo, telefone, ramo_atuacao, tipo_assinatura
    FROM empresa;
""")

for emp in cur_origem.fetchall():
    id_emp, cnpj, nome, email, telefone, ramo, tipo = emp
    id_plano = map_plano.get((tipo or "GRÁTIS").upper(), 1)

    dados_emp = {
        "CNPJ": cnpj.strip(),
        "Nome": nome,
        "Email": email,
        "Senha": "senha_padrao",
        "Senha_Area_Restrita": "senha_restrita",
        "Codigo": f"EMP{id_emp:04}",
        "Ramo_Atuacao": ramo or "Não informado",
        "Telefone": telefone,
        "ID_Plano": id_plano
    }

    inserir_unico(
        "SELECT 1 FROM Empresa WHERE CNPJ = %s;",
        (dados_emp["CNPJ"],),
        """
        INSERT INTO Empresa (CNPJ, Nome, Email, Senha, Senha_Area_Restrita, Codigo, Ramo_Atuacao, Telefone, ID_Plano)
        VALUES (%(CNPJ)s, %(Nome)s, %(Email)s, %(Senha)s, %(Senha_Area_Restrita)s, %(Codigo)s, %(Ramo_Atuacao)s, %(Telefone)s, %(ID_Plano)s);
        """,
        dados_emp,
        "Empresa",
        dados_emp
    )

# =========================
# MIGRA ADMINISTRADORES
# =========================
cur_origem.execute("""
    SELECT cpf, nome, email_admin
    FROM administrador;
""")

for adm in cur_origem.fetchall():
    cpf, nome, email = adm

    if not cpf or str(cpf).strip().lower() in ["none", "null", ""]:
        print(f"Admin ignorado: CPF ausente ou inválido → Nome: {nome}")
        continue

    dados_user = {
        "Nome": nome or "Sem nome",
        "Senha": "senha_padrao",
        "Ativo": True
    }

    inserir_unico(
        "SELECT 1 FROM Usuarios WHERE nome = %s;",
        (dados_user["Nome"],),
        """
        INSERT INTO Usuarios (nome, senha, ativo)
        VALUES (%(Nome)s, %(Senha)s, %(Ativo)s);
        """,
        dados_user,
        "Usuarios",
        dados_user
    )

# =========================
# MIGRA OPERÁRIOS 
# =========================
cur_origem.execute("""
    SELECT cpf, nome, email_operario, cargo_operario, horario_trabalho, id_empresa
    FROM operario;
""")

for op in cur_origem.fetchall():
    cpf, nome, email, cargo, horario, id_emp = op

    if not cpf or str(cpf).strip().lower() in ["none", "null", ""]:
        print(f"Operário ignorado: CPF ausente ou inválido → Nome: {nome}")
        continue

    try:
        horas_previstas = int(str(horario).split(":")[0])
    except Exception:
        horas_previstas = 8

    # Inserir em Operario
    dados_op = {
        "CPF": str(cpf).strip(),
        "Nome": nome or "Sem nome",
        "Email": email or f"{cpf}@sememail.com",
        "Senha": "senha_padrao",
        "Cargo": cargo or "Não informado",
        "Setor": "Operacional",
        "Ferias": False,
        "Ativo": True,
        "Horas_Previstas": horas_previstas,
        "ID_Empresa": id_emp or 1
    }

    inserir_unico(
        "SELECT 1 FROM Operario WHERE CPF = %s;",
        (dados_op["CPF"],),
        """
        INSERT INTO Operario (CPF, Nome, Email, Senha, Cargo, Setor, Ferias, Ativo, Horas_Previstas, ID_Empresa)
        VALUES (%(CPF)s, %(Nome)s, %(Email)s, %(Senha)s, %(Cargo)s, %(Setor)s, %(Ferias)s, %(Ativo)s, %(Horas_Previstas)s, %(ID_Empresa)s);
        """,
        dados_op,
        "Operario",
        dados_op
    )

    # Inserir em Usuarios
    dados_user = {
        "Nome": nome or "Sem nome",
        "Senha": "senha_padrao",
        "Ativo": True
    }

    inserir_unico(
        "SELECT 1 FROM Usuarios WHERE nome = %s;",
        (dados_user["Nome"],),
        """
        INSERT INTO Usuarios (nome, senha, ativo)
        VALUES (%(Nome)s, %(Senha)s, %(Ativo)s);
        """,
        dados_user,
        "Usuarios",
        dados_user
    )


# =========================
# FINALIZA
# =========================
destino.commit()
cur_origem.close()
cur_destino.close()
origem.close()
destino.close()

print("Migração concluída")
