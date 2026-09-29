{ pkgs, ... }:

let
  textual = pkgs.python312Packages.textual.overridePythonAttrs (_: {
    doCheck = false;
  });

  tau = pkgs.python312Packages.buildPythonApplication rec {
    pname = "tau-ai";
    version = "0.4.6";
    pyproject = true;

    src = pkgs.fetchPypi {
      pname = "tau_ai";
      inherit version;
      hash = "sha256-PJG9PUYXx4A57YTI3iHJKrghNnhRCvYI8rV8vMYfiFM=";
    };

    build-system = with pkgs.python312Packages; [ hatchling ];
    dependencies = with pkgs.python312Packages; [
      anyio
      httpx
      packaging
      pillow
      pydantic
      pygments
      rich
      socksio
      textual
      typer
    ];
  };
in
{
  # Keep Tau sessions and other local state out of the user-wide profile.
  enterShell = ''
    export TAU_HOME="$PWD/.tau/sessions"
  '';

  # Tools used by the PetClinic, I Hate Money, and OpenSpec workshop branches.
  packages = with pkgs; [
    jdk17
    uv
    tau
  ];

  languages.javascript = {
    enable = true;
    package = pkgs.nodejs_24;
    pnpm.enable = true;
  };

  languages.typescript = {
    enable = true;
    lsp.package = pkgs.vtsls;
  };

  languages.python = {
    enable = true;
    package = pkgs.python312;
    uv.enable = true;
  };

}
