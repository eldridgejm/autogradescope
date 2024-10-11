{
  description = "Python package for creating Gradescope autograders.";

  inputs.nixpkgs.url = github:NixOS/nixpkgs/nixos-23.11;

  outputs = {
    self,
    nixpkgs,
  }: let
    supportedSystems = ["x86_64-linux" "x86_64-darwin" "aarch64-darwin"];
    forAllSystems = f: nixpkgs.lib.genAttrs supportedSystems (system: f system);
  in rec {
    autogradescope = forAllSystems (
      system:
        with import nixpkgs {
          system = "${system}";
          allowBroken = true;
        };
          python3Packages.buildPythonPackage rec {
            name = "autogradescope";
            src = ./.;
            format = "pyproject";
            propagatedBuildInputs = with python3Packages; [pytest click rich setuptools];
            nativeBuildInputs = with python3Packages; [pytest sphinx sphinx_rtd_theme pip];
            doCheck = false;
          }
    );

    devShell = forAllSystems (
      system:
        with import nixpkgs {
          system = "${system}";
          # allowBroken = true;
        };
          mkShell {
            buildInputs = with python3Packages; [
              # install gradelib package to 1) make sure it's installable, and
              # 2) to get its dependencies. But below we'll add it to PYTHONPATH
              # so we can develop it in place.
              autogradescope.${system}
            ];

            shellHook = ''
              export PYTHONPATH="$(pwd)/src/:$PYTHONPATH"
            '';
          }
    );

    defaultPackage = forAllSystems (
      system:
        self.autogradescope.${system}
    );
  };
}
