{
  description = "Python package for creating Gradescope autograders.";

  inputs.nixpkgs.url = github:NixOS/nixpkgs/nixos-23.11;

  outputs = {
    self,
    nixpkgs,
  }: let
    supportedSystems = ["x86_64-linux" "x86_64-darwin" "aarch64-darwin"];
    forAllSystems = f: nixpkgs.lib.genAttrs supportedSystems (system: f system);
  in {
    autogradescope = forAllSystems (
      system:
        with import nixpkgs {
          system = "${system}";
          allowBroken = true;
        };
          python3Packages.buildPythonPackage rec {
            name = "autogradescope";
            src = ./.;
            propagatedBuildInputs = with python3Packages; [pytest click rich];
            nativeBuildInputs = with python3Packages; [pytest sphinx sphinx_rtd_theme pip];
            doCheck = false;
          }
    );

    defaultPackage = forAllSystems (
      system:
        self.autogradescope.${system}
    );
  };
}
