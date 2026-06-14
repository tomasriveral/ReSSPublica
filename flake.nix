{
  description = "ReSSPublica development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils}:
  flake-utils.lib.eachDefaultSystem (system:
  let
    pkgs = import nixpkgs { inherit system; };
  in {
    packages.resspublica = pkgs.python314Packages.buildPythonApplication {
      pname = "resspublica";
      version = "0.1";
      src = ./.;
      pyproject = true;

      build-system = with pkgs.python314Packages; [ setuptools ];

      dependencies = with pkgs.python314Packages; [
        sparqlwrapper
        feedgen
      ];
      mainProgram = "resspublica.py";
    };
    packages.default = self.packages.${system}.resspublica;
    devShells = {
      default = pkgs.mkShell {
        packages = with pkgs; [
          python3
          python314Packages.sparqlwrapper
          python314Packages.feedgen
        ];
      };
    };
  });
}
