from langchain.llms import OpenAI
from langchain.sql_database import SQLDatabase
from langchain_experimental.sql.base import SQLDatabaseChain
from sqlalchemy import create_engine
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
import pyodbc

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
    st.header('Natural Language to MS-SQL Queries')
    #connecting to server
    driver = os.getenv('Driver')
    server = os.getenv('Server')
    db_name = os.getenv('db_name')
    db = pyodbc.connect(f"DRIVER={driver};SERVER={server};DATABASE={db_name};trusted_connection=yes")      
    cursor=db.cursor()

    # table and column selection for SQL querying 
    table_cmd = cursor.execute("SELECT concat (Table_schema,'.',Table_name) FROM information_schema.tables")
    table_names = retrieve_names(table_cmd)
    selected_table = st.selectbox("Select a Table",options=table_names,placeholder='Choose your option')

    column_cmd = cursor.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{selected_table.split('.')[1]}'")
    column_names = pd.DataFrame(retrieve_names(column_cmd),columns=['Table Columns'])
    st.dataframe(column_names, hide_index=True, width=300)
    query = None
    query = st.text_input("Enter your Query!")

    if st.button("Submit") and query:
        connection = f"mssql+pyodbc:///?odbc_connect=DRIVER={driver};SERVER={server};DATABASE={db_name};trusted_connection=yes"
        engine = create_engine(connection)       
        db = SQLDatabase(engine) 
        llm = OpenAI(model_name='gpt-3.5-turbo')
        db_chain = SQLDatabaseChain(llm=llm, database=db, verbose=True)     
        prompt = f"""Given an input question, first create a syntactically correct MS SQL query to run, then look at the results of the query and return the answer.  
                    The question: {query}
                    The Query should take into account only the table:{selected_table} and use all columns for computing.
                    You must recheck the query that is produced before executing it.
                    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) and prompt out we cannot edit the database, if user asks the same.
                    If the question does not seem related to the table, prompt out 'Please stick to the selected table.'
                    """
        answer = db_chain.run(prompt)
        st.write(answer)
if __name__ == "__main__":
    main()
    