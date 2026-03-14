"""
AI SQL Assistant Module
Natural language to SQL query conversion using Google Gemini AI
"""

import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from io import BytesIO
import google.generativeai as genai
import os


def generate_excel_bytes(df):
    """Generate Excel file bytes from DataFrame"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Query Results')
    return output.getvalue()


def get_table_schema(cursor, table_name):
    """Get table schema information"""
    cursor.execute(f"DESCRIBE `{table_name}`")
    columns = cursor.fetchall()
    
    schema_info = []
    for col in columns:
        schema_info.append(f"  - {col[0]} ({col[1]})")
    
    return "\n".join(schema_info)


def generate_sql_query_with_gemini(user_question, database_context, api_key):
    """
    Generate SQL query from natural language using Google Gemini AI
    """
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # List available models and find the best one
        try:
            available_models = genai.list_models()
            # Find a model that supports generateContent
            model_name = None
            for m in available_models:
                if 'generateContent' in m.supported_generation_methods:
                    model_name = m.name
                    break
            
            if not model_name:
                raise Exception("No suitable model found")
            
            model = genai.GenerativeModel(model_name)
        except:
            # Fallback to trying common model names
            model_names = ['gemini-pro', 'gemini-1.5-pro', 'gemini-1.5-flash']
            model = None
            for name in model_names:
                try:
                    model = genai.GenerativeModel(name)
                    break
                except:
                    continue
            
            if not model:
                raise Exception("Could not initialize Gemini model")
        
        # Build context for AI
        tables_info = "\n".join([f"- {table}" for table in database_context['tables']])
        
        # Build detailed schema information
        schema_details = []
        for table, columns in database_context['columns'].items():
            cols = ", ".join(columns)
            schema_details.append(f"Table: {table}\nColumns: {cols}")
        
        schema_info = "\n\n".join(schema_details)
        
        # Create prompt for Gemini
        prompt = f"""You are an expert MySQL SQL query generator. Convert the user's natural language question into a valid MySQL query.

Database: {database_context['database']}

Available Tables:
{tables_info}

Detailed Schema:
{schema_info}

User Question: {user_question}

IMPORTANT RULES:
1. Generate ONLY the SQL query, nothing else
2. Use backticks for table and column names: `table_name`, `column_name`
3. For SELECT queries, add LIMIT 100 unless user specifies otherwise
4. Use proper MySQL syntax
5. If searching text, use LIKE with wildcards: LIKE '%search%'
6. For counting, use COUNT(*) or COUNT(DISTINCT column)
7. For aggregations, use SUM(), AVG(), MAX(), MIN()
8. For grouping, use GROUP BY with ORDER BY
9. Return ONLY the SQL query without any explanation or markdown

SQL Query:"""
        
        # Generate response
        response = model.generate_content(prompt)
        sql_query = response.text.strip()
        
        # Clean up the response
        # Remove markdown code blocks if present
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        # Remove any leading/trailing quotes
        sql_query = sql_query.strip('"\'')
        
        # Generate explanation
        explanation_prompt = f"""Explain in one simple sentence what this SQL query does:

{sql_query}

Provide ONLY a brief explanation, no technical jargon."""
        
        explanation_response = model.generate_content(explanation_prompt)
        explanation = explanation_response.text.strip()
        
        return sql_query, explanation
    
    except Exception as e:
        # Fallback to simple pattern matching if AI fails
        return generate_sql_query_fallback(user_question, database_context), f"AI unavailable, using fallback: {str(e)}"


def generate_sql_query_fallback(user_question, database_context):
    """
    Fallback SQL generation using pattern matching
    """
    
    question_lower = user_question.lower()
    
    # Extract table name if mentioned
    tables = database_context.get('tables', [])
    mentioned_table = None
    for table in tables:
        if table.lower() in question_lower:
            mentioned_table = table
            break
    
    # If no table mentioned, use the first one
    if not mentioned_table and tables:
        mentioned_table = tables[0]
    
    # Simple pattern matching
    if 'count' in question_lower or 'how many' in question_lower:
        return f"SELECT COUNT(*) as total_count FROM `{mentioned_table}`"
    elif 'sum' in question_lower or 'total' in question_lower:
        columns = database_context.get('columns', {}).get(mentioned_table, [])
        amount_col = next((col for col in columns if 'amount' in col.lower()), columns[0] if columns else 'amount')
        return f"SELECT SUM(`{amount_col}`) as total_sum FROM `{mentioned_table}`"
    elif 'average' in question_lower or 'avg' in question_lower:
        columns = database_context.get('columns', {}).get(mentioned_table, [])
        amount_col = next((col for col in columns if 'amount' in col.lower()), columns[0] if columns else 'amount')
        return f"SELECT AVG(`{amount_col}`) as average_value FROM `{mentioned_table}`"
    else:
        return f"SELECT * FROM `{mentioned_table}` LIMIT 100"


def render_ai_sql_assistant_page():
    """Render the AI SQL Assistant page"""
    
    st.title("🤖 AI SQL Assistant (Powered by Google Gemini)")
    st.markdown("Ask questions in natural language and get SQL queries automatically using AI")
    
    st.markdown("---")
    
    # API Key Configuration
    st.subheader("� Step 1: Configure Gemini API")
    
    # Default API key (pre-configured)
    default_api_key = 'AIzaSyDEY2w6aoqC0yXr4M7cYCEj-5979YScfsI'
    
    # Check for API key in environment or session
    api_key = os.getenv('GEMINI_API_KEY', default_api_key)
    
    # Store in session if not already set
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = api_key
    
    # Show API status
    if st.session_state.gemini_api_key:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success("✅ Gemini API key configured and ready")
        with col2:
            if st.button("🔄 Change Key", use_container_width=True):
                st.session_state.show_api_input = True
        
        # Show input if user wants to change
        if st.session_state.get('show_api_input', False):
            new_api_key = st.text_input(
                "Enter new Google Gemini API Key:",
                type="password",
                help="Get your free API key from https://makersuite.google.com/app/apikey"
            )
            
            if st.button("💾 Save New Key", use_container_width=True):
                if new_api_key:
                    st.session_state.gemini_api_key = new_api_key
                    st.session_state.show_api_input = False
                    st.success("✅ API key updated!")
                    st.rerun()
    
    if not st.session_state.get('gemini_api_key'):
        api_key = st.text_input(
            "Enter your Google Gemini API Key:",
            type="password",
            help="Get your free API key from https://makersuite.google.com/app/apikey"
        )
        
        if api_key:
            st.session_state.gemini_api_key = api_key
        
        if not api_key:
            st.warning("⚠️ Please enter your Gemini API key to continue")
            
            with st.expander("🔑 How to get a Gemini API Key (Free)"):
                st.markdown("""
                ### Get Your Free Gemini API Key:
                
                1. Visit: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
                2. Sign in with your Google account
                3. Click "Create API Key"
                4. Copy the API key
                5. Paste it above
                
                **Note:** Gemini API has a generous free tier:
                - 60 requests per minute
                - Perfect for SQL query generation
                - No credit card required
                """)
            
            return
    
    # MySQL Connection Settings
    st.markdown("---")
    st.subheader("🔌 Step 2: Connect to Database")
    
    col1, col2 = st.columns(2)
    
    with col1:
        host = st.text_input("Host:", value="localhost", key="ai_mysql_host")
        database = st.text_input("Database:", value="fraud_analysis", key="ai_mysql_database")
        user = st.text_input("Username:", value="root", key="ai_mysql_user")
    
    with col2:
        port = st.number_input("Port:", value=3306, min_value=1, max_value=65535, key="ai_mysql_port")
        password = st.text_input("Password:", type="password", key="ai_mysql_password")
    
    # Connect button
    if st.button("🔗 Connect to Database", type="primary", use_container_width=True):
        try:
            connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            
            if connection.is_connected():
                st.session_state.ai_db_connection_params = {
                    'host': host,
                    'port': port,
                    'user': user,
                    'password': password,
                    'database': database
                }
                st.session_state.ai_db_connected = True
                connection.close()
                st.success("✅ Connected successfully!")
                st.rerun()
        except Error as e:
            st.error(f"❌ Connection failed: {str(e)}")
            st.session_state.ai_db_connected = False
    
    # Check if connected
    if not st.session_state.get('ai_db_connected', False):
        st.info("👆 Please connect to database to continue")
        
        # Show example questions
        with st.expander("💡 Example Questions You Can Ask"):
            st.markdown("""
            **Counting & Statistics:**
            - "How many records are in the table?"
            - "Count unique banks"
            - "What's the total amount?"
            - "Calculate average transaction value"
            
            **Viewing Data:**
            - "Show all records"
            - "Display the data"
            - "Get top 20 records"
            
            **Searching:**
            - "Find records with 'Bank of India'"
            - "Search for ACK number '12345'"
            - "Where amount is greater than 10000"
            
            **Grouping & Analysis:**
            - "Group by bank name"
            - "Show records per district"
            - "Count by state"
            
            **Sorting:**
            - "Top 10 highest amounts"
            - "Largest transactions"
            - "Most recent records"
            
            **Tips:**
            - Use quotes for search terms: "Bank of India"
            - Mention table name if you have multiple tables
            - Be specific about column names
            """)
        
        return
    
    # Get connection params
    conn_params = st.session_state.get('ai_db_connection_params', {})
    
    try:
        # Connect to database
        connection = mysql.connector.connect(**conn_params)
        cursor = connection.cursor()
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        if not tables:
            st.warning("⚠️ No tables found in database")
            cursor.close()
            connection.close()
            return
        
        # Get table schemas
        table_columns = {}
        for table in tables:
            cursor.execute(f"DESCRIBE `{table}`")
            columns = [col[0] for col in cursor.fetchall()]
            table_columns[table] = columns
        
        # Database context for AI
        database_context = {
            'tables': tables,
            'columns': table_columns,
            'database': database
        }
        
        # Display database info
        st.markdown("---")
        st.subheader("📊 Connected Database")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Database", database)
            st.metric("Tables", len(tables))
        
        with col2:
            # Show tables
            with st.expander("📋 Available Tables", expanded=False):
                for table in tables:
                    st.text(f"• {table} ({len(table_columns[table])} columns)")
        
        # AI Query Interface
        st.markdown("---")
        st.subheader("🤖 Step 3: Ask Your Question")
        
        st.info("💡 **Powered by Google Gemini AI** - Understands complex questions and generates accurate SQL queries")
        
        # Question input
        user_question = st.text_area(
            "What would you like to know?",
            placeholder="Example: Show me the top 10 banks by transaction amount",
            height=100,
            help="Ask in natural language - the AI will convert it to SQL"
        )
        
        # Quick question buttons
        st.markdown("**💡 Quick Questions:**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Count Records", use_container_width=True):
                user_question = "How many records are there?"
                st.session_state.quick_question = user_question
        
        with col2:
            if st.button("💰 Total Amount", use_container_width=True):
                user_question = "What is the total amount?"
                st.session_state.quick_question = user_question
        
        with col3:
            if st.button("🔝 Top 10", use_container_width=True):
                user_question = "Show me top 10 records"
                st.session_state.quick_question = user_question
        
        with col4:
            if st.button("📋 Show All", use_container_width=True):
                user_question = "Show all records"
                st.session_state.quick_question = user_question
        
        # Use quick question if set
        if st.session_state.get('quick_question'):
            user_question = st.session_state.quick_question
            st.session_state.quick_question = None
        
        # Generate query button
        if st.button("🚀 Generate & Execute Query", type="primary", use_container_width=True, disabled=not user_question):
            if user_question:
                with st.spinner("🤖 Gemini AI is analyzing your question and generating SQL..."):
                    # Generate SQL query using Gemini
                    api_key = st.session_state.get('gemini_api_key', '')
                    sql_query, explanation = generate_sql_query_with_gemini(user_question, database_context, api_key)
                    
                    st.session_state.generated_query = sql_query
                    st.session_state.query_explanation = explanation
                    st.session_state.user_question = user_question
        
        # Display generated query
        if st.session_state.get('generated_query'):
            st.markdown("---")
            st.subheader("📝 Generated SQL Query")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"**Understanding:** {st.session_state.query_explanation}")
            
            with col2:
                if st.button("🔄 Regenerate", use_container_width=True):
                    del st.session_state.generated_query
                    st.rerun()
            
            # Show query in code block
            st.code(st.session_state.generated_query, language="sql")
            
            # Edit query option
            with st.expander("✏️ Edit Query (Advanced)", expanded=False):
                edited_query = st.text_area(
                    "Modify the SQL query if needed:",
                    value=st.session_state.generated_query,
                    height=150,
                    key="edited_query"
                )
                
                if st.button("💾 Use Edited Query", use_container_width=True):
                    st.session_state.generated_query = edited_query
                    st.success("✅ Query updated")
                    st.rerun()
            
            # Execute query button
            if st.button("▶️ Execute Query", type="primary", use_container_width=True):
                try:
                    with st.spinner("Executing query..."):
                        cursor.execute(st.session_state.generated_query)
                        
                        # Check if it's a SELECT query
                        if st.session_state.generated_query.strip().upper().startswith('SELECT'):
                            rows = cursor.fetchall()
                            columns = [desc[0] for desc in cursor.description]
                            
                            if rows:
                                df = pd.DataFrame(rows, columns=columns)
                                st.session_state.query_result = df
                                st.success(f"✅ Query executed successfully! Retrieved {len(df):,} rows")
                            else:
                                st.warning("⚠️ Query executed but returned no results")
                                st.session_state.query_result = None
                        else:
                            # For non-SELECT queries
                            connection.commit()
                            st.success(f"✅ Query executed successfully! Rows affected: {cursor.rowcount}")
                            st.session_state.query_result = None
                
                except Exception as e:
                    st.error(f"❌ Error executing query: {str(e)}")
                    st.code(str(e))
        
        # Display results
        if st.session_state.get('query_result') is not None:
            df = st.session_state.query_result
            
            st.markdown("---")
            st.subheader("📊 Query Results")
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Rows", f"{len(df):,}")
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                # Calculate data size
                size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
                st.metric("Size", f"{size_mb:.2f} MB")
            
            # Display dataframe
            st.dataframe(df, use_container_width=True, height=400)
            
            # Download options
            st.markdown("---")
            st.subheader("📥 Download Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                excel_bytes = generate_excel_bytes(df)
                st.download_button(
                    label=f"📊 Download Excel ({len(df):,} rows)",
                    data=excel_bytes,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            
            with col2:
                csv_bytes = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📄 Download CSV ({len(df):,} rows)",
                    data=csv_bytes,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # Clear results
            if st.button("🔄 Clear Results & Ask New Question", use_container_width=True):
                if 'query_result' in st.session_state:
                    del st.session_state.query_result
                if 'generated_query' in st.session_state:
                    del st.session_state.generated_query
                st.rerun()
        
        # Query history
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        # Save to history
        if st.session_state.get('generated_query') and st.session_state.get('user_question'):
            history_entry = {
                'question': st.session_state.user_question,
                'query': st.session_state.generated_query,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add to history if not already there
            if not any(h['query'] == history_entry['query'] for h in st.session_state.query_history):
                st.session_state.query_history.insert(0, history_entry)
                # Keep only last 10
                st.session_state.query_history = st.session_state.query_history[:10]
        
        # Show history
        if st.session_state.query_history:
            st.markdown("---")
            with st.expander("📜 Query History (Last 10)", expanded=False):
                for idx, entry in enumerate(st.session_state.query_history, 1):
                    st.markdown(f"**{idx}. {entry['timestamp']}**")
                    st.text(f"Q: {entry['question']}")
                    st.code(entry['query'], language="sql")
                    
                    if st.button(f"🔄 Reuse Query #{idx}", key=f"reuse_{idx}"):
                        st.session_state.generated_query = entry['query']
                        st.session_state.query_explanation = "Reused from history"
                        st.rerun()
                    
                    st.markdown("---")
        
        # Close connection
        cursor.close()
        connection.close()
    
    except Error as e:
        st.error(f"❌ Database Error: {str(e)}")
        st.session_state.ai_db_connected = False
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    # Instructions
    st.markdown("---")
    with st.expander("ℹ️ How It Works"):
        st.markdown("""
        ### AI SQL Assistant Features:
        
        **Powered by Google Gemini AI:**
        - Advanced natural language understanding
        - Generates accurate SQL queries
        - Handles complex questions
        - Understands context and intent
        
        **Natural Language Processing:**
        - Ask questions in plain English
        - AI converts to SQL automatically
        - No SQL knowledge required
        - Supports complex queries
        
        **Supported Query Types:**
        - **Counting**: "How many records?", "Count unique values"
        - **Aggregation**: "Total amount", "Average value", "Sum of..."
        - **Viewing**: "Show all", "Display data", "Get records"
        - **Searching**: "Find records with...", "Search for..."
        - **Grouping**: "Group by bank", "Per district"
        - **Sorting**: "Top 10", "Highest amounts", "Most recent"
        
        **Features:**
        - Auto-generates SQL from questions
        - Shows explanation of what query does
        - Edit queries before execution
        - View results in table format
        - Download as Excel or CSV
        - Query history (last 10 queries)
        - Quick question buttons
        
        **Tips for Better Results:**
        - Be specific: "top 10 banks by amount" vs "show banks"
        - Use quotes for search: Find "Bank of India"
        - Mention column names if known
        - Mention table name if multiple tables
        - Use numbers: "top 20", "last 50"
        
        **Examples:**
        - "Show me all records from layerwise_data"
        - "Count how many unique banks are there"
        - "What is the total disputed amount?"
        - "Find all records where amount is greater than 100000"
        - "Group transactions by district and count them"
        - "Show top 15 highest transaction amounts"
        - "Get the most recent 50 records"
        
        **Advanced:**
        - Edit generated queries for fine-tuning
        - Reuse queries from history
        - Execute any valid SQL query
        """)
    
    # Footer
    st.markdown("---")
    st.caption("🤖 AI SQL Assistant | Ask questions in natural language, get SQL queries automatically")
