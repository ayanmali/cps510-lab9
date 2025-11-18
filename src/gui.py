import tkinter as tk
from tkinter import messagebox, scrolledtext

import oracledb

from .db import q1, q2, q3, q4, q5, delete_all, create_tables, populate

def start_gui(conn: oracledb.Connection):
    root = tk.Tk()
    root.title("CPS510 Lab 9")
    root.geometry("1000x700")
    create_widgets(root, conn)
    root.protocol("WM_DELETE_WINDOW", on_close) # type: ignore
    root.mainloop()

def create_widgets(root, conn: oracledb.Connection):
    frame = tk.Frame(root)
    frame.pack(pady=10)
    # tk.Label(frame, text="Query 1").grid(row=0, column=0, padx=10, pady=10)
    # tk.Button(frame, text="Execute", command=lambda: execute_query(conn, 1)).grid(row=0, column=1, padx=10, pady=10) # type: ignore
    # tk.Label(frame, text="Query 2").grid(row=1, column=0, padx=10, pady=10)
    # tk.Button(frame, text="Execute", command=lambda: execute_query(conn, 2)).grid(row=1, column=1, padx=10, pady=10) # type: ignore
    # tk.Label(frame, text="Query 3").grid(row=2, column=0, padx=10, pady=10)
    # tk.Button(frame, text="Execute", command=lambda: execute_query(conn, 3)).grid(row=2, column=1, padx=10, pady=10) # type: ignore
    # tk.Label(frame, text="Query 4").grid(row=3, column=0, padx=10, pady=10)
    # tk.Button(frame, text="Execute", command=lambda: execute_query(conn, 4)).grid(row=3, column=1, padx=10, pady=10) # type: ignore # type: ignore          

    # tk.Label(frame, text="Query 5").grid(row=4, column=0, padx=10, pady=10)
    # tk.Button(frame, text="Execute", command=lambda: execute_query(conn, 5)).grid(row=4, column=1, padx=10, pady=10) # type: ignore # type: ignore      

    # # Separator
    # tk.Label(frame, text="─" * 30).grid(row=5, column=0, columnspan=2, pady=10)
    
    # Database management buttons
    tk.Label(frame, text="Database Management", font=("Arial", 10, "bold")).grid(row=6, column=0, columnspan=2, pady=5)
    
    tk.Label(frame, text="Drop All Tables").grid(row=7, column=0, padx=10, pady=10)
    tk.Button(frame, text="Drop All", command=lambda: handle_drop_all(conn), bg="#ffcccc").grid(row=7, column=1, padx=10, pady=10) # type: ignore
    
    tk.Label(frame, text="Create Tables").grid(row=8, column=0, padx=10, pady=10)
    tk.Button(frame, text="Create", command=lambda: handle_create_tables(conn), bg="#ccffcc").grid(row=8, column=1, padx=10, pady=10) # type: ignore
    
    tk.Label(frame, text="Populate Tables").grid(row=9, column=0, padx=10, pady=10)
    tk.Button(frame, text="Populate", command=lambda: handle_populate(conn), bg="#ccccff").grid(row=9, column=1, padx=10, pady=10) # type: ignore

    tk.Label(frame, text="Exit").grid(row=10, column=0, padx=10, pady=10)
    tk.Button(frame, text="Exit", command=lambda: on_close(root)).grid(row=10, column=1, padx=10, pady=10) # type: ignore # type: ignore
    
    # Custom Query Section
    query_frame = tk.LabelFrame(root, text="Custom SQL Query", padx=10, pady=10)
    query_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # SQL Input Section
    input_label = tk.Label(query_frame, text="Enter SQL Query:", font=("Arial", 10, "bold"))
    input_label.pack(anchor=tk.W, pady=(0, 5))
    
    sql_input = scrolledtext.ScrolledText(query_frame, height=8, width=80, wrap=tk.WORD, font=("Courier", 10))
    sql_input.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # Results Output Section (create before buttons so it can be referenced)
    results_label = tk.Label(query_frame, text="Query Results:", font=("Arial", 10, "bold"))
    results_label.pack(anchor=tk.W, pady=(10, 5))
    
    results_output = scrolledtext.ScrolledText(query_frame, height=12, width=80, wrap=tk.WORD, font=("Courier", 9), state=tk.DISABLED)
    results_output.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # Execute button (placed after results_output so it can reference it)
    execute_btn_frame = tk.Frame(query_frame)
    execute_btn_frame.pack(fill=tk.X)
    
    execute_btn = tk.Button(execute_btn_frame, text="Execute Query", command=lambda: handle_custom_query(conn, sql_input, results_output), bg="#4CAF50", fg="black", font=("Arial", 10, "bold"))
    execute_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    clear_btn = tk.Button(execute_btn_frame, text="Clear", command=lambda: clear_query(sql_input, results_output), bg="#f44336", fg="black")
    clear_btn.pack(side=tk.LEFT)   

def execute_query(conn: oracledb.Connection, query_number: int):
    if query_number == 1:
        results = q1(conn)
    elif query_number == 2:
        results = q2(conn)
    elif query_number == 3:
        results = q3(conn)
    elif query_number == 4:
        results = q4(conn)
    elif query_number == 5:
        results = q5(conn)
    print(results)

def handle_drop_all(conn: oracledb.Connection):
    """Handle dropping all tables with confirmation."""
    response = messagebox.askyesno(
        "Confirm Drop All Tables",
        "Are you sure you want to drop all tables? This action cannot be undone.",
        icon="warning"
    )
    if response:
        try:
            delete_all(conn)
            messagebox.showinfo("Success", "All tables dropped successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Error dropping tables:\n{str(e)}")

def handle_create_tables(conn: oracledb.Connection):
    """Handle creating all tables."""
    try:
        create_tables(conn)
        messagebox.showinfo("Success", "All tables created successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Error creating tables:\n{str(e)}")

def handle_populate(conn: oracledb.Connection):
    """Handle populating tables with sample data."""
    try:
        print("GUI - Populating database with sample data...")
        populate(conn)
        messagebox.showinfo("Success", "Tables populated with sample data successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Error populating tables:\n{str(e)}")

def handle_custom_query(conn: oracledb.Connection, sql_input: scrolledtext.ScrolledText, results_output: scrolledtext.ScrolledText):
    """Handle executing custom SQL query and displaying results."""
    # Get SQL query from input
    query = sql_input.get("1.0", tk.END).strip()
    
    if not query:
        messagebox.showwarning("Warning", "Please enter a SQL query.")
        return
    
    # Clear previous results
    results_output.config(state=tk.NORMAL)
    results_output.delete("1.0", tk.END)
    
    cursor = conn.cursor()
    try:
        # Execute the query
        cursor.execute(query)
        
        # Check if it's a SELECT query (has results)
        if cursor.description:
            # Fetch column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            # Display results
            if rows:
                # Display column headers
                header = " | ".join(str(col).ljust(15) for col in columns)
                results_output.insert(tk.END, header + "\n")
                results_output.insert(tk.END, "-" * len(header) + "\n")
                
                # Display rows
                for row in rows:
                    row_str = " | ".join(str(val).ljust(15) if val is not None else "NULL".ljust(15) for val in row)
                    results_output.insert(tk.END, row_str + "\n")
                
                # Display row count
                results_output.insert(tk.END, f"\n{len(rows)} row(s) returned.\n")
            else:
                results_output.insert(tk.END, "Query executed successfully. No rows returned.\n")
        else:
            # DML statement (INSERT, UPDATE, DELETE, etc.)
            rows_affected = cursor.rowcount
            conn.commit()
            results_output.insert(tk.END, "Query executed successfully.\n")
            results_output.insert(tk.END, f"Rows affected: {rows_affected}\n")
            
    except oracledb.Error as e:
        (error,) = e.args
        error_msg = f"Database Error: {error.message}\n"
        if error.code:
            error_msg += f"Error Code: {error.code}\n"
        results_output.insert(tk.END, error_msg)
        conn.rollback()
    except Exception as e:
        results_output.insert(tk.END, f"Error: {str(e)}\n")
        conn.rollback()
    finally:
        cursor.close()
        results_output.config(state=tk.DISABLED)

def clear_query(sql_input: scrolledtext.ScrolledText, results_output: scrolledtext.ScrolledText):
    """Clear both input and output text areas."""
    sql_input.delete("1.0", tk.END)
    results_output.config(state=tk.NORMAL)
    results_output.delete("1.0", tk.END)
    results_output.config(state=tk.DISABLED)

def on_close(root):
    root.destroy()  # type: ignore