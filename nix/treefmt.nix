{ ... }:
{
  projectRootFile = "flake.nix";
  programs = {
    nixfmt.enable = true;
    ruff-check.enable = true;
    ruff-format.enable = true;
    prettier = {
      enable = true;
      includes = [
        "*.md"
        "*.yaml"
        "*.yml"
        "*.json"
      ];
    };
    shfmt.enable = true;
  };
  settings = {
    global.excludes = [
      ".direnv/**"
      ".git/**"
      ".pre-commit-config.yaml"
      "flake.lock"
      "docs/**"
      "artifacts/**"
      "data/**"
      "notebooks/**"
    ];
    formatter.shfmt.includes = [
      "*.sh"
      ".envrc"
    ];
  };
}
