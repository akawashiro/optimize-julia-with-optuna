import os

import git
import optuna
import subprocess

JULIA_URL = "git@github.com:akawashiro/julia.git"
JULIA_PATH = "julia"
JULIA_BRANCH = "optuna-optimization"

if not os.path.exists(JULIA_PATH):
    git.Repo.clone_from(JULIA_URL, JULIA_PATH)
repo = git.Repo(JULIA_PATH)
repo.git.checkout(JULIA_BRANCH)


def get_tracked_files(trees):
    paths = []
    for tree in trees:
        for blob in tree.blobs:
            paths.append(blob.abspath)
        if tree.trees:
            paths.extend(get_tracked_files(tree.trees))
    return paths


def objective(trial):
    # Revert all changes with Optuna
    repo.git.reset("--hard")

    parameters = {
        "OPTUNA_OPTIMIZATION_INLINE_COST_THRESHOLD": str(
            trial.suggest_int("inline_cost_threshold", 50, 200)
        ),
        "OPTUNA_OPTIMIZATION_INLINE_NONLEAF_PENALTY": str(
            trial.suggest_int("inline_nonleaf_penalty", 500, 2000)
        ),
        "OPTUNA_OPTIMIZATION_INLINE_TUPLERET_BONUS": str(
            trial.suggest_int("inline_tupleret_bonus", 125, 500)
        ),
        "OPTUNA_OPTIMIZATION_INLINE_ERROR_PATH_COST": str(
            trial.suggest_int("inline_error_path_cost", 10, 40)
        ),
    }

    for filename in get_tracked_files([repo.tree()]):
        if not filename.endswith(".jl"):
            continue
        with open(filename, "rt") as f:
            data = f.read()
        for k, v in parameters.items():
            data = data.replace(k, v)

        with open(filename, "wt") as f:
            f.write(data)

    subprocess.run(["make", "-j", f"{os.cpu_count() - 2}"], cwd=JULIA_PATH)
    # TODO: Run benchmark.sh
    # TODO: Return the result of benchmark
    return 100


study = optuna.create_study()
study.optimize(objective, n_trials=2)
