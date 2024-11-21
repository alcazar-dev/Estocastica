# Todo jsjsj

import tkinter as tk
from tkinter import ttk, messagebox
import pyomo.environ as pyo
from ortools.sat.python import cp_model


# ------------------- Funciones del Modelo -------------------
def solve_newsvendor(demanda_promedio, desviacion, costo_faltante, costo_exceso):
    model = pyo.ConcreteModel()
    model.q = pyo.Var(domain=pyo.NonNegativeReals)  # Cantidad a pedir

    def costo_total(model):
        return (
            costo_faltante * (demanda_promedio - model.q) ** 2 +
            costo_exceso * (model.q - demanda_promedio) ** 2
        )
    model.obj = pyo.Objective(rule=costo_total, sense=pyo.minimize)

    solver = pyo.SolverFactory('glpk')
    result = solver.solve(model)
    return model.q.value

def solve_clsp(demanda, capacidad, costos_produccion, costos_setup, horizonte):
    model = pyo.ConcreteModel()
    model.t = range(horizonte)
    model.x = pyo.Var(model.t, domain=pyo.NonNegativeIntegers)  # Cantidad producida en cada periodo
    model.y = pyo.Var(model.t, domain=pyo.Binary)  # Si se produce o no en el periodo

    def costo_total(model):
        return sum(costos_produccion * model.x[t] + costos_setup * model.y[t] for t in model.t)
    model.obj = pyo.Objective(rule=costo_total, sense=pyo.minimize)

    def demanda_cubierta(model, t):
        return model.x[t] >= demanda[t]
    model.demanda_cubierta = pyo.Constraint(model.t, rule=demanda_cubierta)

    def capacidad_maxima(model, t):
        return model.x[t] <= capacidad * model.y[t]
    model.capacidad_maxima = pyo.Constraint(model.t, rule=capacidad_maxima)

    solver = pyo.SolverFactory('glpk')
    result = solver.solve(model)
    return {t: model.x[t].value for t in model.t}

def solve_jssp(tiempos_maquina, secuencia_tareas):
    model = cp_model.CpModel()
    num_maquinas = len(tiempos_maquina)
    num_tareas = len(secuencia_tareas)
    inicio = {}

    for tarea in range(num_tareas):
        for maquina in range(num_maquinas):
            inicio[(tarea, maquina)] = model.NewIntVar(0, sum(map(sum, tiempos_maquina)), f'inicio_{tarea}_{maquina}')

    for tarea, secuencia in enumerate(secuencia_tareas):
        for i in range(len(secuencia) - 1):
            model.Add(inicio[(tarea, secuencia[i])] + tiempos_maquina[secuencia[i]][tarea] <= inicio[(tarea, secuencia[i + 1])])

    makespan = model.NewIntVar(0, sum(map(sum, tiempos_maquina)), 'makespan')
    for maquina in range(num_maquinas):
        for tarea in range(num_tareas):
            model.Add(inicio[(tarea, maquina)] + tiempos_maquina[maquina][tarea] <= makespan)
    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status == cp_model.OPTIMAL:
        return {f'Tarea_{tarea}': {f'Maquina_{maquina}': solver.Value(inicio[(tarea, maquina)]) for maquina in range(num_maquinas)} for tarea in range(num_tareas)}
    else:
        return "No se encontró solución óptima"


# ------------------- Interfaz Gráfica -------------------
def ejecutar_modelos():
    try:
        # Parámetros de Newsvendor
        demanda_promedio = float(entry_demanda.get())
        desviacion = float(entry_desviacion.get())
        costo_faltante = float(entry_costo_faltante.get())
        costo_exceso = float(entry_costo_exceso.get())
        nivel_optimo = solve_newsvendor(demanda_promedio, desviacion, costo_faltante, costo_exceso)

        # Parámetros de CLSP
        demanda = list(map(int, entry_demanda_clsp.get().split(',')))
        capacidad = int(entry_capacidad.get())
        costos_produccion = float(entry_costos_produccion.get())
        costos_setup = float(entry_costos_setup.get())
        horizonte = len(demanda)
        plan_produccion = solve_clsp(demanda, capacidad, costos_produccion, costos_setup, horizonte)

        # Parámetros de JSSP
        tiempos_maquina = eval(entry_tiempos_maquina.get())  # Ejemplo: [[3, 2], [1, 4]]
        secuencia_tareas = eval(entry_secuencia_tareas.get())  # Ejemplo: [[0, 1], [1, 0]]
        resultado_jssp = solve_jssp(tiempos_maquina, secuencia_tareas)

        # Mostrar resultados
        resultados_texto = (
            f"Newsvendor:\nNivel óptimo: {nivel_optimo:.2f}\n\n"
            f"CLSP:\nPlan de producción: {plan_produccion}\n\n"
            f"JSSP:\nResultado: {resultado_jssp}"
        )
        messagebox.showinfo("Resultados", resultados_texto)

    except Exception as e:
        messagebox.showerror("Error", str(e))


# Configuración de la ventana principal
root = tk.Tk()
root.title("Optimización de Producción")

# Parámetros de Newsvendor
ttk.Label(root, text="Demanda Promedio:").grid(row=0, column=0, sticky="w")
entry_demanda = ttk.Entry(root)
entry_demanda.grid(row=0, column=1)

ttk.Label(root, text="Desviación:").grid(row=1, column=0, sticky="w")
entry_desviacion = ttk.Entry(root)
entry_desviacion.grid(row=1, column=1)

ttk.Label(root, text="Costo Faltante:").grid(row=2, column=0, sticky="w")
entry_costo_faltante = ttk.Entry(root)
entry_costo_faltante.grid(row=2, column=1)

ttk.Label(root, text="Costo Exceso:").grid(row=3, column=0, sticky="w")
entry_costo_exceso = ttk.Entry(root)
entry_costo_exceso.grid(row=3, column=1)

# Parámetros de CLSP
ttk.Label(root, text="Demanda CLSP (separada por comas):").grid(row=4, column=0, sticky="w")
entry_demanda_clsp = ttk.Entry(root)
entry_demanda_clsp.grid(row=4, column=1)

ttk.Label(root, text="Capacidad:").grid(row=5, column=0, sticky="w")
entry_capacidad = ttk.Entry(root)
entry_capacidad.grid(row=5, column=1)

ttk.Label(root, text="Costos Producción:").grid(row=6, column=0, sticky="w")
entry_costos_produccion = ttk.Entry(root)
entry_costos_produccion.grid(row=6, column=1)

ttk.Label(root, text="Costos Setup:").grid(row=7, column=0, sticky="w")
entry_costos_setup = ttk.Entry(root)
entry_costos_setup.grid(row=7, column=1)

# Parámetros de JSSP
ttk.Label(root, text="Tiempos Máquina (ej: [[3,2],[1,4]]):").grid(row=8, column=0, sticky="w")
entry_tiempos_maquina = ttk.Entry(root)
entry_tiempos_maquina.grid(row=8, column=1)

ttk.Label(root, text="Secuencia Tareas (ej: [[0,1],[1,0]]):").grid(row=9, column=0, sticky="w")
entry_secuencia_tareas = ttk.Entry(root)
entry_secuencia_tareas.grid(row=9, column=1)

# Botón para ejecutar los modelos
btn_ejecutar = ttk.Button(root, text="Ejecutar Modelos", command=ejecutar_modelos)
btn_ejecutar.grid(row=10, column=0, columnspan=2)

# Iniciar la aplicación
root.mainloop()
