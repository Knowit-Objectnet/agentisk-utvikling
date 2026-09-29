{ pkgs, ... }:

{
  # Tools used by the workshop branches and the OpenTUI presentation.
  packages = with pkgs; [
    bun
    jdk17
    uv
    nodejs_24
  ];
}
