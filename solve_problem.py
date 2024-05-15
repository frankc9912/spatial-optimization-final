import cplex
import os
import csv


def parse_filename(filename):
    parts = filename.replace(".txt", "").split("_")
    alpha, bmax = parts
    return float(alpha), float(bmax)


def solve_lp_problem(filepath):
    cpx = cplex.Cplex(filepath)
    start_time = cplex.Cplex().get_time()
    cpx.solve()
    end_time = cplex.Cplex().get_time()
    running_time = end_time-start_time
    binary_vars = {}
    for i in cpx.variables.get_names():
        binary_vars[i] = cpx.solution.get_values(i)
    return running_time, binary_vars


problem_files_path = "C:/Users/MaJia/Documents/Spatial Op/Final/problems10"
problem_files = os.listdir(problem_files_path)

running_times = {}
binary_variables = {}

for filename in problem_files:
    alpha, bmax = parse_filename(filename)
    filepath = os.path.join(problem_files_path, filename)
    try:
        running_time, binary_vars = solve_lp_problem(filepath)
    except cplex.exceptions.errors.CplexSolverError as e:
        print(f"Solver error for file {filename}: {e}")
        continue

    if alpha not in running_times:
        running_times[alpha] = {}
    running_times[alpha][bmax] = running_time

    binary_variables[f"{alpha}_{bmax}"] = binary_vars

with open('running_times10.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    bmax_values = sorted(set(b for a in running_times for b in running_times[a]))
    writer.writerow(["alpha"] + bmax_values)
    for alpha in sorted(running_times):
        writer.writerow([alpha] + [running_times[alpha].get(bmax, "") for bmax in bmax_values])

with open('binary_variables10.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    headers = ["alpha_bmax"] + [f"X{i}" for i in range(1, 471)]
    writer.writerow(headers)
    for alpha in sorted(running_times):
        for bmax in sorted(running_times[alpha]):
            row = [f"{alpha}_{bmax}"]
            print(binary_variables[f"{alpha}_{bmax}"])
            row.extend(binary_variables[f"{alpha}_{bmax}"].values())
            writer.writerow(row)