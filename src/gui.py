import tkinter as tk
from tkinter import messagebox

import oracledb

from .db import q1, q2, q3, q4, q5, delete_all, create_tables, populate

def start_gui(conn: oracledb.Connection):
    root = tk.Tk()
    root.title("CPS510 Lab 9")
    root.geometry("800x600")
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

def on_close(root):
    root.destroy()  # type: ignore