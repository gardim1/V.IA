import pyodbc
from dotenv import load_dotenv

load_dotenv()

def conectar():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=TMS_LIA;"
        "Trusted_Connection=yes;"
        # "SERVER=IP_OU_NOME_DO_SERVIDOR;"
        # "UID=SEU_USUARIO;"
        # "PWD=SUA_SENHA;"
        #usar env 
        #F"SERVER={os.getenv('SERVER')};"
        )

def listar_tabelas_colunas():
    conn = conectar()
    query = """
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    """
    cursor = conn.cursor()
    cursor.execute(query)
    resultado = cursor.fetchall()
    conn.close()

    tabelas = {}
    for tabela, coluna in resultado:
        tabelas.setdefault(tabela, []).append(coluna)
    return tabelas

def gerar_contexto_tabelas(tabelas_dict):
    linhas = []
    for tabela, colunas in tabelas_dict.items():
        linhas.append(f"Tabela: '{tabela}' possui as colunas: {', '.join(colunas)}")
    return "\n".join(linhas)