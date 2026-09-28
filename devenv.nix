{ pkgs, ... }:

{
  # Tools used by the PetClinic, I Hate Money, and OpenSpec workshop branches.
  packages = with pkgs; [
    jdk17
    uv
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
