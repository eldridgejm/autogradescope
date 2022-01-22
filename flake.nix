{
  inputs.nixpkgs.url = github:NixOS/nixpkgs/21.11;

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs supportedSystems (system: f system);
    in
      rec {

        devShell = forAllSystems (system:
          let pkgs = import nixpkgs { system = system; };
          in
            pkgs.mkShell {
            buildInputs = [
              (
                pkgs.python3.withPackages (ps: 
                  [
                    ps.pytest
                    ps.black
                    ps.rich
                  ]
                )
              )
            ];
          }
        );
      };

}
