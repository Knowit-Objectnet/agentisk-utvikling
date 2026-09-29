{ pkgs, ... }:

{
  languages.javascript = {
    enable = true;
    package = pkgs.nodejs_24;
    pnpm.enable = true;
  };

  languages.typescript = {
    enable = true;
    lsp.package = pkgs.vtsls;
  };
}
