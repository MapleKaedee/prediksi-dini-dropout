{
  description = "Lingkungan pengembangan prediksi dini dropout mahasiswa";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devshell = {
      url = "github:numtide/devshell";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    git-hooks = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      devshell,
      treefmt-nix,
      git-hooks,
    }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3.withPackages (
        ps: with ps; [
          joblib
          matplotlib
          numpy
          pandas
          scikit-learn
          scipy
          shap
          streamlit
          xgboost
          ipykernel
          jupyterlab
          nbconvert
          pytest
        ]
      );
      treefmt = treefmt-nix.lib.evalModule pkgs ./nix/treefmt.nix;
      hooks = git-hooks.lib.${system}.run {
        src = self;
        imports = [ ./nix/hooks.nix ];
        hooks.treefmt.package = treefmt.config.build.wrapper;
      };
    in
    {
      devShells.${system}.default = devshell.legacyPackages.${system}.mkShell {
        imports = [ ./nix/devshell.nix ];
        _module.args = {
          inherit python treefmt hooks;
        };
      };
      formatter.${system} = treefmt.config.build.wrapper;
      checks.${system} = {
        formatting = treefmt.config.build.check self;
        pre-commit = hooks;
      };
    };
}
