'''

MSE 331 Final Project Solver

Name                        Student Number
Shawn Hu                    20881488
Taksh Parmar                20872903
Rahavan Sivaguganantha      20945290
Ethan Wong                  20894768

Requirements:
Python version 3.11.2 or greater
Latest version of gurobipy

'''


import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np

def str_to_int(in_str):
    int_sum = 0
    for i in in_str:
        int_sum += ord(i)
    return int_sum

if __name__ == "__main__":
    # load excel
    df = pd.read_csv("nba_2022-23_all_stats_with_salary.csv")

    skill_coef = {"PG": [1, 1.5, 1, 2, 0.5],
                  "SG": [1.2, 0.8, 1, 1.5, 0.5],
                  "SF": [1, 1, 1, 1, 1],
                  "PF": [0.8, 1.5, 0.5, 0.5, 2],
                  "C": [0.7, 2, 0.5, 0.3, 2.5]}
    
    # check for skill column
    col_names = list(df.columns)
    if "SKILL" not in col_names:
        df["SKILL"] = [0.0]*len(df)
        col_names = list(df.columns)

        # some players can fill 2 positions so we will arbitrate and only take the first position
        for i in range(len(df)):
            if df.at[i, "Position"] in ["SF-PF", "SG-PG", "SF-SG", "PG-SG"]:
                positions = df.at[i, "Position"].split("-")
                df.at[i, "Position"] = positions[0]
    
        # process player skills
        for i in range(len(df)):
            coef_arr = skill_coef[df.at[i, "Position"]]
            df.at[i, "SKILL"] = coef_arr[0] * df.at[i, "PTS"] + coef_arr[1] * df.at[i, "AST"] + coef_arr[2] * (df.at[i, "ORB"] + df.at[i, "DRB"]) + coef_arr[3] * df.at[i, "STL"] + coef_arr[4] * df.at[i, "BLK"]
    
        df.to_csv("nba_2022-23_all_stats_with_salary.csv")

    # begin constructing model
    model = gp.Model()
    
    # define and record all binary decision variables
    decision_variables = []
    for i in range(len(df)):
        decision_variables.append(model.addVar(vtype=GRB.BINARY, name=df.at[i, "Player Name"]))

    # define coaches and trainers/equipment costs
    coach_cost = model.addVar(lb=0, name="Coaches Cost")
    te_cost = model.addVar(lb=0, name="TE Cost")

    # construct objective function
    lin = gp.LinExpr()
    for i in range(len(df)):
        lin.addTerms(df.at[i, "SKILL"], decision_variables[i])
    lin.addTerms(1.5/3000000, coach_cost)
    lin.addTerms(1.2/4000000, te_cost)
    model.setObjective(lin, GRB.MAXIMIZE)

    # construct binary vars for constraints
    old_bin = []
    player_age = []
    for i in range(len(df)):
        old_bin.append(model.addVar(vtype=GRB.BINARY, name=df.at[i, "Player Name"] + " is old"))
        player_age.append(model.addVar(lb=int(df.at[i, "Age"]), ub=int(df.at[i, "Age"]), name=df.at[i, "Player Name"] + " age"))
        model.addConstr((old_bin[i] == 1) >> (player_age[i] >= 33))
        model.addConstr((old_bin[i] == 0) >> (player_age[i] <= 33-np.finfo(float).eps))

    young_bin = []
    for i in range(len(df)):
        young_bin.append(model.addVar(vtype=GRB.BINARY, name=df.at[i, "Player Name"] + " is young"))
        model.addConstr((young_bin[i] == 1) >> (player_age[i] <= 25))
        model.addConstr((young_bin[i] == 0) >> (player_age[i] >= 25+np.finfo(float).eps))

    pg_bin = []
    player_pos = []
    for i in range(len(df)):
        pg_bin.append(model.addVar(vtype=GRB.BINARY, name=df.at[i, "Player Name"] + " is a PG"))
        player_pos.append(model.addVar(lb=str_to_int(df.at[i, "Position"]), ub=str_to_int(df.at[i, "Position"]), name=df.at[i, "Player Name"] + " pos"))
        model.addConstr((pg_bin[i] == 1) >> (player_pos[i] == str_to_int("PG")))
        # model.addConstr((pg_bin[i] == 0) >> (player_pos[i] != str_to_int("PG")))

    sg_bin = []
    for i in range(len(df)):
        sg_bin.append(model.addVar(vtype=GRB.BINARY, name=df.at[i, "Player Name"] + " is a SG"))
        model.addConstr((sg_bin[i] == 1) >> (player_pos[i] == str_to_int("SG")))
        # model.addConstr((sg_bin[i] == 0) >> (player_pos[i] != str_to_int("SG")))

    sf_bin = []
    for i in range(len(df)):
        sf_bin.append(model.addVar(vtype=GRB.BINARY, name=df.at[i, "Player Name"] + " is a SF"))
        model.addConstr((sf_bin[i] == 1) >> (player_pos[i] == str_to_int("SF")))
        # model.addConstr((sf_bin[i] == 0) >> (player_pos[i] != str_to_int("SF")))

    pf_bin = []
    for i in range(len(df)):
        pf_bin.append(model.addVar(vtype=GRB.BINARY, name=df.at[i, "Player Name"] + " is a PF"))
        model.addConstr((pf_bin[i] == 1) >> (player_pos[i] == str_to_int("PF")))
        # model.addConstr((pf_bin[i] == 0) >> (player_pos[i] != str_to_int("PF")))

    c_bin = []
    for i in range(len(df)):
        c_bin.append(model.addVar(vtype=GRB.BINARY, name=df.at[i, "Player Name"] + " is a C"))
        model.addConstr((c_bin[i] == 1) >> (player_pos[i] == str_to_int("C")))
        # model.addConstr((c_bin[i] == 0) >> (player_pos[i] != str_to_int("C")))

    # construct constraints
    budget_constr = gp.LinExpr()
    for i in range(len(decision_variables)):
        budget_constr.addTerms(df.at[i, "Salary"], decision_variables[i])
    budget_constr.addTerms(1, coach_cost)
    budget_constr.addTerms(1, te_cost)
    model.addLConstr(budget_constr, GRB.LESS_EQUAL, 140588000)

    player_constr = gp.LinExpr()
    for i in range(len(decision_variables)):
        player_constr.addTerms(1, decision_variables[i])
    player_constr.addConstant(-12)
    model.addLConstr(player_constr, GRB.LESS_EQUAL, 3)

    seniority_constr = gp.QuadExpr()
    for i in range(len(decision_variables)):
        seniority_constr.add(decision_variables[i] * young_bin[i], 1)
        seniority_constr.add(decision_variables[i] * old_bin[i], -3)
    model.addQConstr(seniority_constr, GRB.LESS_EQUAL, 0)

    pg_constr = gp.QuadExpr()
    for i in range(len(decision_variables)):
        pg_constr.add(decision_variables[i] * pg_bin[i], 1)
    model.addQConstr(pg_constr, GRB.GREATER_EQUAL, 2)

    sg_constr = gp.QuadExpr()
    for i in range(len(decision_variables)):
        sg_constr.add(decision_variables[i] * sg_bin[i], 1)
    model.addQConstr(sg_constr, GRB.GREATER_EQUAL, 2)

    pf_constr = gp.QuadExpr()
    for i in range(len(decision_variables)):
        pf_constr.add(decision_variables[i] * pf_bin[i], 1)
    model.addQConstr(pf_constr, GRB.GREATER_EQUAL, 2)

    sf_constr = gp.QuadExpr()
    for i in range(len(decision_variables)):
        sf_constr.add(decision_variables[i] * sf_bin[i], 1)
    model.addQConstr(sf_constr, GRB.GREATER_EQUAL, 2)

    c_constr = gp.QuadExpr()
    for i in range(len(decision_variables)):
        c_constr.add(decision_variables[i] * c_bin[i], 1)
    model.addQConstr(c_constr, GRB.GREATER_EQUAL, 2)
    
    model.optimize()

    # Display results
    if model.status == GRB.OPTIMAL:
        print("\nOptimal Solution:")
        for v in decision_variables:
            if v.x == 1:
                print(f"{v.varName} = {v.x}")

        print(f"{coach_cost} = {coach_cost.x}")
        print(f"{te_cost} = {te_cost.x}")

        print(f"Optimal Objective Value = {model.objVal}")