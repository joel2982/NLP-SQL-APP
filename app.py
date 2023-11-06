from langchain import OpenAI
from langchain.chains.sql_database.query import create_sql_query_chain
# import sqlalchemy
import streamlit as st
import numpy as np
from dotenv import load_dotenv
import openai
import os
import pyodbc

def sql_chain(db):
    query = st.text_input('Enter your Query.')
    llm = OpenAI(model_name='gpt-3.5-turbo')
    prompt = """Given an input question, first create a syntactically correct MS SQL query to run, then look at the results of the query and return the answer.  
                The question: {query}
                You must recheck the query that is produced before executing it.
                DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database and prompt out we cannot edit the database, if user asks the same.
                If the question does not seem related to the database, prompt out 'Please stick to the selected database/table.'
                """
    sql_query = create_sql_query_chain(llm=llm, database=db, prompt=prompt, top_k=3)
    # output = db_chain.run(prompt.format(query=query))
    st.write(sql_query)

def retrieve_names(cmd):
    string = list(str(cmd.fetchall()))
    names=[]
    val = ''
    for i in string:
        if i in ',':
            if len(val)==0:
                continue
            names.append(val)
            val = ''
        elif i not in " ''[]()":
            val+=i
    names.sort()
    return names


def main():
    load_dotenv()
    driver = os.getenv('Driver')
    server = os.getenv('Server')
    db_name = os.getenv('db_name')

    # username = os.getenv('username')
    # password = os.getenv('password')
    # server = os.getenv('server')
    # db_name = os.getenv('db_name')
    st.header('Natural Language to MS-SQL Queries')
    # # connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={db_name};UID={username};PWD={password}'
    # connectionString = 'DRIVER=ODBC Driver 18 for SQL Server;SERVER=DESKTOP-E20ERU;DATABASE=AdventureWorks2022;UID=Joel John;PWD=pass1231'
    # connection = pyodbc.connect(connectionString) 

    # connection_string=f'''
    #     DRIVER={{{driver}}};
    #     SERVER={server};
    #     DATABASE={db_name};
    #     trusted_connection=yes'''

    db = pyodbc.connect(f"DRIVER={driver};SERVER={server};DATABASE={db_name};trusted_connection=yes")      
    cursor=db.cursor()

    table_cmd = cursor.execute("SELECT concat (Table_schema,'.',Table_name) FROM information_schema.tables")
    table_names = retrieve_names(table_cmd)
    selected_table = st.selectbox("Select a Table",options = table_names)
    if selected_table:
        column_cmd = cursor.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{selected_table.split('.')[1]}'")
        column_names = retrieve_names(column_cmd)
        selected_columns = st.multiselect("Select the Columns",options = column_names)
        st.write(selected_columns)

    # engine = sqlalchemy.create_engine(f"mssql+pymssql://{username}:{password}@{server}.database.windows.net:1433/{db_name}", pool_recycle=3600)
    # connection = pyodbc.connect(f"Driver={{{driver_name}}};Server={server_name};Database={db_name};Trusted_Connection=yes;")
    # db = SQLDatabase.from_uri(f"mssql+pyodbc://{username}:{password}@{host}\SQLEXPRESS/DociQDb?driver=SQL+Server")
    # db = SQLDatabase(engine)
# DESKTOP-E20ERUT	AdventureWorks2022	1	53000002968800001	53000002971200001	53000002968800001	53000002467200001	23-05-2023 11:56:14	23-05-2023 11:56:15	209805312	DESKTOP-E20ERUT\rw	
if __name__ == "__main__":
    main()
    