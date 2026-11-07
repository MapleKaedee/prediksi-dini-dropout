{
  pkgs,
  python,
  treefmt,
  hooks,
  ...
}:
{
  devshell = {
    name = "dropout-mahasiswa";
    packages = [
      python
      pkgs.git
      pkgs.curl
      pkgs.unzip
      pkgs.direnv
      pkgs.nix-direnv
      treefmt.config.build.wrapper
    ]
    ++ hooks.enabledPackages;
    startup.git-hooks.text = ''
      if ${pkgs.git}/bin/git rev-parse --git-dir >/dev/null 2>&1; then
        ${hooks.shellHook}
      fi
    '';
  };

  env = [
    {
      name = "STREAMLIT_BROWSER_GATHER_USAGE_STATS";
      value = "false";
    }
    {
      name = "STREAMLIT_SERVER_ADDRESS";
      value = "127.0.0.1";
    }
    {
      name = "STREAMLIT_CLIENT_TOOLBAR_MODE";
      value = "minimal";
    }
  ];

  commands = [
    {
      name = "fmt";
      category = "Quality";
      help = "Format source files with treefmt";
      command = ''exec ${treefmt.config.build.wrapper}/bin/treefmt "$@"'';
    }
    {
      name = "check";
      category = "Quality";
      help = "Run sandboxed Nix and formatting checks";
      command = ''
        set -euo pipefail
        cd "$PRJ_ROOT"
        exec nix flake check "$@"
      '';
    }
    {
      name = "run-tests";
      category = "Quality";
      help = "Run the app tests with pytest";
      command = ''
        set -euo pipefail
        cd "$PRJ_ROOT"
        exec python -m pytest tests "$@"
      '';
    }
    {
      name = "doctor";
      category = "Development";
      help = "Show Python and library versions";
      command = ''
        python - <<'PY'
        import importlib.metadata as m, sys
        print("python", sys.version.split()[0])
        for p in ["numpy", "pandas", "scipy", "scikit-learn", "joblib", "xgboost", "shap", "streamlit"]:
            print(p, m.version(p))
        PY
      '';
    }
    {
      name = "pins";
      category = "Development";
      help = "Print the install line for the first cell of the Kaggle notebook";
      command = ''
        python -c "import importlib.metadata as m; print('%pip install -q', *[f'{p}=={m.version(p)}' for p in ['scikit-learn', 'xgboost', 'shap']])"
      '';
    }
    {
      name = "lab";
      category = "Development";
      help = "Open JupyterLab on localhost";
      command = ''
        set -euo pipefail
        cd "$PRJ_ROOT"
        exec jupyter lab --ip 127.0.0.1 --no-browser "$@"
      '';
    }
    {
      name = "run-notebook";
      category = "Development";
      help = "Run the experiment notebook on this laptop";
      command = ''
        set -euo pipefail
        cd "$PRJ_ROOT"
        exec jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 notebooks/dropout_experiments.ipynb "$@"
      '';
    }
    {
      name = "app";
      category = "Development";
      help = "Run the Streamlit demo on localhost";
      command = ''
        set -euo pipefail
        cd "$PRJ_ROOT"
        exec streamlit run app/streamlit_app.py "$@"
      '';
    }
  ];
}
