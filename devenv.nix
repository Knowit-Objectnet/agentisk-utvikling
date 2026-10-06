{ pkgs, ... }:

let
  textual = pkgs.python312Packages.textual.overridePythonAttrs (_: {
    doCheck = false;
  });

  tauRuntime = pkgs.python312Packages.buildPythonApplication rec {
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
      logfire
      packaging
      pillow
      pydantic
      pygments
      rich
      socksio
      textual
      typer
    ];

    postInstall = ''
      cp ${./integrations/tau_logfire.py} "$out/${pkgs.python312.sitePackages}/tau_logfire.py"
    '';
  };

  # A stable module survives Tau's extension reloads; the entry file is reloaded.
  logfireExtension = pkgs.writeText "tau-logfire-extension.py" ''
    from tau_logfire import setup
  '';

  tau = pkgs.writeShellScriptBin "tau" ''
    case "''${TAU_LOGFIRE_ENABLED,,}" in
      1|true|yes|on)
        exec ${tauRuntime}/bin/tau --extension ${logfireExtension} "$@"
        ;;
      *) exec ${tauRuntime}/bin/tau "$@" ;;
    esac
  '';

  tauTestPython = pkgs.python312.withPackages (ps: [ (ps.toPythonModule tauRuntime) ps.pytest ]);
in
{
  # This demonstration branch captures Tau activity by default. Keep Logfire
  # write credentials in the shell environment or gitignored .logfire directory.
  env.TAU_LOGFIRE_ENABLED = "1";
  env.TAU_LOGFIRE_CAPTURE_CONTENT = "1";
  env.TAU_LOGFIRE_MAX_CONTENT_CHARS = "100000";
  env.TAU_LOGFIRE_MAX_MESSAGES = "1000";

  # Keep Tau sessions and other local state out of the user-wide profile.
  enterShell = ''
    export TAU_HOME="$PWD/.tau/sessions"
  '';

  scripts.logfire-cli = {
    description = "Run the pinned Logfire setup CLI through uv's tool cache";
    exec = ''
      exec ${pkgs.uv}/bin/uvx logfire-cli==0.1.10 "$@"
    '';
  };

  scripts.test-tau-logfire = {
    description = "Test Tau telemetry without contacting Logfire or a model provider";
    exec = ''
      export TAU_LOGFIRE_CLI=${tau}/bin/tau
      exec ${tauTestPython}/bin/python -m pytest -p no:cacheprovider ${./tests/test_tau_logfire.py} "$@"
    '';
  };

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
