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
        tinydb
        pandas
        geopandas
        shapely
        numpy
        pyarrow
        matplotlib
        pycurl
        beautifulsoup4
      ];

      # you will need to point to your local git clone
      postInstall = ''
        wrapProgram $out/bin/resspublica \
          --set RESSPUBLICA_CACHE "/home/tomasr/devel/ReSSPublica/.cache" \
          --set RESSPUBLICA_ASSETS "/home/tomasr/devel/ReSSPublica/assets"
      '';

      mainProgram = "resspublica.py";
    };
    packages.default = self.packages.${system}.resspublica;
    devShells = {
      default = pkgs.mkShell {
        packages = with pkgs.python314Packages; [
          pkgs.python3
          setuptools
          sparqlwrapper
          feedgen
          tinydb
          pandas
          geopandas
          shapely
          numpy
          pyarrow
          matplotlib
          beautifulsoup4
          pycurl
        ];
      };
    };
  });
}
